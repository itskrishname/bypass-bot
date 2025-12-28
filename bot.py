import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bypass import solve_lksfy

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
        import re
        url_match = re.search(r'(https?://lksfy\.com/[^\s]+)', text)
        if url_match:
            url = url_match.group(1)
            status_msg = await update.message.reply_text(f"Bypassing {url}... Please wait (approx 20-30s).")

            try:
                # Call the async solver directly
                final_url = await solve_lksfy(url)

                if final_url:
                    response_message = (
                        f"┎ 🔗 Original Link :- {url}\n"
                        f"┃\n"
                        f"┖ 🔓 Bypassed Link : {final_url}\n\n"
                        f"━━━━━━━✦✗✦━━━━━━━\n\n"
                        f"Requested By :- @{update.effective_user.username}"
                    )
                    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=response_message, disable_web_page_preview=True)
                else:
                    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text="❌ Failed to bypass the link. Timed out or stuck.")
            except Exception as e:
                logging.error(f"Error bypassing: {e}")
                await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Error: {str(e)}")
        else:
            await update.message.reply_text("Could not find a valid lksfy.com link.")
    else:
        pass

if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        # Fallback for testing if env var not set, though it should be.
        print("Warning: BOT_TOKEN not set.")

    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()
