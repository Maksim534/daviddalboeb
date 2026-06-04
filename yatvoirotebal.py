#!/usr/bin/env python3
# Brawl Stars Account Tracker - ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ

import aiohttp
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
from datetime import datetime

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
# Твой Telegram бот
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"

# Brawl Stars API токен (твой, который получил)
BS_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjQ5MzNkNmE2LTEzNGItNDRkNS1hN2QzLTg2ODFjMjQ4YTUxOCIsImlhdCI6MTc4MDUzMjkwMiwic3ViIjoiZGV2ZWxvcGVyL2E0ZWQ5YzQ1LTVhZjMtN2Y0NS03YjQ3LTkxNTE4MWFkY2JhZCIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTYzLjUzLjI0NC42OSJdLCJ0eXBlIjoiY2xpZW50In1dfQ.AIuccx4lUjhHu8w34rrTWjkdvyT2oCBPhCIqwB-VrPbrFXQFKTbCARsTXC2HLMFTwmD1N3KGYgy7t8CEfArwew"

# ID твоего Telegram чата (куда слать логи)
LOG_CHAT_ID = "8564427714"
# ================================

# Функция для отправки логов
async def log_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": LOG_CHAT_ID, "text": text}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

# Очистка тега игрока (ВАЖНО!)
def clean_tag(tag):
    """Очищает тег от лишних символов и решётки"""
    tag = tag.strip().upper()
    # Убираем решётку если есть
    if tag.startswith('#'):
        tag = tag[1:]
    # Убираем всякий мусор
    tag = ''.join(c for c in tag if c.isalnum() or c == '#')
    return tag

# Запрос к Brawl Stars API
async def fetch_bs_api(endpoint, params=None):
    url = f"https://api.brawlstars.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {BS_API_TOKEN}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                return {"error": f"Ошибка {response.status}: {error_text[:200]}"}

# Получение полной информации об игроке
async def get_player_info(tag):
    clean_tag_str = clean_tag(tag)
    # API Brawl Stars работает с тегом без решётки
    return await fetch_bs_api(f"players/{clean_tag_str}")

# Оценка качества аккаунта
def evaluate_account(player_data):
    if "error" in player_data:
        return None
    
    trophies = player_data.get("trophies", 0)
    highest_trophies = player_data.get("highestTrophies", 0)
    exp_level = player_data.get("expLevel", 0)
    
    # Считаем бойцов
    brawlers = player_data.get("brawlers", [])
    total_brawlers = len(brawlers)
    
    legendaries = len([b for b in brawlers if b.get("rarity") == "LEGENDARY"])
    mythics = len([b for b in brawlers if b.get("rarity") == "MYTHIC"])
    epics = len([b for b in brawlers if b.get("rarity") == "EPIC"])
    
    # Считаем гаджеты и звёздные силы
    total_gadgets = sum(len(b.get("gadgets", [])) for b in brawlers)
    total_star_powers = sum(len(b.get("starPowers", [])) for b in brawlers)
    
    # Средний уровень силы
    if total_brawlers > 0:
        avg_power = sum(b.get("power", 0) for b in brawlers) / total_brawlers
    else:
        avg_power = 0
    
    # Оценка
    score = 0
    
    if trophies >= 30000:
        score += 30
    elif trophies >= 20000:
        score += 20
    elif trophies >= 10000:
        score += 10
        
    if legendaries >= 5:
        score += 25
    elif legendaries >= 3:
        score += 15
    elif legendaries >= 1:
        score += 5
        
    if avg_power >= 9:
        score += 20
    elif avg_power >= 7:
        score += 10
        
    if total_gadgets + total_star_powers >= 50:
        score += 15
    elif total_gadgets + total_star_powers >= 20:
        score += 5
    
    # Вердикт
    if score >= 70:
        verdict = "🔥 **ТОПОВЫЙ АККАУНТ!** Бери не думая!"
        emoji = "💎🔥"
    elif score >= 50:
        verdict = "👍 **Хороший вариант** для старта или доната"
        emoji = "⭐️👍"
    elif score >= 30:
        verdict = "🤷 **Среднячок**. Смотри по цене, если дешево — бери"
        emoji = "🟡🤷"
    else:
        verdict = "💩 **Мусор**. Проходи мимо, даже за бесплатно"
        emoji = "🗑️💩"
    
    return {
        "trophies": trophies,
        "highest_trophies": highest_trophies,
        "exp_level": exp_level,
        "total_brawlers": total_brawlers,
        "legendaries": legendaries,
        "mythics": mythics,
        "epics": epics,
        "total_gadgets": total_gadgets,
        "total_star_powers": total_star_powers,
        "avg_power": round(avg_power, 1),
        "score": score,
        "verdict": verdict,
        "emoji": emoji
    }

