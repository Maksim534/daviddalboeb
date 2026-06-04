#!/usr/bin/env python3
# Wordle Helper Bot - Помощник для игры в слова

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import re

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
YOUR_CHAT_ID = 8564427714  # Твой Telegram ID
# ================================

# Базовый словарь русских слов (можно расширить)
# В реальности лучше подключить большой словарь, но для примера хватит
RUSSIAN_WORDS = [
    "автор", "адрес", "актер", "алмаз", "апрель", "арбуз", "багаж", "базар", 
    "банан", "банка", "барак", "баржа", "барон", "бассейн", "башня", "бегун", 
    "белка", "берег", "билет", "биржа", "бланк", "блеск", "блин", "блок", 
    "бобер", "богач", "бодро", "бокал", "болото", "борщ", "бочка", "брат", 
    "бревно", "брелок", "бриз", "бровь", "бронза", "брюки", "букет", "булка", 
    "бумага", "буран", "буря", "бусы", "бык", "быль", "вагон", "ваза", 
    "вакуум", "валюта", "варвар", "варенье", "вата", "ведро", "веер", "вектор", 
    "велосипед", "венок", "весы", "ветер", "вечер", "видео", "визит", "вилка", 
    "вино", "вирус", "витрина", "вода", "воздух", "война", "волк", "воля", 
    "ворот", "восход", "враг", "время", "вторник", "выбор", "вывод", "высота"
]

def load_full_dictionary():
    """Загружает большой словарь русских слов"""
    try:
        # Попробуем скачать словарь с GitHub
        url = "https://raw.githubusercontent.com/danakt/russian-words/master/russian_words.txt"
        response = requests.get(url, timeout=10)
        words = response.text.splitlines()
        # Фильтруем только слова длиной 5 букв
        return [w.lower() for w in words if len(w) == 5 and w.isalpha()]
    except:
        # Если не получилось - используем базовый словарь
        return RUSSIAN_WORDS

# Загружаем словарь
print("📚 Загружаю словарь...")
WORDS_LIST = load_full_dictionary()
print(f"✅ Загружено {len(WORDS_LIST)} слов")

