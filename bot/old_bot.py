from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# توکن بات تلگرام که از BotFather گرفتی:
TELEGRAM_BOT_TOKEN = '8204535470:AAFQ7ffXUy2jDyj79phxDq4RwdwPeweWrJg'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات هوش مصنوعی هستم. سوالت رو بپرس 🌟")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.reply_text(f"تو گفتی: {user_message} (پاسخ AI به‌زودی اینجا قرار می‌گیره!)")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("ربات روشن شد ✅")
    app.run_polling()
