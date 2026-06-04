#!/usr/bin/env python3
# Physics Exam Bot - Магнитные явления (БЕЗ ОШИБОК FORMATTING)

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
# ================================

# ========== ТЕОРИЯ ПЕРЕД ЭКЗАМЕНОМ (БЕЗ СПЕЦСИМВОЛОВ) ==========
THEORY_TEXT = """
*КРАТКАЯ ТЕОРИЯ: МАГНИТНЫЕ ЯВЛЕНИЯ*

1. Что такое магнитное поле?
Магнитное поле - это особая форма материи, которая существует вокруг движущихся электрических зарядов и постоянных магнитов. Оно действует ТОЛЬКО на движущиеся заряды.

2. Правило буравчика (правой руки)
Определяет НАПРАВЛЕНИЕ магнитного поля вокруг проводника с током:
Если буравчик ввинчивать по направлению тока, то рукоятка покажет направление линий магнитного поля.

3. Правило левой руки
Определяет НАПРАВЛЕНИЕ силы, действующей на проводник с током (сила Ампера) или на заряженную частицу (сила Лоренца):
Если левую руку расположить так, чтобы линии поля входили в ладонь, а 4 пальца указывали направление тока, то отставленный большой палец покажет направление силы.

4. Электромагнитная индукция (Фарадей)
При ИЗМЕНЕНИИ магнитного поля, пронизывающего замкнутый контур, в этом контуре возникает электрический ток.

5. Правило Ленца
Индукционный ток всегда направлен так, чтобы своим магнитным полем ПРОТИВОДЕЙСТВОВАТЬ изменению магнитного потока, которое его вызвало.

6. Ферромагнетики
Вещества, которые сильно намагничиваются во внешнем магнитном поле и сохраняют намагниченность после его снятия:
- Железо (Fe)
- Никель (Ni)
- Кобальт (Co)
- Их сплавы
Именно из них делают постоянные магниты.

7. Сила Ампера
Сила, с которой магнитное поле действует на проводник с током: F = B * I * L * sin a
Максимальна, когда проводник перпендикулярен линиям поля.

8. Магнитное поле Земли
Постепенно ослабевает. Раз в несколько сотен тысяч лет происходит ИНВЕРСИЯ - полюса меняются местами. Последняя инверсия была около 780 000 лет назад.
"""

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
        "explanation": "Правильно! Магнитное поле - это особая форма материи, существующая вокруг движущихся электрических зарядов и постоянных магнитов. Оно действует только на движущиеся заряды."
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
        "explanation": "Правильно! Магнитное поле создаётся любыми движущимися заряженными частицами. Чем больше скорость и заряд - тем сильнее поле."
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
        "explanation": "Правильно! Магнитная индукция B - это векторная величина, силовая характеристика магнитного поля. Показывает, с какой силой поле действует на движущийся заряд."
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
        "explanation": "Правильно! Направление магнитного поля прямого проводника с током определяется правилом буравчика (правой руки)."
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
        "explanation": "Правильно! Правило левой руки определяет направление силы, действующей на проводник с током в магнитном поле (сила Ампера) или на движущуюся заряженную частицу (сила Лоренца)."
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
        "explanation": "Правильно! Электромагнитная индукция открыта Фарадеем. При изменении магнитного поля, пронизывающего замкнутый контур, в нём возникает индукционный ток."
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
        "explanation": "Правильно! Правило Ленца: индукционный ток всегда направлен так, чтобы своим магнитным полем противодействовать изменению магнитного потока, которое его вызвало."
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
        "explanation": "Правильно! Ферромагнетики (железо, никель, кобальт, их сплавы) сильно намагничиваются во внешнем магнитном поле и сохраняют намагниченность после его снятия. Именно из них делают постоянные магниты."
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
        "explanation": "Правильно! Сила Ампера - это сила, с которой магнитное поле действует на проводник с током. Она максимальна, когда проводник перпендикулярен линиям поля."
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
        "explanation": "Правильно! Магнитное поле Земли ослабевает. Примерно раз в несколько сотен тысяч лет происходит инверсия - полюса меняются местами. Последняя была около 780 000 лет назад."
    }
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton("Начать экзамен")]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_text(
        "Экзамен по физике: Магнитные явления\n\n"
        "Я проверю твои знания по теме.\n"
        "Перед экзаменом я дам краткую теорию.\n\n"
        "Нажми 'Начать экзамен', чтобы продолжить.",
        reply_markup=reply_markup
    )

