#!/usr/bin/env python3
# ChatGPT Telegram Bot - РАБОЧАЯ ВЕРСИЯ (OpenAI >=1.0.0)

from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== ТВОИ НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
OPENAI_API_KEY = "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"
# ====================================

# Создаём клиента (новый синтаксис)
client = OpenAI(api_key=OPENAI_API_KEY)

# Храним историю диалогов для каждого пользователя
user_histories = {}

def get_user_history(user_id):
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_history(user_id).clear()
    await update.message.reply_text(
        "🤖 **ChatGPT Бот запущен!**\n\n"
        "Просто напиши мне что угодно — я отвечу.\n"
        "Команды:\n"
        "/clear — очистить историю\n"
        "/help — помощь"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_histories:
        user_histories[user_id].clear()
    await update.message.reply_text("🗑️ История диалога очищена!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    history = get_user_history(user_id)
    history.append({"role": "user", "content": user_message})
    
    # Ограничиваем историю последними 10 сообщениями
    if len(history) > 10:
        history = history[-10:]
        user_histories[user_id] = history
    
    try:
        # НОВЫЙ СПОСОБ ВЫЗОВА (через клиент)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты дружелюбный и полезный помощник. Отвечай кратко и по делу."},
                *history
            ],
            max_tokens=1000,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")
        history.pop()  # Удаляем сообщение, которое не прошло

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    print("🚀 ChatGPT Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
