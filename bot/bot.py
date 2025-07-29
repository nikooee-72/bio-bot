import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()  # بارگذاری فایل .env

# گرفتن اطلاعات از .env
TOKEN = os.getenv("8204535470:AAFQ7ffXUy2jDyj79phxDq4RwdwPeweWrJg")
WEBHOOK_URL = os.getenv("https://bio-bot-production.up.railway.app")

# دستور شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات Webhook با موفقیت راه‌اندازی شد.")

# تابع اصلی
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # هندلرها
    app.add_handler(CommandHandler("start", start))

    # راه‌اندازی Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),  # Railway از PORT استفاده می‌کنه
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
