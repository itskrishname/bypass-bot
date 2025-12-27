import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bypass import LksfyBypasser

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me an lksfy.com link and I will bypass it.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "lksfy.com" in text:
        # Extract URL
        import re
        url_match = re.search(r'(https?://lksfy\.com/[^\s]+)', text)
        if url_match:
            url = url_match.group(1)
            await update.message.reply_text(f"Bypassing {url}... Please wait, this may take a moment.")

            # Run bypass in executor to avoid blocking async loop
            # Bypasser creates a new session for each request, which is thread-safe enough here
            bypasser = LksfyBypasser()

            # Since bypass is synchronous, we run it in a thread
            loop =  context.application.loop if hasattr(context.application, 'loop') else __import__('asyncio').get_running_loop()
            result_url = await loop.run_in_executor(None, bypasser.bypass, url)

            if result_url:
                response_message = (
                    f"┎ 🔗 Original Link :- {url}\n"
                    f"┃\n"
                    f"┖ 🔓 Bypassed Link : {result_url}\n\n"
                    f"━━━━━━━✦✗✦━━━━━━━\n\n"
                    f"Requested By :- @{update.effective_user.username}"
                )
                await update.message.reply_text(response_message, disable_web_page_preview=True)
            else:
                # If logs indicate CAPTCHA (we don't pass logs back, but checking None result)
                # We could improve this by returning a status from bypass()
                await update.message.reply_text("❌ Failed to bypass the link. It might be protected by a CAPTCHA or timed out.")
        else:
            await update.message.reply_text("Could not find a valid lksfy.com link.")
    else:
        # Optional: ignore non-links or reply with help
        pass

if __name__ == '__main__':
    # Use environment variable for token
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("No BOT_TOKEN provided in environment variables.")

    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()
