#!/usr/bin/env python3
# BFG Miner + Farmer v8.1 - С ПРАВИЛЬНЫМ НАЖАТИЕМ КНОПОК

import asyncio
import time
import json
import os
import re
import random
from datetime import datetime
from telethon import TelegramClient, errors, events
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
API_ID = 20045757
API_HASH = '7d3ea0c0d4725498789bd51a9ee02421'
BOT_USERNAME = 'bfgproject'
YOUR_CHAT_ID = 6888643375

# Настройки шахты
MINE_INTERVAL_MIN = 10 * 60
MINE_INTERVAL_MAX = 20 * 60

# Настройки фермы
FARM_INTERVAL_NORMAL = 60 * 60      # 1 час
FARM_INTERVAL_EMPTY = 10 * 60       # 10 минут

# Файлы для сохранения состояния
MINE_STATE_FILE = "mine_state.json"
FARM_STATE_FILE = "farm_state.json"

# ========== СЛОВАРЬ УРОВНЕЙ И РУД ==========
LEVEL_ORES = {
    "Железо": "железо",
    "Золото": "золото",
    "Алмазы": "алмазы",
    "Аметисты": "аметисты",
    "Аквамарин": "аквамарин",
    "Изумруды": "изумруды",
    "Материя": "материя",
    "Плазма": "плазма",
    "Никель": "никель",
    "Титан": "титан",
    "Кобальт": "кобальт",
    "Эктоплазма": "эктоплазма",
    "Палладий": "палладий",
}

# Глобальные переменные
last_mine_response = ""
last_farm_response = ""
client = None

# ========== ФУНКЦИИ ОТПРАВКИ ==========
async def send_report(message):
    try:
        await client.send_message(YOUR_CHAT_ID, message)
        print(f"📨 Отчёт отправлен")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# ========== ФУНКЦИИ ШАХТЫ ==========
def parse_mine_profile(text):
    energy_match = re.search(r'⚡ Энергия:\s*(\d+)', text)
    level_match = re.search(r'⛏ Ваш уровень:\s*([^\n]+)', text)
    
    energy = int(energy_match.group(1)) if energy_match else 0
    level_raw = level_match.group(1).strip() if level_match else "Неизвестно"
    level = re.sub(r'[^\w\s]', '', level_raw).strip()
    
    return energy, level

def get_ore_to_mine(level):
    if level in LEVEL_ORES:
        return f"копать {LEVEL_ORES[level]}"
    for key, value in LEVEL_ORES.items():
        if key in level or level in key:
            return f"копать {value}"
    return "копать палладий"

