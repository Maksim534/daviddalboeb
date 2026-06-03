#!/usr/bin/env python3
# BTC МОНИТОР - с красивыми картинками и оповещениями

import asyncio
import requests
from telegram import Bot, InputFile
from io import BytesIO
import random

# ========== ТВОИ НАСТРОЙКИ ==========
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
CHAT_ID = "8564427714"
CHECK_INTERVAL = 60       # Проверять каждую минуту
PROCESSOR = 1.1       # Оповещать при изменении больше 3.5%
# ===================================

bot = Bot(token=BOT_TOKEN)

# Генератор простых картинок (ASCII-графика)
def generate_up_image(price):
    image = f"""
    🟢🟢🟢🟢🟢🟢🟢
    🟢🚀🚀🚀🚀🚀🟢
    🟢🚀 БИТОК 🚀🟢
    🟢🚀 ВЗЛЕТЕЛ 🚀🟢
    🟢🚀🚀🚀🚀🚀🟢
    🟢🟢🟢🟢🟢🟢🟢
    💰 ЦЕНА: ${price:,.0f}
    """
    return image

def generate_down_image(price):
    image = f"""
    🔴🔴🔴🔴🔴🔴🔴
    🔴💀💀💀💀💀🔴
    🔴💀 БИТОК 💀🔴
    🔴💀 ЕБНУЛСЯ 💀🔴
    🔴💀💀💀💀💀🔴
    🔴🔴🔴🔴🔴🔴🔴
    💰 ЦЕНА: ${price:,.0f}
    """
    return image

async def send_alert(price, old_price, percent):
    direction = "📈 ВЗЛЕТЕЛ" if percent > 0 else "📉 ЕБНУЛСЯ"
    
    if percent > 0:
        emoji = "🚀🎉💰"
        image = generate_up_image(price)
    else:
        emoji = "💀📉🔥"
        image = generate_down_image(price)
    
    caption = f"""
{emoji} {direction} НАХУЙ! {emoji}

💰 Было: ${old_price:,.0f}
💰 Стало: ${price:,.0f}
📊 Изменение: {percent:+.2f}%

⏰ {__import__('datetime').datetime.now().strftime('%H:%M:%S')}
"""
    
    # Отправляем картинку как фото (файл)
    try:
        photo = BytesIO()
        photo.write(image.encode())
        photo.seek(0)
        await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption)
    except:
        # Если с картинкой проблемы, отправим просто текст
        await bot.send_message(chat_id=CHAT_ID, text=caption)

def get_btc_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    data = requests.get(url).json()
    return float(data['price'])

async def main():
    print("🚀 Красивый мониторинг BTC запущен!")
    print(f"Чувствительность: {PROCESSOR}%")
    
    old_price = get_btc_price()
    await bot.send_message(chat_id=CHAT_ID, text=f"✅ Мониторинг BTC запущен!\n💰 Текущая цена: ${old_price:,.0f}\n🔔 Оповещу при изменении > {PROCESSOR}%")
    
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            new_price = get_btc_price()
            percent = (new_price - old_price) / old_price * 100
            
            if abs(percent) >= PROCESSOR:
                await send_alert(new_price, old_price, percent)
                old_price = new_price
            else:
                print(f"Цена: ${new_price:,.0f} ({percent:+.2f}%) - без изменений")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
