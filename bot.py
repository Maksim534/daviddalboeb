#!/usr/bin/env python3
# BFG Miner + Trader v3.0 - Ебашь трейд и шахту в одном флаконе, сука!

import asyncio
import time
import requests
import json
import os
import re
import random
from datetime import datetime
from telethon import TelegramClient, errors

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
# Telegram API (получить на my.telegram.org)
API_ID = 20045757                   # Твой API ID
API_HASH = '7d3ea0c0d4725498789bd51a9ee02421'     # Твой API Hash

# Кому и куда отправлять
BOT_USERNAME = 'bfgproject'            # Юзернейм бота BFG
YOUR_CHAT_ID = 6888643375           # Твой Telegram ID (узнать у @userinfobot)

# Настройки торговли
CHECK_INTERVAL = 60 * 3             # Проверять каждые 3 минуты
DROP_PERCENT = 0.5                  # Покупаем при падении на 2.5%
RISE_PERCENT = 0.5                  # Продаём при росте на 2.5%
MIN_PRICE = 58000                   # Ниже этой цены не покупаем
MAX_PRICE = 85000                   # Выше этой цены не продаём

# Настройки шахты
MINE_INTERVAL_MIN = 10 * 60         # Минимум 10 минут между заходами в шахту
MINE_INTERVAL_MAX = 20 * 60         # Максимум 20 минут
MINE_DELAY_BETWEEN_ACTIONS = 2.0    # Пауза между командами в шахте (сек)

# Файлы для сохранения состояния
STATE_FILE = "bfg_state.json"
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

# ========== ФУНКЦИИ ТРЕЙДА ==========
def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Ошибка получения цены: {e}")
        return None

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_action": None, "last_price": None, "last_action_time": None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def send_bfg_command(client, command):
    try:
        await client.send_message(BOT_USERNAME, command)
        print(f"📤 Отправлено: {command}")
        await asyncio.sleep(2)
        return True
    except errors.FloodWaitError as e:
        print(f"⚠️ Флуд-контроль: жди {e.seconds} секунд")
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
        print(f"❌ Не удалось отправить отчёт: {e}")

# ========== ФУНКЦИИ ШАХТЫ ==========
def parse_mine_profile(text):
    """Парсит сообщение 'Моя шахта'"""
    energy_match = re.search(r'⚡ Энергия:\s*(\d+)', text)
    level_match = re.search(r'⛏ Ваш уровень:\s*([^\n🌕💎]+)', text)
    
    energy = int(energy_match.group(1)) if energy_match else 0
    level = level_match.group(1).strip() if level_match else "Неизвестно"
    
    return energy, level

def get_ore_to_mine(level):
    """Возвращает команду для копки на основе уровня"""
    ore = LEVEL_ORES.get(level, "палладий")
    return f"копать {ore}"

