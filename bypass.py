import requests
import re
import base64
import time
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LksfyBypasser:
    def __init__(self):
        self.session = requests.Session()
        # Use a Mobile User-Agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
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

    def bypass(self, url):
        current_url = url
        logger.info(f"Starting bypass for: {current_url}")

        # Limit steps to avoid infinite loops
        max_steps = 150

        for step in range(max_steps):
            logger.info(f"Step {step}: Requesting {current_url}")

            try:
                response = self.session.get(current_url, allow_redirects=True, timeout=15)
                # Important: Update Referer for the NEXT request to mimic browser behavior
                self.session.headers.update({'Referer': current_url})
            except Exception as e:
                logger.error(f"Error requesting {current_url}: {e}")
                return None

            # Check if we reached the telegram link in the final URL
            if "telegram.me" in response.url or "t.me" in response.url:
                logger.info(f"SUCCESS! Found Telegram link: {response.url}")
                return response.url

            content = response.text

            # Check for telegram link in content
            tg_match = re.search(r'href=["\'](https://(?:telegram\.me|t\.me)/.*?)["\']', content)
            if tg_match:
                 logger.info(f"SUCCESS! Found Telegram link in content: {tg_match.group(1)}")
                 return tg_match.group(1)

            # Check for Cloudflare Turnstile CAPTCHA - if present, we are stuck
            if "cf-turnstile" in content and "lksfy.com" in response.url:
                 logger.error("Cloudflare Turnstile CAPTCHA detected. Cannot bypass automatically.")
                 # Try to see if we can find any other link, but usually this is a hard stop.
                 return None

            # Check for JS window.location.href redirect
            # We prioritize this if no complex 'tagrget_url' logic is found, OR if it's a direct redirect page
            if "<script>window.location.href" in content and "tagrget_url" not in content:
                 match = re.search(r'window\.location\.href\s*=\s*["\'](.*?)["\']', content)
                 if match:
                     next_url = match.group(1)
                     # logger.info(f"Found JS redirect to: {next_url}")
                     current_url = next_url
                     continue

            # Look for the 'tagrget_url' pattern (complex redirect with timer/cookies)
            target_match = re.search(r'var tagrget_url\s*=\s*["\'](.*?)["\']', content)

            if target_match:
                encoded_url = target_match.group(1)
                decoded_url = self.decode_base64(encoded_url)
                logger.info(f"Found tagrget_url: {encoded_url} -> {decoded_url}")

                if decoded_url:
                    # Handle Cookie Clearing
                    if 'document.cookie = "user_step=;' in content:
                        logger.info("Clearing user_step cookie")
                        try:
                            domain = urlparse(current_url).netloc
                            self.session.cookies.clear(domain=domain, path='/', name='user_step')
                            if 'user_step' in self.session.cookies:
                                del self.session.cookies['user_step']
                        except Exception as e:
                            pass

                    # Handle Cookie Setting
                    # setCookiee("user_step", "1", 1);
                    cookie_match = re.search(r'setCookiee\s*\(\s*["\'](.*?)["\']\s*,\s*["\'](.*?)["\']', content)
                    if cookie_match:
                        cookie_name = cookie_match.group(1)
                        cookie_value = cookie_match.group(2)
                        domain = urlparse(current_url).netloc
                        # logger.info(f"Setting cookie: {cookie_name}={cookie_value} for {domain}")
                        self.session.cookies.set(cookie_name, cookie_value, domain=domain)

                    current_url = decoded_url
                    continue
                else:
                    logger.error("Failed to decode URL")
                    break
            else:
                # check for meta refresh
                if 'content="0;url=' in content:
                     meta_match = re.search(r'content=["\']\d+;url=(.*?)["\']', content)
                     if meta_match:
                         # logger.info(f"Found Meta Refresh to {meta_match.group(1)}")
                         current_url = meta_match.group(1)
                         continue

                # If we are just on a random page without next step, we might be lost
                break

        return None

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://lksfy.com/xXias"
    bypasser = LksfyBypasser()
    result = bypasser.bypass(url)
    print(f"Result: {result}")