async def send_theory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Изучил, готов к экзамену", callback_data="ready_for_exam")]
    ])
    
    await update.message.reply_text(
        THEORY_TEXT,
        reply_markup=keyboard
    )

async def start_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Удаляем сообщение с теорией
    try:
        await query.message.delete()
    except Exception:
        pass
    
    # Начинаем экзамен
    random.shuffle(QUESTIONS)
    context.user_data['questions'] = QUESTIONS[:10]
    context.user_data['current'] = 0
    context.user_data['score'] = 0
    context.user_data['answered'] = 0
    
    await ask_question(query.message, context)

async def ask_question(message, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data['current']
    questions = context.user_data['questions']
    
    if q_index >= len(questions):
        score = context.user_data['score']
        total = context.user_data['answered']
        percent = (score / total) * 100 if total > 0 else 0
        
        msg = f"🏆 ЭКЗАМЕН ОКОНЧЕН!\n\n"
        msg += f"Правильных ответов: {score} из {total}\n"
        msg += f"Процент: {percent:.1f}%\n\n"
        
        if percent >= 90:
            msg += "Отлично! Ты шаришь в магнетизме!"
        elif percent >= 70:
            msg += "Хороший результат, но есть куда расти."
        elif percent >= 50:
            msg += "Средний результат. Повтори теорию."
        else:
            msg += "Жесть. Открой учебник и возвращайся."
        
        await message.reply_text(msg)
        return
    
    q = questions[q_index]
    
    msg = f"ВОПРОС {q_index + 1}/{len(questions)}:\n\n"
    msg += f"{q['question']}\n\n"
    msg += f"1. {q['options'][0]}\n"
    msg += f"2. {q['options'][1]}\n"
    msg += f"3. {q['options'][2]}\n"
    msg += f"4. {q['options'][3]}\n\n"
    msg += "Отправь номер ответа (1-4) или текст ответа."
    
    await message.reply_text(msg)

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'questions' not in context.user_data or context.user_data['current'] >= len(context.user_data.get('questions', [])):
        await update.message.reply_text("Сначала изучи теорию и начни экзамен кнопкой.")
        return
    
    user_text = update.message.text.strip()
    q_index = context.user_data['current']
    q = context.user_data['questions'][q_index]
    
    answer_index = None
    if user_text in ['1', '2', '3', '4']:
        answer_index = int(user_text) - 1
    else:
        user_lower = user_text.lower()
        for i, opt in enumerate(q['options']):
            if opt.lower() == user_lower or opt.lower() in user_lower:
                answer_index = i
                break
    
    if answer_index is None:
        await update.message.reply_text("Не понял ответ. Напиши номер (1-4) или текст варианта.")
        return
    
    is_correct = (answer_index == q['correct'])
    context.user_data['answered'] += 1
    
    if is_correct:
        context.user_data['score'] += 1
        await update.message.reply_text(f"✅ ПРАВИЛЬНО!\n\n{q['explanation']}")
    else:
        correct_text = q['options'][q['correct']]
        await update.message.reply_text(
            f"❌ НЕПРАВИЛЬНО!\n\n"
            f"Твой ответ: {q['options'][answer_index]}\n"
            f"Правильный ответ: {correct_text}\n\n"
            f"ПОЧЕМУ ТАК:\n{q['explanation']}"
        )
    
    context.user_data['current'] += 1
    await ask_question(update.message, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Начать экзамен":
        await send_theory(update, context)
    else:
        await check_answer(update, context)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_exam, pattern="ready_for_exam"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Physics Exam Bot запущен!")
    print("Тема: Магнитные явления")
    print("Бот доступен для всех пользователей")
    app.run_polling()

if __name__ == "__main__":
    main()
