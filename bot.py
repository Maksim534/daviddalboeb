#!/usr/bin/env python3
# BFG Miner + Farmer + Gardener v10.0 - С КОПКОЙ МАТЕРИИ ДО 2000
# - Шахта: копает материю до 2000, показывает прогресс
# - Ферма: собирает прибыль, оплачивает налоги
# - Сад: поливает, собирает прибыль, оплачивает налоги

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
YOUR_CHAT_ID = 8564427714

# Настройки шахты (материя)
TARGET_MATERIA = 2000               # Цель по материи

# Настройки фермы и сада
FARM_INTERVAL_NORMAL = 60 * 60      # 1 час
FARM_INTERVAL_EMPTY = 10 * 60       # 10 минут
GARDEN_INTERVAL_NORMAL = 60 * 60    # 1 час
GARDEN_INTERVAL_EMPTY = 10 * 60     # 10 минут

# Файлы для сохранения состояния
MINE_STATE_FILE = "mine_state.json"
FARM_STATE_FILE = "farm_state.json"
GARDEN_STATE_FILE = "garden_state.json"

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
last_garden_response = ""
last_inventory_response = ""
client = None

# ========== ФУНКЦИИ ОТПРАВКИ ==========
async def send_report(message):
    try:
        await client.send_message(YOUR_CHAT_ID, message)
        print(f"📨 Отчёт отправлен")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# ========== НАЖАТИЕ КНОПОК ==========
async def press_button_by_text(button_text: str):
    """Находит кнопку с нужным текстом и нажимает её"""
    try:
        async for msg in client.iter_messages(BOT_USERNAME, limit=1):
            last_msg = msg
            break
        
        if not last_msg or not last_msg.reply_markup:
            print(f"❌ Не найдены кнопки для '{button_text}'")
            return False
        
        for row in last_msg.reply_markup.rows:
            for button in row.buttons:
                if button_text.lower() in button.text.lower():
                    print(f"🔘 Нажимаю кнопку: {button.text}")
                    await client(GetBotCallbackAnswerRequest(
                        peer=BOT_USERNAME,
                        msg_id=last_msg.id,
                        data=button.data
                    ))
                    return True
        
        print(f"❌ Кнопка '{button_text}' не найдена")
        return False
    except Exception as e:
        print(f"❌ Ошибка нажатия кнопки {button_text}: {e}")
        return False

# ========== ФУНКЦИИ ШАХТЫ (КОПКА МАТЕРИИ ДО 2000) ==========
def parse_mine_profile(text):
    energy_match = re.search(r'⚡ Энергия:\s*(\d+)', text)
    level_match = re.search(r'⛏ Ваш уровень:\s*([^\n]+)', text)
    
    energy = int(energy_match.group(1)) if energy_match else 0
    level_raw = level_match.group(1).strip() if level_match else "Неизвестно"
    level = re.sub(r'[^\w\s]', '', level_raw).strip()
    
    return energy, level

