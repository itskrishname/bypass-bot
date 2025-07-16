import logging
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '7808143510:AAFuwJvgVwc9lYh0Yr_xIWEaLscvRJ0ehVk'

SUPPORTED_DOMAINS = ['seturl.in', 'lksfy.com', 'arolinks.com']

def bypass_link(url: str) -> str:
    """
    Basic HTTP redirect bypass.
    For advanced JS/captcha shorteners, integrate Selenium or Playwright.
    """
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        }
        resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        # If meta refresh or JS redirect, try to extract from HTML
        if resp.url == url:
            m = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][0-9]+;url=(.*?)["\']', resp.text, re.IGNORECASE)
            if m:
                return m.group(1)
        return resp.url
    except Exception as e:
        return f"❌ Error bypassing link: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send me a link from seturl.in, lksfy.com, or arolinks.com and I'll try to bypass it."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Just send any supported short link (seturl.in, lksfy.com, arolinks.com), and I'll bypass it for you."
    )

async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    links = re.findall(r'(https?://\S+)', message_text)
    if not links:
        return
    for url in links:
        if any(domain in url for domain in SUPPORTED_DOMAINS):
            await update.message.reply_text("⏳ Bypassing...")
            result = bypass_link(url)
            await update.message.reply_text(f"🔗 {result}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), link_handler))
    print("Bot is running...")
    app.run_polling()
