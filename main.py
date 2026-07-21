import os
import logging
from dotenv import load_dotenv  # <--- Импортируем загрузчик

load_dotenv()  # <--- Загружаем данные из .env файла

from flask import Flask, request
from telegram import Update, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Инициализация Flask для вебхуков и UptimeRobot
app = Flask(__name__)

# --- 1. Инициализация Groq ---
groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# --- 2. Логика работы бота (Бизнес-аналитик на армянском) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Բարև Ձեզ! Ես Ձեր մասնագիտական բիզնես-վերլուծաբանն ու ռազմավարական խորհրդատուն եմ: "
        "Պատրաստ եմ օգնել Ձեզ բիզնես խնդիրների լուծման, վերլուծությունների և պլանավորման հարցում:\n\n"
        "Խորհրդատվության համար վճարելու համար ուղարկեք /pay հրամանը:"
    )

# Команда для оплаты консультации Звездами (Telegram Stars)
async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    title = "Բիզնես-խորհրդատվություն"
    description = "Անհատական ​​ռազմավարական սեսիա բիզնես-վերլուծաբանի հետ"
    payload = "consultation_payment" 
    currency = "XTR"  # Валюта Telegram Stars
    
    # 100 звезд (можно изменить сумму при желании)
    prices = [LabeledPrice("Խորհրդատվություն", 100)] 

    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # ДЛЯ STARS ОБЯЗАТЕЛЬНО ПУСТАЯ СТРОКА!
            currency=currency,
            prices=prices,
        )
    except Exception as e:
        logging.error(f"Ошибка отправки счета: {e}")
        await update.message.reply_text("Սխալ վճարման հաշիվ ուղարկելիս:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
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
                    )
                },
                {"role": "user", "content": user_text}
            ],
            model="llama-3.3-70b-versatile",
        )
        answer = chat_completion.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        logging.error(f"Ошибка Groq: {e}")
        await update.message.reply_text("Տեղի է ունեցել սխալ նեյրոցանցի հետ աշխատելիս:")

# --- 3. Настройка приложения Telegram ---
token = os.environ.get("TELEGRAM_BOT_TOKEN")
application = Application.builder().token(token).build()

# Добавляем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("pay", pay_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- 4. Маршруты веб-сервера (Flask) ---
@app.route(f"/{token}", methods=["POST"])
def webhook():
    """Прием сообщений от Telegram через вебхук"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

@app.route("/", methods=["GET", "HEAD"])
def index():
    """Страница для UptimeRobot (отвечает на GET и HEAD запросы)"""
    return "Bot is running!", 200

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    
    # Автоматическая привязка вебхука к Render при запуске
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{token}"
        application.bot.set_webhook(webhook_url)
        logging.info(f"Вебхук установлен: {webhook_url}")

    application.initialize()
    application.start()
    
    # Запуск сервера
    app.run(host="0.0.0.0", port=PORT)
