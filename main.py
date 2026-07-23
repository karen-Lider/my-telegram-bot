import logging
import os
import threading
from dotenv import load_dotenv
from flask import Flask
from groq import Groq
from telegram import LabeledPrice, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

# Загрузка переменных
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

groq_client = Groq(api_key=GROQ_API_KEY)

# Flask сервер для Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# Функция отправки инвойса (Твой оригинальный текст)
async def send_payment_invoice(chat_id, context):
    title = "Բիզնես-խորհրդատվություն"
    description = "Անհատական ռազմավարական սեսիա բիզնես-վերլուծաբանի հետ"
    payload = "bot_subscription_payload"
    currency = "XTR"
    prices = [LabeledPrice("Заплатить", 100)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Для Telegram Stars обязательно пустая строка!
        currency=currency,
        prices=prices,
    )


# /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Բարև! Ուղարկեք Ձեր հարցը:")


# Обработка сообщений с проверкой оплаты
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # Если пользователь еще не оплатил — просим оплатить
    if not context.user_data.get("is_paid", False):
        await update.message.reply_text(
            "Ծառայությունից օգտվելու համար անհրաժեշտ է վճարել 100 աստղ (Telegram Stars):"
        )
        await send_payment_invoice(update.message.chat_id, context)
        return

    # Если оплачено — отправляем в Groq
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты профессиональный финансовый аналитик. Отвечай подробно и понятно."},
                {"role": "user", "content": user_text},
            ],
        )
        response_text = completion.choices[0].message.content
        await update.message.reply_text(response_text)
    except Exception as e:
        logging.error(f"Ошибка Groq API: {e}")
        await update.message.reply_text("Ցավոք, սխալ տեղի ունեցավ: Խնդրում ենք փորձել փոքր-ինչ ուշ:")


# Обработка пре-чекаута
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


# Подтверждение оплаты
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["is_paid"] = True
    await update.message.reply_text("Շնորհակալություն վճարման համար! Այժմ կարող եք ուղարկել Ձեր հարցերը:")


def main():
    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == "__main__":
    main()
