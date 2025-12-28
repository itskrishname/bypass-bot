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
        page = await context.new_page()

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
                    try { if (typeof tagrget_url !== 'undefined') return atob(tagrget_url); } catch(e) {}

                    for (let s of document.querySelectorAll('script')) {
                        let m = s.innerText.match(/tagrget_url\\s*=\\s*["']([^"']+)["']/);
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
                            return true;
                        }

                        // Also try 'getting-link' or 'get-link'
                        const btn2 = document.getElementById('getting-link') || document.getElementById('get-link') || document.getElementById('glink');
                        if(btn2) {
                            btn2.style.display = 'block';
                            btn2.click();
                            return true;
                        }

                        return false;
                    }''')

                if await try_click_button():
                    print("[*] Forced click on button. Waiting for timer/generation (10s)...")
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