# Форматирование сообщения для Telegram
def format_report(account_info):
    return f"""
{account_info['emoji']} **ОЦЕНКА АККАУНТА BRAWL STARS**

🏆 Трофеи: **{account_info['trophies']}** (рекорд: {account_info['highest_trophies']})
⭐️ Уровень опыта: {account_info['exp_level']}

🎲 **БОЙЦЫ:**
• Легендарные: {account_info['legendaries']} ⭐️
• Мифические: {account_info['mythics']} 🌙
• Эпические: {account_info['epics']} ✨
• Всего: {account_info['total_brawlers']}

🔧 **ПРОКАЧКА:**
• Средний уровень силы: {account_info['avg_power']}/11
• Гаджетов: {account_info['total_gadgets']} 💥
• Звёздных сил: {account_info['total_star_powers']} 🌟

📊 **РЕЙТИНГ:** {account_info['score']}/100

{account_info['verdict']}
"""

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Brawl Stars Account Tracker**\n\n"
        "Пришли тег игрока для оценки аккаунта.\n"
        "Пример: `/check 2PPQVUQ8J`\n"
        "Или просто отправь тег в чат.\n\n"
        "Тег можно найти в игре: профиль → под ником (начинается с #)"
    )

# Команда /check
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажи тег игрока!\nПример: `/check 2PPQVUQ8J`")
        return
    
    raw_tag = context.args[0]
    player_tag = clean_tag(raw_tag)
    
    if not player_tag:
        await update.message.reply_text("❌ Неправильный формат тега. Пример: `2PPQVUQ8J`")
        return
    
    await update.message.reply_text(f"🔍 Проверяю аккаунт `{raw_tag}`... Подожди немного.")
    
    await log_message(f"📊 Проверка аккаунта {raw_tag} от {update.effective_user.username}")
    
    # Получаем данные
    player_data = await get_player_info(player_tag)
    
    if "error" in player_data:
        error_msg = player_data["error"]
        await update.message.reply_text(
            f"❌ Не удалось найти аккаунт `{raw_tag}`.\n\n"
            f"Причина: {error_msg[:200]}\n\n"
            f"Проверь правильность тега.\n"
            f"Тег можно найти в игре: профиль → под ником (начинается с #)"
        )
        return
    
    # Анализируем
    account_info = evaluate_account(player_data)
    if not account_info:
        await update.message.reply_text(f"❌ Ошибка при анализе аккаунта `{raw_tag}`.")
        return
    
    report = format_report(account_info)
    await update.message.reply_text(report, parse_mode='Markdown')

# Если пользователь просто пишет тег в чат (без команды)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Проверяем, похоже на тег Brawl Stars (с решёткой или без)
    clean_text = text.replace('#', '').strip().upper()
    if len(clean_text) >= 5 and len(clean_text) <= 15 and clean_text.isalnum():
        # Подставляем в команду /check
        context.args = [text]
        await check(update, context)
    else:
        await update.message.reply_text(
            "Отправь тег игрока в формате `2PPQVUQ8J` или `#2PPQVUQ8J`\n"
            "Пример: `2PPQVUQ8J`\n\n"
            "Тег можно найти в игре: профиль → под ником"
        )

def main():
    print("=" * 50)
    print("🔥 Brawl Stars Tracker Bot запущен!")
    print("🤖 Бот готов к работе")
    print("=" * 50)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен, жду команды...")
    app.run_polling()

if __name__ == "__main__":
    main()