def load_mine_state():
    if os.path.exists(MINE_STATE_FILE):
        with open(MINE_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_mine_time": 0}

def save_mine_state(state):
    with open(MINE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def mine_process():
    global last_mine_response
    print("\n⛏️ ЗАХОДИМ В ШАХТУ!")
    
    last_mine_response = ""
    await client.send_message(BOT_USERNAME, "Моя шахта")
    await asyncio.sleep(3)
    
    profile_text = last_mine_response
    if not profile_text:
        print("❌ Не удалось получить профиль шахты")
        return
    
    energy, level = parse_mine_profile(profile_text)
    print(f"📊 Энергия: {energy}, Уровень: {level}")
    
    if energy <= 0:
        print("⚡ Нет энергии")
        return
    
    ore_command = get_ore_to_mine(level)
    print(f"⛏ Копаем: {ore_command}")
    
    for i in range(energy):
        await client.send_message(BOT_USERNAME, ore_command)
        print(f"  Копка {i+1}/{energy}")
        await asyncio.sleep(random.uniform(2.0, 3.0))
    
    sell_command = ore_command.replace("копать", "продать")
    await client.send_message(BOT_USERNAME, sell_command)
    print(f"💰 Продажа: {sell_command}")
    await asyncio.sleep(3)
    
    sell_response = last_mine_response
    amount_match = re.search(r'продали\s+(\d+)\s+([а-я]+)\s+за\s+([\d\.]+)\$', sell_response, re.IGNORECASE)
    
    if amount_match:
        report = f"""⛏️ **Шахта отработала!**

📊 **Уровень:** {level}
⛏️ **Руда:** {amount_match.group(2)}
💰 **Продано:** {amount_match.group(1)} шт.
💵 **Сумма:** {amount_match.group(3)}$"""
    else:
        report = f"""⛏️ **Шахта отработала!**

📊 **Уровень:** {level}
⛏️ **Руда:** добыта
💰 **Продажа выполнена**"""
    
    await send_report(report)

# ========== ФУНКЦИИ ФЕРМЫ ==========
def load_farm_state():
    if os.path.exists(FARM_STATE_FILE):
        with open(FARM_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_farm_time": 0, "current_interval": 3600}

def save_farm_state(state):
    with open(FARM_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def farm_process():
    global last_farm_response
    print("\n🌾 ЗАХОДИМ В ФЕРМУ!")
    
    last_farm_response = ""
    
    await client.send_message(BOT_USERNAME, "Моя ферма")
    await asyncio.sleep(3)
    
    farm_text = last_farm_response
    if not farm_text:
        print("❌ Не удалось получить ответ от фермы")
        return False
    
    print(f"📥 Ответ: {farm_text[:200]}")
    
    tax_match = re.search(r'Налоги:\s*([\d\.]+)[^\d]*\/\s*([\d\.]+)[^\d]*', farm_text)
    if not tax_match:
        print("❌ Не удалось распарсить налоги")
        return False
    
    current_tax = float(tax_match.group(1).replace('.', ''))
    max_tax = float(tax_match.group(2).replace('.', ''))
    print(f"📊 Налоги: {current_tax:,.0f} / {max_tax:,.0f}")
    
    if current_tax == 0:
        print("🌾 Ферма пуста")
        await send_report("🌾 **Ферма пуста**\nСледующая проверка через 10 минут.")
        return False
    
    # Получаем последнее сообщение с кнопками
    async for msg in client.iter_messages(BOT_USERNAME, limit=1):
        last_msg = msg
        break
    
    if not last_msg or not last_msg.reply_markup:
        print("❌ Не найдены кнопки")
        return False
    
    # Нажимаем кнопки
    for row in last_msg.reply_markup.rows:
        for button in row.buttons:
            button_text = button.text
            print(f"🔘 Найдена кнопка: {button_text}")
            
            if "Оплатить" in button_text or "налог" in button_text.lower():
                print(f"💰 Нажимаю: {button_text}")
                try:
                    await client(GetBotCallbackAnswerRequest(
                        peer=BOT_USERNAME,
                        msg_id=last_msg.id,
                        data=button.data
                    ))
                    print("✅ Налоги оплачены")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
            
            elif "Собрать" in button_text or "прибыль" in button_text.lower():
                print(f"📦 Нажимаю: {button_text}")
                try:
                    await client(GetBotCallbackAnswerRequest(
                        peer=BOT_USERNAME,
                        msg_id=last_msg.id,
                        data=button.data
                    ))
                    print("✅ Прибыль собрана")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
    
    await send_report("🌾 **Ферма отработала!**\n💰 Налоги оплачены\n📦 Прибыль собрана")
    return True

# ========== ОСНОВНАЯ ЛОГИКА ==========
async def main_loop():
    global last_mine_response, last_farm_response, client
    
    print("=" * 60)
    print("🚀 BFG MINER + FARMER v8.1 ЗАПУЩЕН")
    print(f"⛏️ Шахта: каждые {MINE_INTERVAL_MIN//60}-{MINE_INTERVAL_MAX//60} минут")
    print(f"🌾 Ферма: каждый час (при пустоте — через 10 минут)")
    print("=" * 60)
    
    client = TelegramClient('bfg_session', API_ID, API_HASH)
    await client.start()
    print("✅ Подключен к Telegram")
    
    @client.on(events.NewMessage(chats=BOT_USERNAME))
    async def handler(event):
        global last_mine_response, last_farm_response
        text = event.message.text
        if "шахты" in text or "Энергия" in text or "продали" in text:
            last_mine_response = text
        if "Майнинг ферма" in text or "Налоги" in text:
            last_farm_response = text
            print("📥 Получен ответ от фермы")
    
    mine_state = load_mine_state()
    farm_state = load_farm_state()
    
    last_mine_time = mine_state.get('last_mine_time', 0)
    last_farm_time = farm_state.get('last_farm_time', 0)
    farm_interval = farm_state.get('current_interval', FARM_INTERVAL_NORMAL)
    
    await send_report("🤖 BFG Miner+Farmer v8.1 запущен!\n⛏️ Шахта: 10-20 мин\n🌾 Ферма: каждый час")
    
    while True:
        try:
            now = time.time()
            
            if now - last_mine_time > random.randint(MINE_INTERVAL_MIN, MINE_INTERVAL_MAX):
                await mine_process()
                last_mine_time = now
                save_mine_state({"last_mine_time": now})
            
            if now - last_farm_time > farm_interval:
                result = await farm_process()
                last_farm_time = now
                farm_interval = FARM_INTERVAL_EMPTY if result is False else FARM_INTERVAL_NORMAL
                save_farm_state({"last_farm_time": now, "current_interval": farm_interval})
            
        except Exception as e:
            print(f"💥 Ошибка: {e}")
            await send_report(f"⚠️ Ошибка: {str(e)[:100]}")
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
