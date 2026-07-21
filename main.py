import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 1. Загружаем переменные из .env файла
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 👑 Твой ID админа (для тебя бот всегда БЕСПЛАТНЫЙ)
ADMIN_IDS = [260743981]

# База активных пользователей (после оплаты)
users_has_access = {}

# 2. Подключаемся к ИИ (Groq)
ai_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

logging.basicConfig(level=logging.INFO)

# ================= 🤖 ЛОГИКА БОТА =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    has_access = users_has_access.get(user_id, False) or (user_id in ADMIN_IDS)

    if has_access:
        # Ответ для тебя / авторизованного пользователя
        await update.message.reply_text(
            "👋 Բարև ձեզ! Ձեր մուտքն ակտիվ է: Ուղարկեք ինձ ձեր բիզնես-հարցը:"
        )
    else:
        # Ответ для всех ОСТАЛЬНЫХ пользователей (требование оплаты)
        keyboard = [
            [InlineKeyboardButton(text="⭐ Գնել մուտք (10 Stars)", callback_data="buy")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "👋 Բարև ձեզ! Ես BOLD Analyst Assistant-ն եմ:\n\n"
            "🔒 Բոտից օգտվելու համար անհրաժեշտ է ձեռք բերել մուտք Telegram Stars-ի միջոցով:",
            reply_markup=reply_markup
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    has_access = users_has_access.get(user_id, False) or (user_id in ADMIN_IDS)

    # Защита: если нет доступа, ИИ даже не вызывается
    if not has_access:
        await update.message.reply_text(
            "🔒 Ձեր մուտքն ակտիվ չէ: Սեղմեք /start մուտքը վճարելու համար ⭐:"
        )
        return

    # Запрос к ИИ для разрешенных пользователей
    user_text = update.message.text
    status_msg = await update.message.reply_text("🧠 *Վերլուծում եմ հարցումը...*", parse_mode="Markdown")

    try:
        completion = ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Դուք BOLD ընկերության փորձառու ավագ բիզնես-վերլուծաբանն եք: "
                        "Պատասխանեք հարցերին կոնկրետ, խորը, առանց «ջրի» և բացառապես հայերենով:"
                    )
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )

        answer = completion.choices[0].message.content
        await status_msg.edit_text(answer)

    except Exception as e:
        await status_msg.edit_text(f"❌ Սխալ ԻԻ: {e}")

# ================= 🚀 ЗАПУСК БОТА =================

def main():
    if not BOT_TOKEN:
        print("❌ Ошибка: Не найден TELEGRAM_BOT_TOKEN в файле .env!")
        return
    if not GROQ_API_KEY:
        print("❌ Ошибка: Не найден GROQ_API_KEY в файле .env!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Бот BOLD Analyst успешно запущен и готов к тестам!")
    app.run_polling()

if __name__ == "__main__":
    main()