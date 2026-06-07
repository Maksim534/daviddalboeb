#!/usr/bin/env python3
# BFG Miner + Trader v5.3 - ИСПРАВЛЕННАЯ ВЕРСИЯ
# - Починен трейд (обработка None)
# - Шахта проверяет энергию после каждой копки
# - Правильный перехват сообщений от BFG
# - ИСПРАВЛЕНО: определение уровня со смайликами
# - Парсинг суммы продажи шахты
# - Ручные команды .buy и .sell

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
CHECK_INTERVAL = 60            # Проверять каждую минуту
DROP_PERCENT = 0.1             # Покупаем при падении на 0.1%
RISE_PERCENT = 0.1             # Продаём при росте на 0.1%
MIN_PRICE = 58000              # Ниже этой цены не покупаем
MAX_PRICE = 85000              # Выше этой цены не продаём

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

# Глобальные переменные для перехвата ответов BFG
last_mine_response = ""
last_price_response = ""

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

# ========== ФУНКЦИИ ШАХТЫ (ИСПРАВЛЕННЫЕ) ==========
def parse_mine_profile(text):
    """Парсит сообщение 'Моя шахта' и очищает уровень от смайликов"""
    energy_match = re.search(r'⚡ Энергия:\s*(\d+)', text)
    level_match = re.search(r'⛏ Ваш уровень:\s*([^\n]+)', text)
    
    energy = int(energy_match.group(1)) if energy_match else 0
    level_raw = level_match.group(1).strip() if level_match else "Неизвестно"
    
    # Убираем смайлики и лишние символы (оставляем только буквы)
    level = re.sub(r'[^\w\s]', '', level_raw).strip()
    
    print(f"📊 Распознано: энергия={energy}, уровень={level}")
    return energy, level

def get_ore_to_mine(level):
    """Возвращает команду для копки на основе уровня"""
    # Пробуем найти точное совпадение
    if level in LEVEL_ORES:
        ore = LEVEL_ORES[level]
        print(f"⛏ Уровень {level} -> руда: {ore}")
        return f"копать {ore}"
    
    # Если не нашли, пробуем найти частичное совпадение
    for key, value in LEVEL_ORES.items():
        if key in level or level in key:
            ore = value
            print(f"⛏ Уровень {level} (похож на {key}) -> руда: {ore}")
            return f"копать {ore}"
    
    # Если ничего не подошло — палладий (но это не должно случиться)
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
    """Полный цикл шахты: профиль → копка до 0 энергии → продажа → отчёт"""
    global last_mine_response
    print("\n⛏️ ЗАХОДИМ В ШАХТУ!")
    
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
        print("⚡ Нет энергии")
        return
    
    ore_command = get_ore_to_mine(level)
    ore_name = ore_command.replace("копать ", "")
    print(f"⛏ Копаем: {ore_command}")
    
    # 2. Копаем, пока есть энергия
    last_energy = energy
    mined_count = 0
    
    for i in range(energy + 5):
        await client.send_message(BOT_USERNAME, ore_command)
        mined_count += 1
        print(f"  Копка {i+1}")
        await asyncio.sleep(random.uniform(2.0, 3.0))
        
        # Проверяем остаток энергии
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
    
    # 3. Продаём и перехватываем ответ
    last_mine_response = ""
    sell_command = ore_command.replace("копать", "продать")
    await client.send_message(BOT_USERNAME, sell_command)
    print(f"💰 Продажа: {sell_command}")
    await asyncio.sleep(3)
    
    # Парсим ответ о продаже
    sell_response = last_mine_response
    print(f"📥 Ответ BFG: {sell_response[:200]}")
    
    # Ищем количество и сумму
    amount_match = re.search(r'продали\s+(\d+[\d\s]*)\s+([а-я]+)\s+за\s+([\d\.]+)\$', sell_response, re.IGNORECASE)
    
    if amount_match:
        count = amount_match.group(1).strip()
        ore_type = amount_match.group(2).strip()
        total_price = amount_match.group(3).strip()
        
        print(f"✅ Распознано: {count} {ore_type} за {total_price}$")
        
        report = f"""⛏️ **Шахта отработана!**

📊 **Уровень:** {level}
⛏️ **Руда:** {ore_type}
🔨 **Вскопано:** {mined_count} раз(а)

💰 **Продано:** {count} {ore_type}
💵 **Сумма:** {total_price}$

🎉 Твой заработок за этот заход!"""
        
    else:
        # Если не распознали сумму
        report = f"""⛏️ **Шахта отработана!**

📊 **Уровень:** {level}
⛏️ **Руда:** {ore_name}
🔨 **Вскопано:** {mined_count} раз(а)

💰 **Продажа выполнена**
📝 Проверь баланс в игре"""
    
    # Бонусы НЕ собираем
    
    # Отправляем отчёт
    await send_report(client, report)

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

# ========== РУЧНЫЕ КОМАНДЫ ДЛЯ ЮЗЕРБОТА ==========
async def buy_all_command(event):
    """Покупает всё доступное количество BTC"""
    try:
        await event.reply("💰 Покупаю биткоины...")
        
        current_price = await get_bfg_price(event.client)
        if not current_price:
            await event.reply("❌ Не удалось получить курс")
            return
        
        await send_bfg_command(event.client, "Купить биткоин всё")
        
        state = load_state()
        state['last_action'] = 'buy'
        state['last_price'] = current_price
        state['last_action_time'] = datetime.now().isoformat()
        save_state(state)
        
        await send_report(event.client, f"📈 КУПЛЕНО BTC по ${current_price:,.2f}")
        await event.reply(f"✅ Куплено BTC по курсу ${current_price:,.2f}")
    except Exception as e:
        await event.reply(f"❌ Ошибка: {e}")

