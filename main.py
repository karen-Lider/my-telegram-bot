import logging
import os
import threading
from dotenv import load_dotenv
from flask import Flask

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

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ==========================================
# УКАЖИ ЗДЕСЬ СВОЙ TELEGRAM ID (ЧИСЛО):
OWNER_ID = 260743981  # Замени на свой ID!
# ==========================================

# 1. Заглушка Flask для работы на Render 24/7
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Инициализация Groq
groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# 3. Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == OWNER_ID:
        msg = (
            "Բարև Ձեզ, հարգելի ադմինիստրատոր! Ձեզ համար բոտի բոլոր ֆունկցիաները "
            "անվճար են: Կարող եք տալ ցանկացած հարց:"
        )
    else:
        msg = (
            "Բարև Ձեզ! Ես Ձեր մասնագիտական բիզնես-վերլուծաբանն ու ռազմավարական խորհրդատուն եմ: "
            "Պատրաստ եմ օգնել Ձեզ բիզնես խնդիրների լուծման, վերլուծությունների և պլանավորման հարցում:\n\n"
            "Խորհրդատվության համար վճարելու համար ուղարկեք /pay հրամանը:"
        )
    await update.message.reply_text(msg)

# 4. Команда /pay (Оплата 100 Звёзд)
async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_ID:
        await update.message.reply_text("Դուք ադմինիստրատորն եք: Ձեզ համար վճարում չի պահանջվում:")
        return

    chat_id = update.effective_chat.id
    title = "Բիզնես-խորհրդատվություն"
    description = "Անհատական ​​ռազմավարական սեսիա բիզնես-վերլուծաբանի հետ"
    payload = "consultation_payment"

    # Параметры STRICTLY для Telegram Stars (XTR)
    currency = "XTR"
    provider_token = ""
    prices = [LabeledPrice("Խորհրդատվություն", amount=100)]  # 100 звёзд

    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
        )
    except Exception as e:
        logging.error(f"Ошибка отправки счета: {e}")
        await update.message.reply_text("Սխալ վճարման հաշիվ ուղարկելիս:")

# 5. Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # Проверка: если не владелец, просим оплатить
    if user_id != OWNER_ID:
        await update.message.reply_text(
            "Ծառայությունից օգտվելու համար անհրաժեշտ է վճարել 100 աստղ (Telegram Stars):\n"
            "Ուղարկեք /pay հրամանը վճարման համար:"
        )
        return

    # Для владельца — ответы от нейросети Groq без ограничений
    if not groq_client:
        await update.message.reply_text("Սխալ: GROQ_API_KEY-ը գտնված չէ կարգավորումներում:")
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
        await update.message.reply_text("Տեղի է ունեցել սխալ նեյրոցանցի հետ աշխատելիս:")

# 6. Запуск
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pay", pay_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен...")
    application.run_polling()
