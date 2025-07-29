from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ❗ توکن ربات — فقط برای تست، بعداً از ENV بخون
TOKEN = "8204535470:AAFQ7ffXUy2jDyj79phxDq4RwdwPeweWrJg"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات زیست‌شناسی هستم. سوالی داری بپرس :)")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور /start رو بزن یا سوالی درباره زیست بپرس.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    # اینجا پاسخ ساده می‌ده، بعداً می‌تونی به هوش مصنوعی وصلش کنی
    await update.message.reply_text(f"تو گفتی: {user_message}\nدر حال پردازش...")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
