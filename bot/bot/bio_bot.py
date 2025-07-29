import logging
import os
import aiofiles
from io import BytesIO
from PIL import Image
from pydub import AudioSegment
import asyncio

from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import openai
import whisper
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

# --------- تنظیمات توکن ها ----------
TELEGRAM_TOKEN = '8204535470:AAFQ7ffXUy2jDyj79phxDq4RwdwPeweWrJg'
OPENROUTER_API_KEY = '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'

# تنظیم کلید OpenRouter در کتابخانه openai
openai.api_key = OPENROUTER_API_KEY

# --------- بارگذاری مدل‌ها ------------

# مدل Whisper (تبدیل ویس به متن)
whisper_model = whisper.load_model("base")  # نسخه سبک؛ اگر سرورت قوی است "small" یا "medium" هم می‌توان انتخاب کرد

# مدل BLIP (تحلیل و توصیف تصویر)
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

# --------- تنظیم لاگ ---------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --------- پرامپت سیستم برای محدود کردن حوزه (زیست و پزشکی) ---------
SYSTEM_PROMPT = (
    "شما دستیار هوش مصنوعی هستید که فقط به سوالات مرتبط با زیست‌شناسی، پزشکی، علوم تجربی و موضوعات علمی پاسخ می‌دهید."
    " اگر سوال خارج از این حوزه باشد، مودبانه اعلام کنید که فقط در این حوزه‌ها پاسخگو هستید."
)

# --------- تابع پرسش به OpenRouter ----------
async def ask_openrouter(question: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",  # یا مدلی که توکن تو پشتیبانی می‌کند
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return "متأسفانه در حال حاضر نمی‌توانم به سوال شما پاسخ دهم."

# --------- تبدیل ویس به متن با Whisper ---------
async def transcribe_audio(file_path: str) -> str:
    result = whisper_model.transcribe(file_path)
    return result["text"]

# --------- تحلیل تصویر با BLIP ----------
async def analyze_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        inputs = processor(image, return_tensors="pt").to(device)
        out = blip_model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        logger.error(f"BLIP image analysis error: {e}")
        return "متأسفانه نتوانستم تصویر را تحلیل کنم."

# --------- هندلر شروع /start ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "سلام! من ربات هوشمند هستم. می‌توانید از من سوال بپرسید، فایل صوتی ارسال کنید تا متنش را بنویسم، یا تصویر ارسال کنید تا آن را تحلیل کنم."
    )

# --------- هندلر پیام متنی ---------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    user_id = update.message.from_user.id
    logger.info(f"Received text from {user_id}: {user_text}")

    response_text = await ask_openrouter(user_text)
    await update.message.reply_text(response_text)

# --------- هندلر فایل صوتی ---------
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice = update.message.voice
    user_id = update.message.from_user.id
    logger.info(f"Received voice from {user_id}")

    # دانلود فایل صوتی
    file = await context.bot.get_file(voice.file_id)
    file_path = f"voice_{user_id}.ogg"
    await file.download_to_drive(file_path)

    # تبدیل ogg به wav با pydub
    wav_path = f"voice_{user_id}.wav"
    audio = AudioSegment.from_ogg(file_path)
    audio.export(wav_path, format="wav")

    # تبدیل صدا به متن
    transcription = await transcribe_audio(wav_path)

    # حذف فایل‌ها برای صرفه‌جویی در فضا
    os.remove(file_path)
    os.remove(wav_path)

    # پاسخ متن تبدیل شده
    await update.message.reply_text(f"متن گفتار شما:\n{transcription}")

# --------- هندلر عکس ---------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    logger.info(f"Received photo from {user_id}")

    photo = update.message.photo[-1]  # با کیفیت ترین عکس
    file = await context.bot.get_file(photo.file_id)
    bio = BytesIO()
    await file.download(out=bio)
    bio.seek(0)

    caption = await analyze_image(bio.read())
    await update.message.reply_text(f"توضیح تصویر:\n{caption}")

# --------- هندلر فایل متنی ---------
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    logger.info(f"Received document from {user_id}")

    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)
    file_path = f"document_{user_id}_{doc.file_name}"
    await file.download_to_drive(file_path)

    # خواندن فایل متنی (مثلاً txt)
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
    except Exception as e:
        logger.error(f"Error reading document: {e}")
        content = "متأسفانه نتوانستم فایل را بخوانم."

    os.remove(file_path)
    # ارسال محتوا به مدل برای پاسخ (مثلاً خلاصه یا سوال)
    response_text = await ask_openrouter(content)
    await update.message.reply_text(f"محتوای فایل:\n{response_text}")

# --------- تابع اصلی ----------
async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("🤖 ربات شما فعال شد!")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
