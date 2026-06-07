#!/usr/bin/env python3
# BFG Miner v6.0 - ТОЛЬКО ШАХТА
# - Копает шахту, продаёт руду, присылает отчёты
# - БЕЗ ТОРГОВЛИ БИТКОИНАМИ

import asyncio
import time
import json
import os
import re
import random
from datetime import datetime
from telethon import TelegramClient, errors, events

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
API_ID = 20045757
API_HASH = '7d3ea0c0d4725498789bd51a9ee02421'
BOT_USERNAME = 'bfgproject'
YOUR_CHAT_ID = 6888643375

# Настройки шахты
MINE_INTERVAL_MIN = 10 * 60         # Минимум 10 минут между заходами в шахту
MINE_INTERVAL_MAX = 20 * 60         # Максимум 20 минут

# Файлы для сохранения состояния
MINE_STATE_FILE = "mine_state.json"

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

# Глобальная переменная для перехвата ответов BFG
last_mine_response = ""

# ========== ФУНКЦИИ ОТПРАВКИ ==========
async def send_report(message):
    try:
        await client.send_message(YOUR_CHAT_ID, message)
        print(f"📨 Отчёт отправлен")
    except Exception as e:
        print(f"❌ Ошибка отправки отчёта: {e}")

# ========== ФУНКЦИИ ШАХТЫ ==========
def parse_mine_profile(text):
    """Парсит сообщение 'Моя шахта' и очищает уровень от смайликов"""
    energy_match = re.search(r'⚡ Энергия:\s*(\d+)', text)
    level_match = re.search(r'⛏ Ваш уровень:\s*([^\n]+)', text)
    
    energy = int(energy_match.group(1)) if energy_match else 0
    level_raw = level_match.group(1).strip() if level_match else "Неизвестно"
    
    # Убираем смайлики и лишние символы
    level = re.sub(r'[^\w\s]', '', level_raw).strip()
    
    print(f"📊 Распознано: энергия={energy}, уровень={level}")
    return energy, level

def get_ore_to_mine(level):
    """Возвращает команду для копки на основе уровня"""
    if level in LEVEL_ORES:
        ore = LEVEL_ORES[level]
        print(f"⛏ Уровень {level} -> руда: {ore}")
        return f"копать {ore}"
    
    for key, value in LEVEL_ORES.items():
        if key in level or level in key:
            ore = value
            print(f"⛏ Уровень {level} (похож на {key}) -> руда: {ore}")
            return f"копать {ore}"
    
    print(f"⚠️ Неизвестный уровень: {level}, копаю палладий")
    return "копать палладий"

def load_mine_state():
    if os.path.exists(MINE_STATE_FILE):
        with open(MINE_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_mine_time": 0}

def save_mine_state(state):
    with open(MINE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def mine_process(client):
    """Полный цикл шахты: профиль → копка → продажа → отчёт"""
    global last_mine_response
    print("\n⛏️ ЗАХОДИМ В ШАХТУ!")
    
    last_mine_response = ""
    
    # 1. Получаем профиль
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
    ore_name = ore_command.replace("копать ", "")
    print(f"⛏ Копаем: {ore_command}")
    
    # 2. Копаем
    last_energy = energy
    mined_count = 0
    
    for i in range(energy + 5):
        await client.send_message(BOT_USERNAME, ore_command)
        mined_count += 1
        print(f"  Копка {i+1}")
        await asyncio.sleep(random.uniform(2.0, 3.0))
        
        last_mine_response = ""
        await client.send_message(BOT_USERNAME, "Моя шахта")
        await asyncio.sleep(2)
        
        new_profile = last_mine_response
        if new_profile:
            new_energy, _ = parse_mine_profile(new_profile)
            print(f"  Остаток энергии: {new_energy}")
            if new_energy <= 0 or new_energy >= last_energy:
                break
            last_energy = new_energy
        else:
            break
        await asyncio.sleep(1.0)
    
    # 3. Продаём
    last_mine_response = ""
    sell_command = ore_command.replace("копать", "продать")
    await client.send_message(BOT_USERNAME, sell_command)
    print(f"💰 Продажа: {sell_command}")
    await asyncio.sleep(3)
    
    # 4. Парсим сумму
    sell_response = last_mine_response
    amount_match = re.search(r'продали\s+(\d+[\d\s]*)\s+([а-я]+)\s+за\s+([\d\.]+)\$', sell_response, re.IGNORECASE)
    
    if amount_match:
        count = amount_match.group(1).strip()
        ore_type = amount_match.group(2).strip()
        total_price = amount_match.group(3).strip()
        
        report = f"""⛏️ **Шахта отработала!**

📊 **Уровень:** {level}
⛏️ **Руда:** {ore_type}
🔨 **Выкопано:** {mined_count} раз(а)

💰 **Продано:** {count} {ore_type}
💵 **Сумма:** {total_price}$

🎉 Твой заработок за этот заход!"""
    else:
        report = f"""⛏️ **Шахта отработала!**

📊 **Уровень:** {level}
⛏️ **Руда:** {ore_name}
🔨 **Выкопано:** {mined_count} раз(а)

💰 **Продажа выполнена**
📝 Проверь баланс в игре"""
    
    await send_report(report)

# ========== ОСНОВНАЯ ЛОГИКА ==========
async def main_loop():
    global last_mine_response, client
    
    print("=" * 60)
    print("🚀 BFG MINER v6.0 ЗАПУЩЕН (ТОЛЬКО ШАХТА)")
    print(f"⛏️ Шахта: каждые {MINE_INTERVAL_MIN//60}-{MINE_INTERVAL_MAX//60} минут")
    print("=" * 60)
    
    global client
    client = TelegramClient('bfg_session', API_ID, API_HASH)
    await client.start()
    print("✅ Подключен к Telegram")
    
    @client.on(events.NewMessage(chats=BOT_USERNAME))
    async def handler(event):
        global last_mine_response
        text = event.message.text
        if "профиль шахты" in text or "Энергия" in text or "продали" in text:
            last_mine_response = text
            print("📥 Получен ответ от шахты")
    
    mine_state = load_mine_state()
    last_mine_time = mine_state.get('last_mine_time', 0)
    
    await send_report("🤖 BFG Miner v1.0 запущен! Буду копать шахту каждые 10-20 минут.")
    
    while True:
        try:
            now = time.time()
            if now - last_mine_time > random.randint(MINE_INTERVAL_MIN, MINE_INTERVAL_MAX):
                await mine_process(client)
                last_mine_time = now
                mine_state['last_mine_time'] = now
                save_mine_state(mine_state)
            
        except Exception as e:
            print(f"💥 ОШИБКА: {e}")
            await send_report(f"⚠️ Ошибка: {str(e)[:100]}")
        
        await asyncio.sleep(60)

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n💀 Фатальная ошибка: {e}")
