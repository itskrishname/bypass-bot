import requests
import re
import base64
import time
from urllib.parse import urlparse
import logging
from browser_solver import solve_with_browser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LksfyBypasser:
    def __init__(self):
        self.session = requests.Session()
        self.user_agent = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Referer': 'https://lksfy.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def decode_base64(self, s):
        try:
            return base64.b64decode(s).decode('utf-8')
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return None

    def sync_bypass(self, url):
        """
        Runs the requests-based bypass loop.
        Returns:
          - Str: Final Telegram URL
          - Dict: {"action": "browser_solve", "url": ...}
          - None: Failure
        """
        current_url = url
        max_steps = 150

        for step in range(max_steps):
            logger.info(f"Step {step}: Requesting {current_url}")

            try:
                response = self.session.get(current_url, allow_redirects=True, timeout=15)
                self.session.headers.update({'Referer': current_url})
            except Exception as e:
                logger.error(f"Error requesting {current_url}: {e}")
                return None

            if "telegram.me" in response.url or "t.me" in response.url:
                logger.info(f"SUCCESS! Found Telegram link: {response.url}")
                return response.url

            content = response.text

            tg_match = re.search(r'href=["\'](https://(?:telegram\.me|t\.me)/.*?)["\']', content)
            if tg_match:
                 logger.info(f"SUCCESS! Found Telegram link in content: {tg_match.group(1)}")
                 return tg_match.group(1)

            # Check for CAPTCHA
            if "cf-turnstile" in content and "lksfy.com" in response.url:
                 logger.info("Cloudflare Turnstile CAPTCHA detected.")
                 return {
                     "action": "browser_solve",
                     "url": current_url,
                     "cookies": self.session.cookies.get_dict(),
                     "user_agent": self.user_agent
                 }

            # Redirects
            if "<script>window.location.href" in content and "tagrget_url" not in content:
                 match = re.search(r'window\.location\.href\s*=\s*["\'](.*?)["\']', content)
                 if match:
                     next_url = match.group(1)
                     current_url = next_url
                     continue

            target_match = re.search(r'var tagrget_url\s*=\s*["\'](.*?)["\']', content)

            if target_match:
                encoded_url = target_match.group(1)
                decoded_url = self.decode_base64(encoded_url)
                logger.info(f"Found tagrget_url: {encoded_url} -> {decoded_url}")

                if decoded_url:
                    if 'document.cookie = "user_step=;' in content:
                        try:
                            domain = urlparse(current_url).netloc
                            self.session.cookies.clear(domain=domain, path='/', name='user_step')
                            if 'user_step' in self.session.cookies:
                                del self.session.cookies['user_step']
                        except:
                            pass

                    cookie_match = re.search(r'setCookiee\s*\(\s*["\'](.*?)["\']\s*,\s*["\'](.*?)["\']', content)
                    if cookie_match:
                        cookie_name = cookie_match.group(1)
                        cookie_value = cookie_match.group(2)
                        domain = urlparse(current_url).netloc
                        self.session.cookies.set(cookie_name, cookie_value, domain=domain)

                    current_url = decoded_url
                    continue
                else:
                    logger.error("Failed to decode URL")
                    break
            else:
                if 'content="0;url=' in content:
                     meta_match = re.search(r'content=["\']\d+;url=(.*?)["\']', content)
                     if meta_match:
                         current_url = meta_match.group(1)
                         continue
                break

        return None

    async def run_hybrid_bypass(self, url):
        """
        Orchestrates the hybrid bypass (requests -> browser -> requests).
        """
        current_url = url

        # Increased loop limit to handle multiple CAPTCHA checks
        for loop_idx in range(50):
            logger.info(f"Hybrid Loop {loop_idx}: Starting sync bypass...")

            # 1. Run Sync Bypass
            import asyncio
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self.sync_bypass, current_url)

            # 2. Check Result
            if isinstance(result, str):
                return result # Success!

            if isinstance(result, dict) and result.get("action") == "browser_solve":
                logger.info("Sync bypass hit CAPTCHA. Switching to Browser...")

                # 3. Run Browser Solver
                browser_result = await solve_with_browser(result["url"], result["cookies"], result["user_agent"])

                if browser_result and browser_result.get("url"):
                    new_url = browser_result["url"]
                    logger.info(f"Browser returned new URL: {new_url}")

                    if "telegram.me" in new_url or "t.me" in new_url:
                        return new_url

                    # Update cookies from browser back to session
                    if browser_result.get("cookies"):
                        for c in browser_result["cookies"]:
                            self.session.cookies.set(c['name'], c['value'], domain=c['domain'], path=c['path'])

                    current_url = new_url
                    continue # Loop back to sync bypass
                else:
                    logger.error("Browser failed to solve CAPTCHA or find next link.")
                    return None

            logger.info("Sync bypass returned None or unknown state.")
            return None

        return None