def load_mine_state():
    if os.path.exists(MINE_STATE_FILE):
        with open(MINE_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_mine_time": 0}

def save_mine_state(state):
    with open(MINE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def mine_process(client):
    """Полный цикл шахты: профиль → копка → продажа"""
    print("\n⛏️ ЗАХОДИМ В ШАХТУ, ЕБАТЬ!")
    
    # Отправляем запрос профиля
    await client.send_message(BOT_USERNAME, "Моя шахта")
    await asyncio.sleep(3)
    
    # Здесь нужен перехват ответа через @client.on(events.NewMessage)
    # Это заглушка — в реальном коде ты получишь profile_text из события
    profile_text = await get_last_message_from_bfg(client)  # см. ниже
    
    if not profile_text:
        print("❌ Не удалось получить профиль шахты")
        return
    
    energy, level = parse_mine_profile(profile_text)
    print(f"📊 Энергия: {energy}, Уровень: {level}")
    
    if energy <= 0:
        print("⚡ Нет энергии, идём дальше")
        return
    
    ore_command = get_ore_to_mine(level)
    print(f"⛏ Копаем: {ore_command}")
    
    # Копаем, пока есть энергия
    for i in range(energy):
        await client.send_message(BOT_USERNAME, ore_command)
        print(f"  Скопал {i+1}/{energy}")
        await asyncio.sleep(random.uniform(1.5, 3.0))
    
    # Продаём
    sell_command = ore_command.replace("копать", "продать")
    await client.send_message(BOT_USERNAME, sell_command)
    print(f"💰 Продано: {sell_command}")
    
    # Собираем бонусы
    await client.send_message(BOT_USERNAME, "собрать бонусы")
    print("🎁 Бонусы собраны")
    
    await send_report(client, f"⛏️ Шахта отработана!\nУровень: {level}\nСкопано: {energy} раз(а)\nРуда: {ore_command.replace('копать ', '')}")

# Функция-заглушка для получения последнего сообщения от BFG
# В реальном боте ты должен использовать event handler
async def get_last_message_from_bfg(client):
    """Возвращает текст последнего сообщения от BFG (нужно реализовать через events)"""
    # Это временная заглушка. Правильная реализация требует @client.on(events.NewMessage)
    # Пока возвращаем тестовые данные
    return """
Игрок, это ваш профиль шахты:
🏆 Опыт: 520
⚡ Энергия: 15
⛏ Ваш уровень: Золото 🌕
"""

# ========== ОСНОВНАЯ ЛОГИКА (ТРЕЙД + ШАХТА) ==========
async def main_loop():
    print("=" * 60)
    print("🚀 BFG MINER + TRADER v3.0 ЗАПУЩЕН, СУКА!")
    print(f"📊 Интервал проверки цены: {CHECK_INTERVAL // 60} минут")
    print(f"📉 Покупка при падении на: {DROP_PERCENT}%")
    print(f"📈 Продажа при росте на: {RISE_PERCENT}%")
    print(f"🎯 Диапазон торговли: ${MIN_PRICE:,.0f} - ${MAX_PRICE:,.0f}")
    print(f"⛏️ Шахта: каждые {MINE_INTERVAL_MIN//60}-{MINE_INTERVAL_MAX//60} минут")
    print("=" * 60)
    
    # Подключаемся к Telegram
    client = TelegramClient('bfg_session', API_ID, API_HASH)
    await client.start()
    print("✅ Подключен к Telegram")
    
    # Загружаем состояния
    state = load_state()
    mine_state = load_mine_state()
    
    print(f"📁 Последняя сделка: {state['last_action']} по цене {state['last_price']}")
    
    # Отправляем приветствие
    await send_report(client, f"🤖 BFG Miner+Trader запущен!\n📊 Трейд: ${MIN_PRICE:,.0f}-${MAX_PRICE:,.0f}, {DROP_PERCENT}%\n⛏️ Шахта: каждые {MINE_INTERVAL_MIN//60}-{MINE_INTERVAL_MAX//60} мин")
    
    last_mine_time = mine_state.get('last_mine_time', 0)
    
    while True:
        try:
            # ===== ТОРГОВАЯ ЛОГИКА =====
            current_price = get_btc_price()
            if current_price is None:
                print("❌ Не удалось получить цену BTC, жду следующий цикл...")
                await asyncio.sleep(60)
                continue   # Пропускаем весь торговый цикл
            
            # Дополнительная страховка: если цена не число
            if not isinstance(current_price, (int, float)):
                print(f"⚠️ Цена не число: {current_price}, жду...")
                await asyncio.sleep(60)
                continue
            
            if MIN_PRICE <= current_price <= MAX_PRICE:
                last_price = state.get('last_price', current_price)
                # Страховка: если last_price вдруг None (например, сломался файл)
                if last_price is None:
                    last_price = current_price
                    print("📁 last_price отсутствовал, установлена текущая цена")
                
                buy_threshold = last_price * (1 - DROP_PERCENT / 100)
                sell_threshold = last_price * (1 + RISE_PERCENT / 100)
            
            # ===== ЛОГИКА ШАХТЫ =====
            now = time.time()
            if now - last_mine_time > random.randint(MINE_INTERVAL_MIN, MINE_INTERVAL_MAX):
                await mine_process(client)
                last_mine_time = now
                mine_state['last_mine_time'] = now
                save_mine_state(mine_state)
            
        except Exception as e:
            print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
            await send_report(client, f"⚠️ Ошибка: {str(e)[:100]}")
        
        await asyncio.sleep(CHECK_INTERVAL)

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен. Пока, сука!")
    except Exception as e:
        print(f"\n💀 Фатальная ошибка: {e}")
