#!/usr/bin/env python3
# Physics Exam Bot - Магнитные явления

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
YOUR_CHAT_ID = 8564427714
# ================================

# ========== БАЗА ВОПРОСОВ ==========
QUESTIONS = [
    {
        "question": "Что такое магнитное поле?",
        "options": [
            "Область вокруг движущихся зарядов и магнитов",
            "Область вокруг неподвижных зарядов",
            "Поток частиц в вакууме",
            "Вихревое электрическое поле"
        ],
        "correct": 0,
        "explanation": "✅ Магнитное поле — это особая форма материи, существующая вокруг движущихся электрических зарядов и постоянных магнитов. Оно действует только на движущиеся заряды."
    },
    {
        "question": "Какие частицы создают магнитное поле?",
        "options": [
            "Только протоны",
            "Только электроны",
            "Любые движущиеся заряженные частицы",
            "Только нейтроны"
        ],
        "correct": 2,
        "explanation": "✅ Магнитное поле создаётся любыми движущимися заряженными частицами. Чем больше скорость и заряд — тем сильнее поле."
    },
    {
        "question": "Что такое магнитная индукция (B)?",
        "options": [
            "Сила, действующая на заряд",
            "Силовая характеристика магнитного поля",
            "Энергия магнитного поля",
            "Напряжённость электрического поля"
        ],
        "correct": 1,
        "explanation": "✅ Магнитная индукция B — это векторная величина, силовая характеристика магнитного поля. Показывает, с какой силой поле действует на движущийся заряд."
    },
    {
        "question": "Как определяется направление магнитного поля проводника с током?",
        "options": [
            "Правилом левой руки",
            "Правилом буравчика (правой руки)",
            "Правилом Ленца",
            "Законом Ома"
        ],
        "correct": 1,
        "explanation": "✅ Направление магнитного поля прямого проводника с током определяется правилом буравчика (правой руки): если буравчик ввинчивать по току, то рукоятка покажет направление линий поля."
    },
    {
        "question": "Что определяет правило левой руки?",
        "options": [
            "Направление магнитного поля",
            "Направление силы Ампера или Лоренца",
            "Направление индукционного тока",
            "Направление электрического поля"
        ],
        "correct": 1,
        "explanation": "✅ Правило левой руки определяет направление силы, действующей на проводник с током в магнитном поле (сила Ампера) или на движущуюся заряженную частицу (сила Лоренца)."
    },
    {
        "question": "Что такое явление электромагнитной индукции?",
        "options": [
            "Возникновение тока в замкнутом контуре при изменении магнитного поля",
            "Действие магнитного поля на ток",
            "Притяжение магнитов",
            "Намагничивание железа"
        ],
        "correct": 0,
        "explanation": "✅ Электромагнитная индукция открыта Фарадеем. При изменении магнитного поля, пронизывающего замкнутый контур, в нём возникает индукционный ток."
    },
    {
        "question": "Сформулируйте правило Ленца",
        "options": [
            "Индукционный ток направлен так, чтобы увеличить изменения магнитного поля",
            "Индукционный ток направлен так, чтобы противодействовать изменениям магнитного поля",
            "Индукционный ток не зависит от изменений поля",
            "Индукционный ток всегда постоянен"
        ],
        "correct": 1,
        "explanation": "✅ Правило Ленца: индукционный ток всегда направлен так, чтобы своим магнитным полем противодействовать изменению магнитного потока, которое его вызвало."
    },
    {
        "question": "Что такое ферромагнетики?",
        "options": [
            "Вещества, не реагирующие на магнитное поле",
            "Вещества с очень слабой магнитной проницаемостью",
            "Вещества, сильно намагничивающиеся во внешнем поле (железо, никель, кобальт)",
            "Жидкие магниты"
        ],
        "correct": 2,
        "explanation": "✅ Ферромагнетики (железо, никель, кобальт, их сплавы) сильно намагничиваются во внешнем магнитном поле и сохраняют намагниченность после его снятия. Именно из них делают постоянные магниты."
    },
    {
        "question": "Что такое сила Ампера?",
        "options": [
            "Сила, действующая на заряд в магнитном поле",
            "Сила, действующая на проводник с током в магнитном поле",
            "Сила притяжения двух проводников",
            "Сила отталкивания магнитов"
        ],
        "correct": 1,
        "explanation": "✅ Сила Ампера — это сила, с которой магнитное поле действует на проводник с током. Она максимальна, когда проводник перпендикулярен линиям поля."
    },
    {
        "question": "Как меняется магнитное поле Земли со временем?",
        "options": [
            "Оно постоянно",
            "Оно постепенно ослабевает, полюса могут меняться местами",
            "Оно исчезнет через 100 лет",
            "Оно усиливается каждый год"
        ],
        "correct": 1,
        "explanation": "✅ Магнитное поле Земли ослабевает. Примерно раз в несколько сотен тысяч лет происходит инверсия — полюса меняются местами. Последняя была около 780 000 лет назад."
    }
]

