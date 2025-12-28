import asyncio
from playwright.async_api import async_playwright
import base64
import re
import json
from urllib.parse import urlparse

def new_url_domain(url):
    return urlparse(url).netloc

async def solve_lksfy(url):
    print(f"[*] Launching Browser for {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # NOTE: Do NOT block ad scripts (fundingchoices, adsbygoogle) as the site detects this and blocks access.
        # Instead, we handle the overlays/vignettes they generate.

        page = await context.new_page()

        # Try to neutralize AdBlock detection early
        await page.add_init_script('''
            window.AdBDetected = function() { console.log("AdBlock detection neutralized"); };
        ''')

        try:
            print(f"[*] Going to {url}")
            await page.goto(url)

            # Wait for initial load
            try:
                await page.wait_for_load_state("domcontentloaded")
            except:
                pass

            max_steps = 30
            for i in range(max_steps):
                current_url = page.url
                print(f"[{i}] Processing: {current_url}")

                # 1. Cloudflare Check
                try:
                    if "Just a moment" in await page.title():
                        print("[*] Cloudflare detected. Waiting...")
                        await page.wait_for_timeout(5000)
                        continue
                except: pass

                # 1.1 Google Vignette Check
                if "#google_vignette" in current_url:
                    print("[*] Google Vignette detected. Attempting to dismiss...")
                    try:
                        # Try to find and click the dismiss button (usually in an iframe or shadow DOM, but often just a div with ID)
                        # Common IDs/Selectors for Google Vignette dismiss
                        dismissed = await page.evaluate('''() => {
                            const closeBtn = document.getElementById('dismiss-button') || document.querySelector('[aria-label="Close ad"]');
                            if (closeBtn) {
                                closeBtn.click();
                                return true;
                            }
                            // Sometimes it's inside an iframe, let's try to check frames from python side
                            return false;
                        }''')

                        if not dismissed:
                            # Try to click via frames
                            for frame in page.frames:
                                try:
                                    if await frame.evaluate('''() => {
                                        const btn = document.getElementById('dismiss-button') || document.querySelector('[aria-label="Close ad"]');
                                        if(btn) { btn.click(); return true; }
                                        return false;
                                    }'''):
                                        dismissed = True
                                        break
                                except: pass

                        if dismissed:
                            print("[*] Vignette dismissed.")
                            await page.wait_for_timeout(2000) # Wait for animation
                            continue
                        else:
                            print("[!] Could not find dismiss button. Reloading...")
                            await page.reload()
                            continue

                    except Exception as e:
                        print(f"[!] Error handling vignette: {e}")

                # 2. Final Lksfy Page Logic
                if "lksfy.com" in current_url:
                    print("[*] On Lksfy Page.")
                    try:
                        try:
                            await page.wait_for_selector('#go-link', timeout=5000)
                        except:
                            pass

                        inputs = await page.evaluate('''() => {
                            const form = document.getElementById('go-link');
                            if (!form) return null;
                            const inputs = form.querySelectorAll('input');
                            const data = {};
                            inputs.forEach(input => { data[input.name] = input.value; });
                            return data;
                        }''')

                        if inputs:
                            print(f"[*] Extracted Form Data: {inputs}")
                            resp = await context.request.post("https://lksfy.com/links/go",
                                form=inputs,
                                headers={"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded"}
                            )
                            text = await resp.text()
                            try:
                                j = json.loads(text)
                                if 'url' in j:
                                    print(f"SUCCESS_URL: {j['url']}")
                                    return j['url']
                            except:
                                pass
                            return None
                    except Exception as e:
                        print(f"[!] Lksfy Error: {e}")

                # 3. Blog Step Logic - Fast Path (Variable)
                target = await page.evaluate('''() => {
                    // Check for tagrget_url, target_url, or other variations
                    const vars = ['tagrget_url', 'target_url', 'get_link', 'next_url'];
                    for (let v of vars) {
                        try { if (typeof window[v] !== 'undefined') return atob(window[v]); } catch(e) {}
                    }

                    for (let s of document.querySelectorAll('script')) {
                        // Match variable assignment: var/let/const name = '...'
                        let m = s.innerText.match(/(?:tagrget_url|target_url|get_link|next_url)\\s*=\\s*["']([^"']+)["']/);
                        if (m) return atob(m[1]);
                    }
                    return null;
                }''')

                if target:
                    print(f"[*] Found Target: {target}")
                    # Apply Cookie Hack
                    step_text = await page.evaluate("() => document.querySelector('.tag') ? document.querySelector('.tag').innerText : ''")
                    if step_text:
                        m = re.search(r'Step\s*(\d+)', step_text)
                        if m:
                            step = m.group(1)
                            print(f"[*] Setting user_step={step}")
                            await context.add_cookies([{'name': 'user_step', 'value': step, 'domain': new_url_domain(current_url), 'path': '/'}])
                    await page.goto(target)
                    continue

                # 4. Final Step Logic (Force Button Click)
                print("[*] No target variable found. Scanning frames/buttons...")

                # Check for Overlay and Close it
                await page.evaluate('''() => {
                    const overlay = document.querySelector('.adb-overlay');
                    if(overlay) overlay.remove();
                    const adbModel = document.getElementById('AdbModel');
                    if(adbModel) adbModel.remove();
                }''')

                # Helper to find and click button
                async def try_click_button():
                    return await page.evaluate('''() => {
                        // Force show and click bottomButton
                        const btn = document.getElementById('bottomButton');
                        if (btn) {
                            btn.style.display = 'block';
                            btn.style.visibility = 'visible';
                            btn.style.opacity = '1';
                            btn.click();
                            return "ID: bottomButton";
                        }

                        // Also try 'getting-link' or 'get-link'
                        const btn2 = document.getElementById('getting-link') || document.getElementById('get-link') || document.getElementById('glink');
                        if(btn2) {
                            btn2.style.display = 'block';
                            btn2.click();
                            return "ID: " + btn2.id;
                        }

                        // Try generic search by text
                        const buttons = document.querySelectorAll('button, a.btn, div[role="button"], a');
                        for (let b of buttons) {
                            if (b.offsetParent !== null && b.innerText.trim().length > 0) {
                                const t = b.innerText.toLowerCase();
                                if (t.includes("get link") || t.includes("open link") || t.includes("continue") || t.includes("go to link") || t.includes("download") || t.includes("लिंक") || t.includes("click") || t.includes("here")) {
                                    b.click();
                                    return "Text: " + b.innerText;
                                }
                            }
                        }
                        return false;
                    }''')

                # Scroll to bottom to trigger lazy loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                clicked_btn = await try_click_button()
                if clicked_btn:
                    print(f"[*] Forced click on button ({clicked_btn}). Waiting for timer/generation (10s)...")
                    await page.wait_for_timeout(10000)
                else:
                    # Try Frames
                    for frame in page.frames:
                        try:
                            if await frame.evaluate('''() => {
                                const btn = document.getElementById('bottomButton') || document.getElementById('getting-link') || document.getElementById('get-link');
                                if(btn) { btn.click(); return true; }
                                return false;
                            }'''):
                                print("[*] Clicked button in frame!")
                                await page.wait_for_timeout(10000)
                                break
                        except: pass

                # Check for generated link
                generated_link = await page.evaluate('''() => {
                    const a = document.getElementById('open-link');
                    if (a) return a.href;

                    const btn = document.getElementById('bottomButton');
                    if (btn && btn.parentElement.tagName === 'A') return btn.parentElement.href;

                    for (let l of document.querySelectorAll('a')) {
                        if (l.href.includes('lksfy.com')) return l.href;
                    }
                    return null;
                }''')

                if generated_link:
                    print(f"[*] Found Generated Link: {generated_link}")
                    await page.goto(generated_link)
                    continue

                # Scroll a bit
                await page.evaluate("window.scrollBy(0, 500)")
                print("[*] Waiting for content...")
                await page.wait_for_timeout(3000)

        except Exception as e:
            print(f"[!] Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    url = "https://lksfy.com/xXias"
    asyncio.run(solve_lksfy(url))
