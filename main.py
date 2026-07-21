import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. Легкий веб-сервер для бесплатного тарифа Render (НЕ ТРОГАТЬ) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Запускаем веб-сервер в фоновом потоке
threading.Thread(target=run_http_server, daemon=True).start()

# --- 2. Инициализация Groq ---
groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# --- 3. Логика работы бота (Бизнес-аналитик на армянском) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Բարև Ձեզ! Ես Ձեր մասնագիտական բիզնես-վերլուծաբանն ու ռազմավարական խորհրդատուն եմ: "
        "Պատրաստ եմ օգնել Ձեզ բիզնես խնդիրների լուծման, վերլուծությունների և պլանավորման հարցում:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    if not groq_client:
        await update.message.reply_text("Սխալ: GROQ_API_KEY-ը գտնված չէ կարգավորումներում:")
        return

    try:
        # Инструкция для нейросети: быть бизнес-аналитиком и писать на армянском
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
        await update.message.reply_text("Տեղի է ունեցել սխալ նეյրոցանցի հետ աշխատելիս:")

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("Ошибка: TELEGRAM_BOT_TOKEN не найден в настройках!")
        return

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
