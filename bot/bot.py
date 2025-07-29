import logging
import os
import aiofiles
import asyncio
from pydub import AudioSegment
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import openai

# --- توکن‌ها ---
TELEGRAM_TOKEN = '8204535470:AAFQ7ffXUy2jDyj79phxDq4RwdwPeweWrJg'
OPENROUTER_API_KEY = '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'

# تنظیم کلید API
openai.api_key = OPENROUTER_API_KEY

# --- لاگ ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- پرامپت محدودکننده حوزه ---
SYSTEM_PROMPT = (
    "شما یک ربات هوش مصنوعی هستید که فقط به سوالات مرتبط با زیست‌شناسی، پزشکی و علوم تجربی پاسخ می‌دهید. "
    "در صورتی که سوال خارج از این حوزه‌ها باشد، با احترام اعلام کنید که نمی‌توانید پاسخ دهید."
)

# --- پرسش به OpenRouter ---
async def ask_openrouter(prompt: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"خطای OpenRouter: {e}")
        return "متأسفم، در حال حاضر نمی‌توانم پاسخ دهم."

# --- شروع ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! سوالات زیستی، ویس یا فایل متنی بفرست تا پاسخ بدم.")

# --- پیام متنی ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = await ask_openrouter(text)
    await update.message.reply_text(response)

# --- ویس ---
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    ogg_path = f"voice_{voice.file_id}.ogg"
    wav_path = f"voice_{voice.file_id}.wav"

    # دانلود فایل بصورت async
    await file.download_to_drive(ogg_path)

    # تبدیل از ogg به wav در thread جداگانه (sync)
    def convert_ogg_to_wav():
        sound = AudioSegment.from_ogg(ogg_path)
        sound.export(wav_path, format="wav")

    await asyncio.to_thread(convert_ogg_to_wav)

    # تبدیل صوت به متن با Whisper (sync) در thread جداگانه
    def transcribe_audio():
        with open(wav_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript

    transcript = await asyncio.to_thread(transcribe_audio)

    # حذف فایل‌ها
    try:
        os.remove(ogg_path)
        os.remove(wav_path)
    except Exception as e:
        logger.warning(f"خطا در حذف فایل‌ها: {e}")

    await update.message.reply_text(f"متن ویس شما:\n{transcript['text']}")

# --- فایل متنی ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)
    path = f"file_{doc.file_name}"
    await file.download_to_drive(path)

    try:
        async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        os.remove(path)
        response = await ask_openrouter(content)
        await update.message.reply_text(f"پاسخ به محتوای فایل:\n{response}")
    except Exception as e:
        logger.error(f"خطا در خواندن فایل: {e}")
        await update.message.reply_text("متاسفم، نتوانستم فایل را بخوانم.")

# --- اجرای ربات ---
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("✅ ربات آماده است!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
