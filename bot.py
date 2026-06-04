#!/usr/bin/env python3
# BFG Miner + Trader v4.0 - ИСПРАВЛЕННАЯ ВЕРСИЯ
# - Починен трейд (обработка None)
# - Шахта проверяет энергию после каждой копки
# - Правильный перехват сообщений от BFG

import asyncio
import time
import requests
import json
import os
import re
import random
from datetime import datetime
from telethon import TelegramClient, errors, events

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
# Telegram API (получить на my.telegram.org)
API_ID = 20045757                   # Твой API ID
API_HASH = '7d3ea0c0d4725498789bd51a9ee02421'     # Твой API Hash

# Кому и куда отправлять
BOT_USERNAME = 'bfgproject'            # Юзернейм бота BFG
YOUR_CHAT_ID = 6888643375           # Твой Telegram ID (узнать у @userinfobot)

# Настройки торговли
CHECK_INTERVAL = 60             # Проверять каждые 3 минуты
DROP_PERCENT = 0.3                  # Покупаем при падении на 0.5%
RISE_PERCENT = 0.3                  # Продаём при росте на 0.5%
MIN_PRICE = 58000                   # Ниже этой цены не покупаем
MAX_PRICE = 85000                   # Выше этой цены не продаём

# Настройки шахты
MINE_INTERVAL_MIN = 10 * 60         # Минимум 10 минут между заходами в шахту
MINE_INTERVAL_MAX = 20 * 60         # Максимум 20 минут

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

# Глобальная переменная для перехвата ответов от BFG
last_mine_response = ""

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
    """Полный цикл шахты: профиль → копка до 0 энергии → продажа"""
    global last_mine_response
    print("\n⛏️ ЗАХОДИМ В ШАХТУ, ЕБАТЬ!")
    
    # Сбрасываем переменную
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
        print("⚡ Нет энергии, идём дальше")
        return
    
    ore_command = get_ore_to_mine(level)
    print(f"⛏ Копаем: {ore_command}")
    
    # 2. Копаем, пока есть энергия
    max_attempts = energy + 5  # запас на случай, если энергия не обновилась
    last_energy = energy
    
    for i in range(max_attempts):
        # Отправляем команду на копку
        await client.send_message(BOT_USERNAME, ore_command)
        print(f"  Отправлена команда {i+1}")
        await asyncio.sleep(random.uniform(2.0, 3.0))
        
        # Проверяем остаток энергии
        last_mine_response = ""
        await client.send_message(BOT_USERNAME, "Моя шахта")
        await asyncio.sleep(2)
        
        new_profile = last_mine_response
        if new_profile:
            new_energy, new_level = parse_mine_profile(new_profile)
            print(f"  Остаток энергии: {new_energy}")
            
            # Если энергия не уменьшилась или стала 0 — выходим
            if new_energy <= 0:
                print("  ⚡ Энергия кончилась, заканчиваем копку")
                break
            if new_energy >= last_energy:
                print("  ⚡ Энергия не тратится, возможно лимит")
                break
            
            last_energy = new_energy
            energy = new_energy
        else:
            print("  ⚠️ Не удалось получить обновление энергии")
            break
        
        await asyncio.sleep(1.0)
    
    # 3. Продаём
    sell_command = ore_command.replace("копать", "продать")
    await client.send_message(BOT_USERNAME, sell_command)
    print(f"💰 Продано: {sell_command}")
    await asyncio.sleep(2)
    
    # 4. Собираем бонусы
    await client.send_message(BOT_USERNAME, "собрать бонусы")
    print("🎁 Бонусы собраны")
    
    await send_report(client, f"⛏️ Шахта отработана!\nУровень: {level}\nРуда: {ore_command.replace('копать ', '')}")

# ========== ОСНОВНАЯ ЛОГИКА (ТРЕЙД + ШАХТА) ==========
async def main_loop():
    global last_mine_response
    
    print("=" * 60)
    print("🚀 BFG MINER + TRADER v4.0 ЗАПУЩЕН, СУКА!")
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
    
    # Обработчик сообщений от BFG
    @client.on(events.NewMessage(chats=BOT_USERNAME))
    async def handler(event):
        global last_mine_response
        message_text = event.message.text
        if "профиль шахты" in message_text or "Энергия" in message_text:
            last_mine_response = message_text
            print("📥 Получен профиль шахты")
    
    # Загружаем состояния
    state = load_state()
    mine_state = load_mine_state()
    
    print(f"📁 Последняя сделка: {state['last_action']} по цене {state['last_price']}")
    
    # Отправляем приветствие
    await send_report(client, f"🤖 BFG Miner+Trader v4.0 запущен!\n📊 Трейд: ${MIN_PRICE:,.0f}-${MAX_PRICE:,.0f}, {DROP_PERCENT}%\n⛏️ Шахта: каждые {MINE_INTERVAL_MIN//60}-{MINE_INTERVAL_MAX//60} мин")
    
    last_mine_time = mine_state.get('last_mine_time', 0)
    
    while True:
        try:
            # ===== ТОРГОВАЯ ЛОГИКА (С ПРОВЕРКОЙ НА None) =====
            current_price = get_btc_price()
            
            # Проверка: если цена не получена — пропускаем цикл
            if current_price is None:
                print("❌ Не удалось получить цену BTC, жду следующий цикл...")
                await asyncio.sleep(60)
                continue
            
            # Дополнительная проверка: цена должна быть числом
            if not isinstance(current_price, (int, float)):
                print(f"⚠️ Цена не является числом: {current_price}")
                await asyncio.sleep(60)
                continue
            
            if MIN_PRICE <= current_price <= MAX_PRICE:
                last_price = state.get('last_price', current_price)
                
                # Если last_price почему-то None — исправляем
                if last_price is None:
                    last_price = current_price
                    print("📁 last_price отсутствовал, установлена текущая цена")
                
                buy_threshold = last_price * (1 - DROP_PERCENT / 100)
                sell_threshold = last_price * (1 + RISE_PERCENT / 100)
                
                print(f"📊 BTC: ${current_price:,.2f} | Купить < ${buy_threshold:,.2f} | Продать > ${sell_threshold:,.2f}")
                
                if current_price <= buy_threshold and state['last_action'] != 'buy':
                    print("🔻 ПОКУПАЮ...")
                    if await send_bfg_command(client, "Купить биткоин всё"):
                        await send_report(client, f"📉 КУПИЛ BTC по ${current_price:,.2f}")
                        state['last_action'] = 'buy'
                        state['last_price'] = current_price
                        save_state(state)
                        
                elif current_price >= sell_threshold and state['last_action'] != 'sell':
                    print("🟢 ПРОДАЮ...")
                    if await send_bfg_command(client, "Продать биткоин всё"):
                        await send_report(client, f"📈 ПРОДАЛ BTC по ${current_price:,.2f}")
                        state['last_action'] = 'sell'
                        state['last_price'] = current_price
                        save_state(state)
                else:
                    print("⚖️ Бездействие")
            else:
                print(f"⏸️ Цена ${current_price:,.2f} вне диапазона торговли")
            
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
