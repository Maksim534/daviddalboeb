#!/usr/bin/env python3
# BTC Монитор - просто кидает уведомления, когда биток резко движется

import asyncio
import requests
from telegram import Bot

# ========== НАСТРОЙКИ ==========
# Токен бота (получить у @BotFather)
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"  # твой токен

# Твой Telegram ID (узнать у @userinfobot)
CHAT_ID = "8564427714"  # твой ID

# Чувствительность (процент изменения для уведомления)
PROCESSOR = 3.5  # 3.5% - если меняется на столько - кидаем оповещение

# Как часто проверяем (в секундах)
CHECK_INTERVAL = 60  # каждую минуту

# ========== КОД (ничего не трогать) ==========
bot = Bot(token=BOT_TOKEN)

def get_btc():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    data = requests.get(url).json()
    return float(data['price'])

async def send_alert(price, old_price, percent):
    direction = "📈 ВЗЛЕТЕЛ" if percent > 0 else "📉 ЕБНУЛСЯ"
    emoji = "🚀" if percent > 0 else "💀"
    msg = f"""{emoji} {direction} НАХУЙ!

💰 Было: ${old_price:,.0f}
💰 Стало: ${price:,.0f}
📊 Изменение: {percent:+.2f}%

⏰ {__import__('datetime').datetime.now().strftime('%H:%M:%S')}"""
    await bot.send_message(chat_id=CHAT_ID, text=msg)

async def main():
    print("🚀 BTC Монитор запущен, сука!")
    print(f"📊 Чувствительность: {PROCESSOR}%")
    print(f"⏱️  Проверка каждые {CHECK_INTERVAL} сек")
    
    old = get_btc()
    print(f"💰 Текущая цена: ${old:,.0f}")
    await bot.send_message(chat_id=CHAT_ID, text=f"✅ BTC Монитор запущен!\n💰 Цена: ${old:,.0f}\n📊 Оповещение при изменении > {PROCESSOR}%")
    
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            new = get_btc()
            percent = (new - old) / old * 100
            
            if abs(percent) >= PROCESSOR:
                await send_alert(new, old, percent)
                old = new
            else:
                print(f"Цена: ${new:,.0f} ({percent:+.2f}%) - херня")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())        return price
    except Exception as e:
        print(f"❌ Ошибка получения цены: {e}")
        return None

# ========== РАБОТА С ФАЙЛОМ СОСТОЯНИЯ ==========
def load_state():
    """Загружает сохранённую цену последней сделки"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_action": None, "last_price": None, "last_action_time": None}

def save_state(state):
    """Сохраняет состояние"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ========== ОТПРАВКА КОМАНД В BFG ==========
async def send_bfg_command(client, command):
    """Отправляет команду боту BFG"""
    try:
        await client.send_message(BOT_USERNAME, command)
        print(f"📤 Отправлено: {command}")
        await asyncio.sleep(2)  # Пауза, чтобы бот успел ответить
        return True
    except errors.FloodWaitError as e:
        print(f"⚠️ Флуд-контроль: жди {e.seconds} секунд")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

# ========== ОТПРАВКА ОТЧЁТОВ ТЕБЕ ==========
async def send_report(client, message):
    """Отправляет отчёт в твою личку"""
    try:
        await client.send_message(YOUR_CHAT_ID, message)
        print(f"📨 Отчёт отправлен")
    except Exception as e:
        print(f"❌ Не удалось отправить отчёт: {e}")

