#!/usr/bin/env python3
# BFG Miner + Trader v5.1 - ФИНАЛЬНАЯ ВЕРСИЯ
# - Курс из BFG с корректным умножением на 1000
# - Шахта с проверкой энергии
# - Сохранение состояния в JSON

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

# Настройки торговли
CHECK_INTERVAL = 60            # Проверять каждую минуту
DROP_PERCENT = 0.3             # Покупаем при падении на 0.3%
RISE_PERCENT = 0.3             # Продаём при росте на 0.3%
MIN_PRICE = 58000
MAX_PRICE = 85000

# Настройки шахты
MINE_INTERVAL_MIN = 10 * 60
MINE_INTERVAL_MAX = 20 * 60

# Файлы состояния
STATE_FILE = "bfg_state.json"
MINE_STATE_FILE = "mine_state.json"

# ========== СЛОВАРЬ РУД ==========
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

# Глобальные переменные для перехвата ответов BFG
last_mine_response = ""
last_price_response = ""

# ========== ФУНКЦИИ СОСТОЯНИЯ ==========
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_action": None, "last_price": None, "last_action_time": None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_mine_state():
    if os.path.exists(MINE_STATE_FILE):
        with open(MINE_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_mine_time": 0}

def save_mine_state(state):
    with open(MINE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ========== ПОЛУЧЕНИЕ КУРСА ИЗ BFG ==========
async def get_bfg_price(client):
    """Запрашивает курс биткоина у BFG и парсит цену"""
    global last_price_response
    
    last_price_response = ""
    await client.send_message(BOT_USERNAME, "биткоин курс")
    await asyncio.sleep(3)
    
    response = last_price_response
    if not response:
        print("❌ Не удалось получить ответ от BFG")
        return None
    
    # Парсим цену (пример: "курс 1 BTC составляет - 63.091$ 🌐")
    match = re.search(r'(\d+\.?\d*)\$', response)
    if match:
        # ВАЖНО: умножаем на 1000, потому что BFG показывает цену в тысячах
        price = float(match.group(1)) * 1000
        print(f"📊 Курс BFG: ${price:.2f}")
        return price
    else:
        print(f"❌ Не удалось распарсить цену: {response[:100]}")
        return None

# ========== ФУНКЦИИ ШАХТЫ ==========
def parse_mine_profile(text):
    energy_match = re.search(r'⚡ Энергия:\s*(\d+)', text)
    level_match = re.search(r'⛏ Ваш уровень:\s*([^\n🌕💎]+)', text)
    energy = int(energy_match.group(1)) if energy_match else 0
    level = level_match.group(1).strip() if level_match else "Неизвестно"
    return energy, level

def get_ore_to_mine(level):
    ore = LEVEL_ORES.get(level, "палладий")
    return f"копать {ore}"

async def mine_process(client):
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
    
    last_energy = energy
    for i in range(energy + 5):
        await client.send_message(BOT_USERNAME, ore_command)
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
    
    sell_command = ore_command.replace("копать", "продать")
    await client.send_message(BOT_USERNAME, sell_command)
    print(f"💰 Продано: {sell_command}")
    await asyncio.sleep(2)
    
    await client.send_message(BOT_USERNAME, "собрать бонусы")
    print("🎁 Бонусы собраны")
    
    await send_report(client, f"⛏️ Шахта отработана!\nУровень: {level}\nРуда: {ore_command.replace('копать ', '')}")

# ========== ОТПРАВКА КОМАНД ==========
async def send_bfg_command(client, command):
    try:
        await client.send_message(BOT_USERNAME, command)
        print(f"📤 Отправлено: {command}")
        await asyncio.sleep(2)
        return True
    except errors.FloodWaitError as e:
        print(f"⚠️ Флуд-контроль: жди {e.seconds} сек")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

async def send_report(client, message):
    try:
        await client.send_message(YOUR_CHAT_ID, message)
        print(f"📨 Отчёт отправлен")
    except Exception as e:
        print(f"❌ Ошибка отправки отчёта: {e}")

# ========== ОСНОВНОЙ ЦИКЛ ==========
async def main_loop():
    global last_mine_response, last_price_response
    
    print("=" * 60)
    print("🚀 BFG MINER + TRADER v5.1 (ФИНАЛ)")
    print(f"📊 Интервал: {CHECK_INTERVAL} сек")
    print(f"📉 Покупка при падении на: {DROP_PERCENT}%")
    print(f"📈 Продажа при росте на: {RISE_PERCENT}%")
    print(f"🎯 Диапазон: ${MIN_PRICE} - ${MAX_PRICE}")
    print("=" * 60)
    
    client = TelegramClient('bfg_session', API_ID, API_HASH)
    await client.start()
    print("✅ Подключен к Telegram")
    
    # Единый обработчик сообщений от BFG
    @client.on(events.NewMessage(chats=BOT_USERNAME))
    async def handler(event):
        global last_mine_response, last_price_response
        text = event.message.text
        if "профиль шахты" in text or "Энергия" in text:
            last_mine_response = text
            print("📥 Профиль шахты получен")
        if "курс 1 BTC составляет" in text:
            last_price_response = text
            print("📥 Курс BTC получен")
    
    state = load_state()
    mine_state = load_mine_state()
    
    print(f"📁 Состояние: {state}")
    
    await send_report(client, f"🤖 BFG Trader v5.1 запущен!\n📉 Падение: {DROP_PERCENT}%\n📈 Рост: {RISE_PERCENT}%")
    
    last_mine_time = mine_state.get('last_mine_time', 0)
    
    while True:
        try:
            # ===== ТОРГОВЛЯ ПО КУРСУ BFG =====
            current_price = await get_bfg_price(client)
            
            if current_price is None:
                print("❌ Нет курса, жду...")
                await asyncio.sleep(60)
                continue
            
            if MIN_PRICE <= current_price <= MAX_PRICE:
                last_price = state.get('last_price', current_price)
                
                if last_price is None:
                    last_price = current_price
                    print("📁 last_price отсутствовал, установлена текущая цена")
                    state['last_price'] = last_price
                    save_state(state)
                    print("💾 Состояние сохранено")
                
                buy_threshold = last_price * (1 - DROP_PERCENT / 100)
                sell_threshold = last_price * (1 + RISE_PERCENT / 100)
                
                print(f"📊 Текущая: ${current_price:.2f} | Купить < ${buy_threshold:.2f} | Продать > ${sell_threshold:.2f}")
                print(f"📈 Последняя сделка: {state['last_action']} по ${last_price:.2f}")
                
                if current_price <= buy_threshold and state['last_action'] != 'buy':
                    print("🔻 ПОКУПАЮ...")
                    if await send_bfg_command(client, "биткоин купить все"):
                        await send_report(client, f"📉 КУПЛЕНО по ${current_price:.2f}")
                        state['last_action'] = 'buy'
                        state['last_price'] = current_price
                        save_state(state)
                        
                elif current_price >= sell_threshold and state['last_action'] != 'sell':
                    print("🟢 ПРОДАЮ...")
                    if await send_bfg_command(client, "биткоин продать все"):
                        await send_report(client, f"📈 ПРОДАНО по ${current_price:.2f}")
                        state['last_action'] = 'sell'
                        state['last_price'] = current_price
                        save_state(state)
                else:
                    print("⚖️ Бездействие")
            else:
                print(f"⏸️ Цена ${current_price:.2f} вне диапазона {MIN_PRICE}-{MAX_PRICE}")
            
            # ===== ШАХТА =====
            now = time.time()
            if now - last_mine_time > random.randint(MINE_INTERVAL_MIN, MINE_INTERVAL_MAX):
                await mine_process(client)
                last_mine_time = now
                mine_state['last_mine_time'] = now
                save_mine_state(mine_state)
            
        except Exception as e:
            print(f"💥 ОШИБКА: {e}")
            await send_report(client, f"⚠️ Ошибка: {str(e)[:100]}")
        
        await asyncio.sleep(CHECK_INTERVAL)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n💀 Фатальная ошибка: {e}")