async def sell_all_command(event):
    """Продаёт всё доступное количество BTC"""
    try:
        await event.reply("💰 Продаю биткоины...")
        
        current_price = await get_bfg_price(event.client)
        if not current_price:
            await event.reply("❌ Не удалось получить курс")
            return
        
        await send_bfg_command(event.client, "Продать биткоин всё")
        
        state = load_state()
        last_buy_price = state.get('last_price')
        
        state['last_action'] = 'sell'
        state['last_price'] = current_price
        state['last_action_time'] = datetime.now().isoformat()
        save_state(state)
        
        if last_buy_price:
            profit = current_price - last_buy_price
            profit_percent = (profit / last_buy_price) * 100
            await send_report(event.client, 
                f"📉 ПРОДАНО BTC по ${current_price:,.2f}\n"
                f"📊 Куплено было по ${last_buy_price:,.2f}\n"
                f"💰 Прибыль: ${profit:,.2f} ({profit_percent:+.2f}%)")
            await event.reply(f"✅ Продано BTC по ${current_price:,.2f}\n💰 Прибыль: ${profit:,.2f}")
        else:
            await send_report(event.client, f"📉 ПРОДАНО BTC по ${current_price:,.2f}")
            await event.reply(f"✅ Продано BTC по курсу ${current_price:,.2f}")
    except Exception as e:
        await event.reply(f"❌ Ошибка: {e}")

# ========== ОСНОВНАЯ ЛОГИКА (ТРЕЙД + ШАХТА) ==========
async def main_loop():
    global last_mine_response, last_price_response
    
    print("=" * 60)
    print("🚀 BFG MINER + TRADER v5.3 ЗАПУЩЕН, СУКА!")
    print(f"📊 Интервал проверки цены: {CHECK_INTERVAL} секунд")
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
        global last_mine_response, last_price_response
        text = event.message.text
        
        if "профиль шахты" in text or "Энергия" in text:
            last_mine_response = text
            print("📥 Получен профиль шахты")
        
        if "продали" in text and "за" in text:
            last_mine_response = text
            print("📥 Получен ответ о продаже")
        
        if "курс 1 BTC составляет" in text:
            last_price_response = text
            print("📥 Получен курс BTC от BFG")
    
    # Загружаем состояния
    state = load_state()
    mine_state = load_mine_state()
    
    print(f"📁 Последняя сделка: {state['last_action']} по цене {state['last_price']}")
    
    # Отправляем приветствие
    await send_report(client, f"🤖 BFG Miner+Trader v5.3 запущен!\n📊 Трейд: ${MIN_PRICE:,.0f}-${MAX_PRICE:,.0f}, {DROP_PERCENT}%\n⛏️ Шахта: каждые {MINE_INTERVAL_MIN//60}-{MINE_INTERVAL_MAX//60} мин")
    
    last_mine_time = mine_state.get('last_mine_time', 0)
    
    while True:
        try:
            # ===== ТОРГОВАЯ ЛОГИКА =====
            current_price = await get_bfg_price(client)
            
            if current_price is None:
                print("❌ Не удалось получить цену BTC, жду следующий цикл...")
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
                
                print(f"📊 BTC: ${current_price:,.2f} | Купить < ${buy_threshold:,.2f} | Продать > ${sell_threshold:,.2f}")
                print(f"📈 Последняя сделка: {state['last_action']} по ${last_price:,.2f}")
                
                if current_price <= buy_threshold and state['last_action'] != 'buy':
                    print("🔻 ПОКУПАЮ...")
                    if await send_bfg_command(client, "Купить биткоин всё"):
                        report = f"""📉 **СОВЕРШЕНА ПОКУПКА BTC**

💰 Цена покупки: ${current_price:,.2f}
📊 Предыдущая цена: ${last_price:,.2f}
📉 Падение: {((last_price - current_price) / last_price * 100):.2f}%
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 Для продажи используй команду: Продать биткоин всё"""
                        await send_report(client, report)
                        state['last_action'] = 'buy'
                        state['last_price'] = current_price
                        save_state(state)
                        
                elif current_price >= sell_threshold and state['last_action'] != 'sell':
                    print("🟢 ПРОДАЮ...")
                    if await send_bfg_command(client, "Продать биткоин всё"):
                        buy_price = state.get('last_price', current_price)
                        profit = current_price - buy_price
                        profit_percent = (profit / buy_price) * 100 if buy_price else 0
                        
                        report = f"""📈 **СОВЕРШЕНА ПРОДАЖА BTC**

💰 Цена продажи: ${current_price:,.2f}
📊 Цена покупки: ${buy_price:,.2f}
💰 Прибыль: ${profit:,.2f} ({profit_percent:+.2f}%)
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 Для новой покупки бот будет ждать падения цены"""
                        await send_report(client, report)
                        state['last_action'] = 'sell'
                        state['last_price'] = current_price
                        save_state(state)
                else:
                    print("⚖️ Бездействие")
            else:
                print(f"⏸️ Цена ${current_price:,.2f} вне диапазона {MIN_PRICE}-{MAX_PRICE}")
            
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
