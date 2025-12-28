import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LksfyBypasser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://lksfy.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def decode_base64(self, s):
        import base64
        try:
            return base64.b64decode(s).decode('utf-8')
        except:
            return None

    def bypass(self, url):
        current_url = url
        logger.info(f"Starting bypass for: {current_url}")

        max_steps = 150

        for step in range(max_steps):
            logger.info(f"Step {step}: Requesting {current_url}")

            try:
                # Add slight delay to mimic human behavior
                time.sleep(1)
                response = self.session.get(current_url, allow_redirects=True, timeout=15)
                # Important: Update referer
                self.session.headers.update({'Referer': current_url})
            except Exception as e:
                logger.error(f"Error requesting {current_url}: {e}")
                return None

            if "telegram.me" in response.url or "t.me" in response.url:
                logger.info(f"SUCCESS! Found Telegram link: {response.url}")
                return response.url

            content = response.text

            # Check if we are on the Turnstile/Form page
            # Look for the form with id "go-link" as seen in archelaus script and my dumps
            if 'id="go-link"' in content or 'class="go-link"' in content:
                logger.info("Found go-link form. Attempting POST bypass...")

                bs4 = BeautifulSoup(content, 'lxml')
                form = bs4.find('form', {'id': 'go-link'}) or bs4.find('form', {'class': 'go-link'})

                if form:
                    inputs = form.find_all('input')
                    data = {input.get('name'): input.get('value') for input in inputs}

                    # Add missing inputs if needed (alias?)
                    if not data.get('alias'):
                        alias_match = re.search(r"var alias = '(.*?)'", content)
                        if alias_match:
                            data['alias'] = alias_match.group(1)

                    logger.info(f"Form Data: {data}")

                    # Wait 10s as per archelaus script
                    logger.info("Sleeping 10s...")
                    time.sleep(10)

                    post_url = f"https://lksfy.com/links/go"
                    headers = {
                        'x-requested-with': 'XMLHttpRequest',
                        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
                    }

                    # Update session headers for this request
                    # self.session.headers.update(headers)

                    try:
                        post_resp = self.session.post(post_url, data=data, headers=headers)
                        logger.info(f"POST Response: {post_resp.status_code}")
                        # logger.info(f"POST Content: {post_resp.text}")

                        try:
                            json_resp = post_resp.json()
                            if json_resp.get('url'):
                                logger.info(f"Got URL from JSON: {json_resp['url']}")
                                return json_resp['url']
                            elif json_resp.get('message'):
                                logger.error(f"Error Message: {json_resp['message']}")
                        except:
                            pass
                    except Exception as e:
                        logger.error(f"POST failed: {e}")
                else:
                    logger.error("Could not find form element even though ID was found in text?")

            # Standard redirect logic (JS, meta, etc)
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
                if 'content="0;url=' in content:
                     meta_match = re.search(r'content=["\']\d+;url=(.*?)["\']', content)
                     if meta_match:
                         current_url = meta_match.group(1)
                         continue

                # If we are stuck on lksfy and didn't find the form
                if "lksfy.com" in current_url:
                     logger.warning("Stuck on lksfy.com without form?")
                     # Maybe we need to wait/refresh?
                     pass

                # If we are stuck elsewhere, break
                # break

        return None