def is_authorized(update: Update):
    return update.effective_user.id == YOUR_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("❌ Доступ запрещён")
        return
    
    # Создаём кнопки для удобства
    buttons = [[KeyboardButton("🔘 Начать экзамен"), KeyboardButton("📊 Статистика")]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_text(
        "🧲 **Экзамен по физике: Магнитные явления**\n\n"
        "Я задам тебе 10 вопросов. На каждый вопрос будет 4 варианта ответа.\n"
        "Отвечай цифрой (1-4) или текстом.\n\n"
        "Если ошибёшься — покажу правильный ответ и объясню почему.\n\n"
        "Нажми **🔘 Начать экзамен** или напиши /exam",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    
    # Перемешиваем вопросы и берём 10 (или меньше, если их меньше)
    random.shuffle(QUESTIONS)
    context.user_data['questions'] = QUESTIONS[:10]
    context.user_data['current'] = 0
    context.user_data['score'] = 0
    context.user_data['answered'] = 0
    
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data['current']
    questions = context.user_data['questions']
    
    if q_index >= len(questions):
        # Экзамен окончен
        score = context.user_data['score']
        total = context.user_data['answered']
        percent = (score / total) * 100 if total > 0 else 0
        
        msg = f"🏆 **Экзамен окончен!**\n\n"
        msg += f"✅ Правильных ответов: {score} из {total}\n"
        msg += f"📊 Процент: {percent:.1f}%\n\n"
        
        if percent >= 90:
            msg += "🎉 Отлично! Ты шаришь в магнетизме!"
        elif percent >= 70:
            msg += "👍 Хороший результат, но есть куда расти."
        elif percent >= 50:
            msg += "📚 Средний результат. Повтори теорию, братан."
        else:
            msg += "💀 Жесть. Открой учебник и возвращайся."
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    q = questions[q_index]
    
    # Формируем сообщение с вопросом
    msg = f"**Вопрос {q_index + 1}/{len(questions)}:**\n\n"
    msg += f"{q['question']}\n\n"
    msg += "1️⃣ " + q['options'][0] + "\n"
    msg += "2️⃣ " + q['options'][1] + "\n"
    msg += "3️⃣ " + q['options'][2] + "\n"
    msg += "4️⃣ " + q['options'][3] + "\n\n"
    msg += "_Отправь номер ответа (1-4) или текст ответа._"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    
    # Если экзамен не начат
    if 'questions' not in context.user_data or context.user_data['current'] >= len(context.user_data.get('questions', [])):
        await update.message.reply_text("❌ Сначала начни экзамен командой /exam")
        return
    
    user_text = update.message.text.strip()
    q_index = context.user_data['current']
    q = context.user_data['questions'][q_index]
    
    # Определяем, какой ответ выбрал пользователь
    answer_index = None
    
    # Проверка по цифре
    if user_text in ['1', '2', '3', '4']:
        answer_index = int(user_text) - 1
    else:
        # Проверка по тексту (ищем совпадение с вариантом)
        user_lower = user_text.lower()
        for i, opt in enumerate(q['options']):
            if opt.lower() == user_lower or opt.lower() in user_lower:
                answer_index = i
                break
    
    if answer_index is None:
        await update.message.reply_text("❌ Не понял ответ. Напиши номер (1-4) или текст варианта.")
        return
    
    # Проверяем правильность
    is_correct = (answer_index == q['correct'])
    context.user_data['answered'] += 1
    
    if is_correct:
        context.user_data['score'] += 1
        await update.message.reply_text(f"✅ **Правильно!**\n\n{q['explanation']}", parse_mode='Markdown')
    else:
        correct_text = q['options'][q['correct']]
        await update.message.reply_text(
            f"❌ **Неправильно!**\n\n"
            f"Твой ответ: {q['options'][answer_index]}\n"
            f"✅ Правильный ответ: {correct_text}\n\n"
            f"📖 **Почему так:**\n{q['explanation']}",
            parse_mode='Markdown'
        )
    
    context.user_data['current'] += 1
    await ask_question(update, context)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    
    # Статистика по вопросам в этой сессии
    msg = "📊 **Статистика по магнитным явлениям**\n\n"
    msg += "🧲 Магнитное поле создаётся движущимися зарядами\n"
    msg += "🔧 Правило буравчика — для направления поля\n"
    msg += "✋ Правило левой руки — для силы Ампера/Лоренца\n"
    msg += "⚡ Электромагнитная индукция — ток при изменении поля\n"
    msg += "🔄 Правило Ленца — противодействие изменению\n"
    msg += "🧲 Ферромагнетики — железо, никель, кобальт\n\n"
    msg += "Напиши /exam чтобы проверить себя!"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔘 Начать экзамен":
        await exam(update, context)
    elif text == "📊 Статистика":
        await stats(update, context)
    else:
        await check_answer(update, context)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("exam", exam))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Physics Exam Bot запущен!")
    print("📚 Тема: Магнитные явления")
    app.run_polling()

if __name__ == "__main__":
    main()
