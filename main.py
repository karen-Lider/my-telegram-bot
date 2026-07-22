import logging
import os
from dotenv import load_dotenv

load_dotenv()

from groq import Groq
from telegram import LabeledPrice, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# 1. Инициализация Groq
groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None


# 2. Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Բարև Ձեզ! Ես Ձեր մասնագիտական բիզնես-վերլուծաբանն ու ռազմավարական խորհրդատուն եմ: "
        "Պատրաստ եմ օգնել Ձեզ բիզնես խնդիրների լուծման, վերլուծությունների և պլանավորման հարցում:\n\n"
        "Խորհրդատվության համար վճարելու համար ուղարկեք /pay հրամանը:"
    )


async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    title = "Բիզնես-խորհրդատվություն"
    description = (
        "Անհատական ​​ռազմավարական սեսիա բիզնես-վերլուծաբանի հետ"
    )
    payload = "consultation_payment"
    currency = "XTR"  # Валюта Telegram Stars

    # Сумма: 100 звёзд
    prices = [LabeledPrice("Խորհրդատվություն", amount=100)]

    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Для Stars - пустая строка
            currency=currency,
            prices=prices,
        )
    except Exception as e:
        logging.error(f"Ошибка отправки счета: {e}")
        await update.message.reply_text("Սխալ վճարման հաշիվ ուղարկելիս:")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if not groq_client:
        await update.message.reply_text(
            "Սխալ: GROQ_API_KEY-ը գտնված չէ կարգավորումներում:"
        )
        return

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a top-tier professional Business Analyst and strategic expert. "
                        "You provide expert, highly accurate, strategic business advice, data analysis, and professional insights. "
                        "ALWAYS respond in fluent, professional, and grammatically correct Armenian language."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            model="llama-3.3-70b-versatile",
        )
        answer = chat_completion.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        logging.error(f"Ошибка Groq: {e}")
        await update.message.reply_text(
            "Տեղի է ունեցել սխալ նեյրոցանցի հետ աշխատելիս:"
        )


# 3. Запуск бота через Polling
if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pay", pay_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logging.info("Бот запущен...")
    application.run_polling()