def load_mine_state():
    if os.path.exists(MINE_STATE_FILE):
        with open(MINE_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_mine_time": 0}

def save_mine_state(state):
    with open(MINE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def get_materia_count():
    """Проверяет количество материи в инвентаре"""
    global last_inventory_response
    
    last_inventory_response = ""
    await client.send_message(BOT_USERNAME, "инвентарь")
    await asyncio.sleep(3)
    
    inv_text = last_inventory_response
    if not inv_text:
        print("❌ Не удалось получить инвентарь")
        return None
    
    materia_match = re.search(r'🌌\s*Материя:\s*([\d\.,]+)\s*шт', inv_text)
    if materia_match:
        count_str = materia_match.group(1).replace('.', '').replace(',', '')
        return int(count_str)
    return 0

async def mine_process():
    """Копает материю до 2000, показывает прогресс"""
    global last_mine_response, last_inventory_response
    print("\n⛏️ ЗАХОДИМ В ШАХТУ!")
    
    # Проверяем текущее количество материи
    current = await get_materia_count()
    if current is None:
        print("❌ Не удалось проверить инвентарь")
        return
    
    print(f"📊 Текущий баланс: {current} / {TARGET_MATERIA} материи")
    
    if current >= TARGET_MATERIA:
        await send_report(f"🌌 **Цель достигнута!**\n📊 {current} / {TARGET_MATERIA} материи\n🎉 Фарм завершён!")
        return
    
    # Получаем профиль шахты (для энергии)
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
    
    # Копаем материю (родительный падеж!)
    ore_command = "копать материю"
    print(f"⛏ Копаем: {ore_command}")
    
    for i in range(energy):
        await client.send_message(BOT_USERNAME, ore_command)
        print(f"  Копка {i+1}/{energy}")
        await asyncio.sleep(random.uniform(2.0, 3.0))
        
        # Проверяем новый баланс
        new_count = await get_materia_count()
        if new_count is None:
            break
        
        percent = (new_count / TARGET_MATERIA) * 100
        progress_bar = '█' * int(percent//5) + '░' * (20 - int(percent//5))
        
        await send_report(f"🌌 **Фарм материи:**\n📊 {new_count} / {TARGET_MATERIA} ({percent:.1f}%)\n{progress_bar}")
        
        if new_count >= TARGET_MATERIA:
            print(f"🎉 Цель достигнута! {new_count}/{TARGET_MATERIA}")
            await send_report(f"🌌 **ГОТОВО!**\n📊 Накопано {new_count} материи из {TARGET_MATERIA}")
            return
        
        if new_count == current:
            print("⚡ Энергия кончилась или материя не копается")
            break
        
        current = new_count
    
    print(f"🌌 Фарм завершён. Итог: {current}/{TARGET_MATERIA}")

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
    
    if current_tax > 0:
        print(f"💰 Оплачиваю налоги: {current_tax:,.0f}")
        await press_button_by_text("Оплатить налоги")
        await asyncio.sleep(2)
    
    print("📦 Собираю прибыль...")
    await press_button_by_text("Собрать прибыль")
    await asyncio.sleep(2)
    
    await send_report("🌾 **Ферма отработала!**\n💰 Налоги оплачены\n📦 Прибыль собрана")
    return True

# ========== ФУНКЦИИ САДА ==========
def load_garden_state():
    if os.path.exists(GARDEN_STATE_FILE):
        with open(GARDEN_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_garden_time": 0, "current_interval": 3600}

def save_garden_state(state):
    with open(GARDEN_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def garden_process():
    global last_garden_response
    print("\n🌳 ЗАХОДИМ В САД!")
    
    last_garden_response = ""
    await client.send_message(BOT_USERNAME, "мои сад")
    await asyncio.sleep(3)
    
    garden_text = last_garden_response
    if not garden_text:
        print("❌ Не удалось получить ответ от сада")
        return False
    
    tax_match = re.search(r'Налоги:\s*([\d\.]+)[^\d]*\/\s*([\d\.]+)[^\d]*', garden_text)
    water_match = re.search(r'Воды:\s*(\d+)\/\s*(\d+)', garden_text)
    
    if not tax_match:
        print("❌ Не удалось распарсить налоги сада")
        return False
    
    current_tax = float(tax_match.group(1).replace('.', ''))
    max_tax = float(tax_match.group(2).replace('.', ''))
    water_current = int(water_match.group(1)) if water_match else 0
    
    print(f"📊 Налоги: {current_tax:,.0f} / {max_tax:,.0f}")
    print(f"💧 Вода: {water_current}")
    
    if current_tax > 0:
        print(f"💰 Оплачиваю налоги: {current_tax:,.0f}")
        await press_button_by_text("Оплатить налоги")
        await asyncio.sleep(2)
    
    if water_current < 100:
        print(f"💧 Поливаю сад...")
        await press_button_by_text("Полить сад")
        await asyncio.sleep(2)
    
    print("📦 Собираю прибыль...")
    await press_button_by_text("Собрать прибыль")
    await asyncio.sleep(2)
    
    if "0 шт./10 шт." in garden_text or "деревьев: 0" in garden_text:
        print("🌳 Сад пуст (нет деревьев)")
        await send_report("🌳 **Сад пуст!**\nКупи деревья командой `купить дерево`")
        return False
    
    await send_report("🌳 **Сад обработан!**\n💰 Налоги оплачены\n💧 Сад полит\n📦 Прибыль собрана")
    return True

# ========== ОСНОВНАЯ ЛОГИКА ==========
async def main_loop():
    global last_mine_response, last_farm_response, last_garden_response, last_inventory_response, client
    
    print("=" * 60)
    print("🚀 BFG MINER + FARMER + GARDENER v10.0 ЗАПУЩЕН")
    print(f"🌌 Шахта: копка материи до {TARGET_MATERIA}")
    print(f"🌾 Ферма: каждый час (при пустоте — через 10 минут)")
    print(f"🌳 Сад: каждый час (при пустоте — через 10 минут)")
    print("=" * 60)
    
    client = TelegramClient('bfg_session', API_ID, API_HASH)
    await client.start()
    print("✅ Подключен к Telegram")
    
    @client.on(events.NewMessage(chats=BOT_USERNAME))
    async def handler(event):
        global last_mine_response, last_farm_response, last_garden_response, last_inventory_response
        text = event.message.text
        
        if "шахты" in text or "Энергия" in text:
            last_mine_response = text
        
        if "Майнинг ферма" in text or "Налоги" in text:
            last_farm_response = text
            print("📥 Получен ответ от фермы")
        
        if "Сад" in text or "Воды" in text or "Деревья" in text:
            last_garden_response = text
            print("📥 Получен ответ от сада")
        
        if "инвентарь" in text or "Материя" in text:
            last_inventory_response = text
            print("📥 Получен инвентарь")
    
    # Загружаем состояния
    mine_state = load_mine_state()
    farm_state = load_farm_state()
    garden_state = load_garden_state()
    
    last_mine_time = mine_state.get('last_mine_time', 0)
    last_farm_time = farm_state.get('last_farm_time', 0)
    last_garden_time = garden_state.get('last_garden_time', 0)
    
    farm_interval = farm_state.get('current_interval', FARM_INTERVAL_NORMAL)
    garden_interval = garden_state.get('current_interval', GARDEN_INTERVAL_NORMAL)
    
    await send_report(f"🤖 BFG Bot v10.0 запущен!\n🌌 Фарм материи до {TARGET_MATERIA}\n🌾 Ферма: каждый час\n🌳 Сад: каждый час")
    
    while True:
        try:
            now = time.time()
            
            # Шахта (материя) — раз в 10-20 минут
            if now - last_mine_time > random.randint(600, 1200):
                await mine_process()
                last_mine_time = now
                save_mine_state({"last_mine_time": now})
            
            # Ферма
            if now - last_farm_time > farm_interval:
                result = await farm_process()
                last_farm_time = now
                farm_interval = FARM_INTERVAL_EMPTY if result is False else FARM_INTERVAL_NORMAL
                save_farm_state({"last_farm_time": now, "current_interval": farm_interval})
            
            # Сад
            if now - last_garden_time > garden_interval:
                result = await garden_process()
                last_garden_time = now
                garden_interval = GARDEN_INTERVAL_EMPTY if result is False else GARDEN_INTERVAL_NORMAL
                save_garden_state({"last_garden_time": now, "current_interval": garden_interval})
            
        except Exception as e:
            print(f"💥 Ошибка: {e}")
            await send_report(f"⚠️ Ошибка: {str(e)[:100]}")
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
