import logging
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Config ---
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
ADMIN_ID = 7660990923  # Replace with your Telegram ID for admin features

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)

# --- Bypass Function ---
def bypass_link(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10, allow_redirects=True)
        return resp.url
    except Exception as e:
        return f"❌ Error bypassing link: {e}"

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to the Link Bypasser Bot!\nSend me a link from seturl.in, lksfy.com, or arolinks.com.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💡 Just send any supported short link, and I'll bypass it for you.")

# --- Link Handler ---
async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    links = re.findall(r'(https?://\S+)', message_text)

    if not links:
        return

    for url in links:
        if any(domain in url for domain in ['seturl.in', 'lksfy.com', 'arolinks.com']):
            await update.message.reply_text("⏳ Bypassing...")
            result = bypass_link(url)
            await update.message.reply_text(f"🔗 {result}")

# --- Main ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), link_handler))

    print("Bot is running...")
    app.run_polling()
