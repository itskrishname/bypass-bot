import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

async def solve_with_browser(url, cookies, user_agent):
    logger.info(f"Starting browser solver for {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                f'--user-agent={user_agent}'
            ]
        )
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 375, 'height': 812},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True
        )

        if cookies:
            playwright_cookies = []
            for name, value in cookies.items():
                playwright_cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.lksfy.com',
                    'path': '/'
                })
            try:
                await context.add_cookies(playwright_cookies)
            except Exception as e:
                logger.warning(f"Failed to set cookies: {e}")

        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Wait for navigation away from lksfy.com or to telegram
            for _ in range(45): # 90 seconds
                current_url = page.url

                if "telegram.me" in current_url or "t.me" in current_url:
                    logger.info("Found Telegram link in browser.")
                    return {"url": current_url, "cookies": await context.cookies()}

                # If redirected to a known intermediate domain (not lksfy)
                # And assume we passed the captcha
                if "lksfy.com" not in current_url and "about:blank" not in current_url:
                    logger.info(f"Solved CAPTCHA? Redirected to: {current_url}")
                    # Return new URL and new cookies
                    return {"url": current_url, "cookies": await context.cookies()}

                # Check for "Get Link" button
                try:
                    button = page.locator("a#get-link, button#get-link, a.get-link")
                    if await button.count() > 0 and await button.is_visible():
                        if await button.is_enabled():
                            logger.info("Clicking Get Link button...")
                            await button.click()
                except:
                    pass

                await asyncio.sleep(2)

            logger.info(f"Browser solver timed out. Final URL: {page.url}")
            return None

        except Exception as e:
            logger.error(f"Browser error: {e}")
            return None
        finally:
            await browser.close()