def is_authorized(update: Update):
    return update.effective_user.id == YOUR_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("❌ Доступ запрещён")
        return
    
    await update.message.reply_text(
        "🎮 **Wordle Помощник**\n\n"
        "Как пользоваться:\n"
        "1. Напиши /set слово\n"
        "2. Укажи буквы:\n"
        "   • зелёные: `А` (на своём месте)\n"
        "   • жёлтые: `?Б` (есть, не на этом месте)\n"
        "   • серые: `-В` (нет в слове)\n\n"
        "**Пример:**\n"
        "Если первая буква 'К', третья 'Т', есть 'А' не на втором месте, и нет букв 'О','Р':\n"
        "`/set К?А-ОР ?-Т`\n\n"
        "Или просто опиши словами:\n"
        "`первая К, третья Т, есть А не на втором, нет О Р`\n\n"
        "Команды:\n"
        "/set условия — найти слова\n"
        "/help — помощь\n"
        "/stats — статистика"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text(
        f"📊 **Статистика словаря**\n"
        f"📚 Всего слов: {len(WORDS_LIST)}\n"
        f"🔤 Длина слов: 5 букв\n"
        f"📅 Словарь обновлён"
    )

def parse_conditions(text):
    """Парсит условия из текста"""
    green = {}  # позиция -> буква
    yellow = {}  # позиция -> буква (не на этой позиции)
    gray = set()  # буквы, которых нет
    
    # Ищем буквы на позициях (формат: "буква цифра" или "цифра буква")
    pos_matches = re.findall(r'(\d+)\s*([а-яА-Я])|([а-яА-Я])\s*(\d+)', text)
    for match in pos_matches:
        if match[0] and match[1]:  # цифра буква
            pos, letter = int(match[0]), match[1].lower()
            green[pos] = letter
        elif match[2] and match[3]:  # буква цифра
            letter, pos = match[2].lower(), int(match[3])
            green[pos] = letter
    
    # Ищем зелёные буквы (на месте)
    green_match = re.findall(r'зел[её]н(?:ая|ые?)?\s*[:\-]?\s*([а-яА-Я]+)', text, re.IGNORECASE)
    for letters in green_match:
        for i, letter in enumerate(letters.lower()):
            green[i+1] = letter
    
    # Ищем жёлтые буквы (есть, не на месте)
    yellow_match = re.findall(r'желт(?:ая|ые?)?\s*[:\-]?\s*([а-яА-Я]+)', text, re.IGNORECASE)
    for letters in yellow_match:
        for letter in letters.lower():
            # Пока без позиции, просто добавляем в жёлтые
            yellow[0] = yellow.get(0, "") + letter
    
    # Ищем серые буквы (нет в слове)
    gray_match = re.findall(r'сер(?:ая|ые?)?\s*[:\-]?\s*([а-яА-Я]+)', text, re.IGNORECASE)
    for letters in gray_match:
        gray.update(letters.lower())
    
    return green, yellow, gray

def find_words(green, yellow, gray, length=5):
    """Находит слова по условиям"""
    results = []
    
    for word in WORDS_LIST:
        if len(word) != length:
            continue
        
        # Проверяем зелёные буквы
        valid = True
        for pos, letter in green.items():
            if pos > len(word) or word[pos-1] != letter:
                valid = False
                break
        
        if not valid:
            continue
        
        # Проверяем серые буквы (не должно быть в слове)
        for letter in gray:
            if letter in word:
                valid = False
                break
        
        if not valid:
            continue
        
        # Проверяем жёлтые буквы (должны быть в слове, но не на указанной позиции)
        for pos, letters in yellow.items():
            for letter in letters:
                if letter not in word:
                    valid = False
                    break
                if pos > 0 and word[pos-1] == letter:
                    valid = False
                    break
            if not valid:
                break
        
        if valid:
            results.append(word)
    
    return results

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажи условия.\n\n"
            "Пример:\n"
            "`первая А, третья С, есть Е, нет Т Р`\n"
            "Или напиши словами что знаешь."
        )
        return
    
    text = ' '.join(context.args).lower()
    
    # Пробуем распарсить
    green, yellow, gray = parse_conditions(text)
    
    # Если парсинг не дал результатов, пробуем простой режим
    if not green and not yellow and not gray:
        # Простой режим: ищем слова с заданными буквами
        required = set(re.findall(r'[а-я]', text))
        results = [w for w in WORDS_LIST if all(c in w for c in required)]
    else:
        results = find_words(green, yellow, gray)
    
    if not results:
        await update.message.reply_text("❌ Не найдено слов по твоим условиям.")
        return
    
    # Формируем ответ
    if len(results) > 50:
        msg = f"🔍 Найдено {len(results)} слов. Показываю первые 50:\n\n"
        display = results[:50]
    else:
        msg = f"🔍 Найдено {len(results)} слов:\n\n"
        display = results
    
    # Группируем по 10 слов в строке
    lines = []
    for i in range(0, len(display), 10):
        lines.append(" | ".join(display[i:i+10]))
    msg += "\n".join(lines)
    
    if len(results) > 50:
        msg += f"\n\n... и ещё {len(results)-50} слов."
    
    await update.message.reply_text(msg)

async def manual_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка прямого ввода формата: позиция-буква"""
    if not is_authorized(update):
        return
    
    text = update.message.text.lower()
    
    # Формат: 1а 3с +е -т -р
    green = {}
    yellow = {}
    gray = set()
    
    # Парсим позиции с буквами
    pos_matches = re.findall(r'(\d+)([а-я])', text)
    for pos, letter in pos_matches:
        green[int(pos)] = letter
    
    # Парсим жёлтые буквы (+)
    yellow_matches = re.findall(r'\+([а-я])', text)
    for letter in yellow_matches:
        yellow[0] = yellow.get(0, "") + letter
    
    # Парсим серые буквы (-)
    gray_matches = re.findall(r'-([а-я])', text)
    gray.update(gray_matches)
    
    results = find_words(green, yellow, gray)
    
    if not results:
        await update.message.reply_text("❌ Не найдено слов.")
        return
    
    if len(results) > 30:
        msg = f"🔍 Найдено {len(results)} слов. Показываю первые 30:\n\n"
        display = results[:30]
    else:
        msg = f"🔍 Найдено {len(results)} слов:\n\n"
        display = results
    
    lines = []
    for i in range(0, len(display), 8):
        lines.append(" | ".join(display[i:i+8]))
    msg += "\n".join(lines)
    
    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("set", find))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manual_input))
    
    print("🚀 Wordle Helper Bot запущен!")
    print(f"📚 Словарь: {len(WORDS_LIST)} слов")
    app.run_polling()

if __name__ == "__main__":
    main()