# ========== ОСНОВНАЯ ЛОГИКА ТОРГОВЛИ ==========
async def main_loop():
    print("=" * 50)
    print("🚀 BFG AUTO TRADER v2.0 ЗАПУЩЕН, СУКА!")
    print(f"📊 Интервал проверки: {CHECK_INTERVAL // 60} минут")
    print(f"📉 Покупка при падении на: {DROP_PERCENT}%")
    print(f"📈 Продажа при росте на: {RISE_PERCENT}%")
    print(f"🎯 Диапазон торговли: ${MIN_PRICE:,.0f} - ${MAX_PRICE:,.0f}")
    print("=" * 50)
    
    # Подключаемся к Telegram
    client = TelegramClient('bfg_session', API_ID, API_HASH)
    await client.start()
    print("✅ Подключен к Telegram")
    
    # Загружаем состояние
    state = load_state()
    print(f"📁 Последняя сделка: {state['last_action']} по цене {state['last_price']}")
    
    # Отправляем приветствие
    await send_report(client, f"🤖 BFG Auto Trader запущен!\nДиапазон: ${MIN_PRICE:,.0f}-${MAX_PRICE:,.0f}\nЧувствительность: {DROP_PERCENT}%")
    
    while True:
        try:
            # 1. Получаем текущую цену
            current_price = get_btc_price()
            if current_price is None:
                await asyncio.sleep(60)
                continue
            
            # 2. Проверяем, входим ли мы в диапазон торговли
            if current_price < MIN_PRICE:
                print(f"⏸️ Цена ${current_price:,.2f} ниже минимальной ${MIN_PRICE:,.0f}, ждём...")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
                
            if current_price > MAX_PRICE:
                print(f"⏸️ Цена ${current_price:,.2f} выше максимальной ${MAX_PRICE:,.0f}, ждём...")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            
            # 3. Считаем пороги для сделки
            last_price = state.get('last_price', current_price)
            
            buy_threshold = last_price * (1 - DROP_PERCENT / 100)
            sell_threshold = last_price * (1 + RISE_PERCENT / 100)
            
            print(f"📊 Цена: ${current_price:,.2f} | Купить если ниже ${buy_threshold:,.2f} | Продать если выше ${sell_threshold:,.2f}")
            
            # 4. Принимаем решение
            action = None
            
            if current_price <= buy_threshold and state['last_action'] != 'buy':
                action = 'buy'
            elif current_price >= sell_threshold and state['last_action'] != 'sell':
                action = 'sell'
            
            # 5. Выполняем сделку
            if action == 'buy':
                print("🔻 ЦЕНА УПАЛА! ПОКУПАЮ...")
                success = await send_bfg_command(client, "Купить биткоин всё")
                
                if success:
                    report = f"""
📉 **СОВЕРШЕНА ПОКУПКА**
💰 Цена: ${current_price:,.2f}
📊 Предыдущая цена: ${last_price:,.2f}
📉 Падение: {(1 - current_price/last_price) * 100:.2f}%
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    await send_report(client, report)
                    state['last_action'] = 'buy'
                    state['last_price'] = current_price
                    state['last_action_time'] = datetime.now().isoformat()
                    save_state(state)
                    
            elif action == 'sell':
                print("🟢 ЦЕНА ВЫРОСЛА! ПРОДАЮ...")
                success = await send_bfg_command(client, "Продать биткоин всё")
                
                if success:
                    report = f"""
📈 **СОВЕРШЕНА ПРОДАЖА**
💰 Цена: ${current_price:,.2f}
📊 Предыдущая цена: ${last_price:,.2f}
📈 Рост: {(current_price/last_price - 1) * 100:.2f}%
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    await send_report(client, report)
                    state['last_action'] = 'sell'
                    state['last_price'] = current_price
                    state['last_action_time'] = datetime.now().isoformat()
                    save_state(state)
            else:
                print("⚖️ Бездействие, ждём сигнала...")
                
        except Exception as e:
            print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
            await send_report(client, f"⚠️ Ошибка в боте: {str(e)[:100]}")
        
        # Ждём следующую проверку
        await asyncio.sleep(CHECK_INTERVAL)

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен вручную. Пока, сука!")
    except Exception as e:
        print(f"\n💀 Фатальная ошибка: {e}")
        input("Нажми Enter чтобы выйти...")
