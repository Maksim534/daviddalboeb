#!/usr/bin/env python3
# BFG Miner + Trader v7.1 - ПРАВИЛЬНАЯ КОМАНДА ПРОДАЖИ

import asyncio
import time
import json
import os
import re
import random
from datetime import datetime
from telethon import TelegramClient, errors, events

# ========== НАСТРОЙКИ ==========
API_ID = 20045757
API_HASH = '7d3ea0c0d4725498789bd51a9ee02421'
BOT_USERNAME = 'bfgproject'
YOUR_CHAT_ID = 6888643375

# Настройки торговли (микро-контроль)
CHECK_INTERVAL = 60          # каждую минуту
DROP_PERCENT = 0.0001           # 0.3% падение → покупка
RISE_PERCENT = 0.0001           # 0.3% рост → продажа
MIN_PRICE = 58000
MAX_PRICE = 85000

# Настройки шахты
MINE_INTERVAL_MIN = 10 * 60
MINE_INTERVAL_MAX = 20 * 60

STATE_FILE = "bfg_state.json"
MINE_STATE_FILE = "mine_state.json"

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

last_response = {"balance": "", "price": "", "mine": ""}

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

async def get_bfg_data(client, command, response_key):
    global last_response
    last_response[response_key] = ""
    await client.send_message(BOT_USERNAME, command)
    await asyncio.sleep(3)
    return last_response[response_key]

async def get_balance_and_price(client):
    # Баланс
    balance_text = await get_bfg_data(client, "б", "balance")
    balance_match = re.search(r'💰 Деньги:\s*([\d\.]+)', balance_text)
    if not balance_match:
        return None, None
    balance = float(balance_match.group(1).replace('.', ''))
    
    # Цена BTC
    price_text = await get_bfg_data(client, "биткоин курс", "price")
    price_match = re.search(r'(\d+\.?\d*)\$', price_text)
    if not price_match:
        return None, None
    price = float(price_match.group(1)) * 1000
    
    print(f"💰 Баланс: ${balance:,.0f} | 📊 Курс BFG: ${price:.2f}")
    return balance, price

async def buy_max_btc(client, balance, price):
    """Покупает максимальное целое количество BTC"""
    if price <= 0 or balance <= 0:
        return False
    
    max_btc = int(balance // price)   # целое число
    
    if max_btc <= 0:
        print("❌ Недостаточно средств даже на 1 BTC")
        return False
    
    command = f"биткоины купить {max_btc}"
    await client.send_message(BOT_USERNAME, command)
    print(f"📤 {command}")
    await asyncio.sleep(2)
    return True

async def sell_all_btc(client):
    """Продаёт все биткоины (правильная команда)"""
    command = "продать биткоины"
    await client.send_message(BOT_USERNAME, command)
    print(f"📤 {command}")
    await asyncio.sleep(2)
    return True

def parse_mine_profile(text):
    energy_match = re.search(r'⚡ Энергия:\s*(\d+)', text)
    level_match = re.search(r'⛏ Ваш уровень:\s*([^\n🌕💎]+)', text)
    energy = int(energy_match.group(1)) if energy_match else 0
    level = level_match.group(1).strip() if level_match else "Неизвестно"
    return energy, level

def get_ore_to_mine(level):
    return f"копать {LEVEL_ORES.get(level, 'палладий')}"

async def mine_process(client):
    global last_response
    print("\n⛏️ ЗАХОДИМ В ШАХТУ!")
    last_response["mine"] = ""
    await client.send_message(BOT_USERNAME, "Моя шахта")
    await asyncio.sleep(3)
    profile_text = last_response["mine"]
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
        last_response["mine"] = ""
        await client.send_message(BOT_USERNAME, "Моя шахта")
        await asyncio.sleep(2)
        new_profile = last_response["mine"]
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

async def send_report(client, message):
    try:
        await client.send_message(YOUR_CHAT_ID, message)
        print(f"📨 Отчёт отправлен")
    except Exception as e:
        print(f"❌ Ошибка отправки отчёта: {e}")

async def main_loop():
    global last_response
    
    print("=" * 60)
    print("🚀 BFG MINER + TRADER v7.1 (КОМАНДА: продать биткоины)")
    print(f"📊 Интервал: {CHECK_INTERVAL} сек")
    print(f"📉 Покупка при падении на: {DROP_PERCENT}%")
    print(f"📈 Продажа при росте на: {RISE_PERCENT}%")
    print("=" * 60)
    
    client = TelegramClient('bfg_session', API_ID, API_HASH)
    await client.start()
    print("✅ Подключен к Telegram")
    
    @client.on(events.NewMessage(chats=BOT_USERNAME))
    async def handler(event):
        global last_response
        text = event.message.text
        if "профиль шахты" in text or "Энергия" in text:
            last_response["mine"] = text
        if "курс 1 BTC составляет" in text:
            last_response["price"] = text
        if "👫 Ник: Игрок" in text:
            last_response["balance"] = text
    
    state = load_state()
    mine_state = load_mine_state()
    print(f"📁 Состояние: {state}")
    
    await send_report(client, f"🤖 BFG Trader v7.1 запущен!\n📉 Падение: {DROP_PERCENT}%\n📈 Рост: {RISE_PERCENT}%")
    
    last_mine_time = mine_state.get('last_mine_time', 0)
    
    while True:
        try:
            balance, current_price = await get_balance_and_price(client)
            if balance is None or current_price is None:
                await asyncio.sleep(60)
                continue
            
            if not (MIN_PRICE <= current_price <= MAX_PRICE):
                print(f"⏸️ Цена вне диапазона")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            
            last_price = state.get('last_price')
            if last_price is None:
                last_price = current_price
                state['last_price'] = last_price
                save_state(state)
                print(f"📁 Начальная цена: ${last_price:.2f}")
            
            buy_threshold = last_price * (1 - DROP_PERCENT / 100)
            sell_threshold = last_price * (1 + RISE_PERCENT / 100)
            
            print(f"📊 Текущая: ${current_price:.2f} | База: ${last_price:.2f}")
            print(f"📉 Купить если ≤ ${buy_threshold:.2f} | 📈 Продать если ≥ ${sell_threshold:.2f}")
            
            if current_price <= buy_threshold and state['last_action'] != 'buy':
                print("🔻 ПОКУПАЮ...")
                if await buy_max_btc(client, balance, current_price):
                    await send_report(client, f"📉 КУПЛЕНО по ${current_price:.2f}")
                    state['last_action'] = 'buy'
                    state['last_price'] = current_price
                    save_state(state)
            
            elif current_price >= sell_threshold and state['last_action'] != 'sell':
                print("🟢 ПРОДАЮ...")
                if await sell_all_btc(client):
                    await send_report(client, f"📈 ПРОДАНО по ${current_price:.2f}")
                    state['last_action'] = 'sell'
                    state['last_price'] = current_price
                    save_state(state)
            else:
                print("⚖️ Бездействие")
            
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

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n💀 Ошибка: {e}")
