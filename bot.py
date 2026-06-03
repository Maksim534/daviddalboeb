#!/usr/bin/env python3
# BTC Монитор - кидает сообщение когда биток резко движется

import asyncio
import requests
from telegram import Bot

# ========== НАСТРОЙКИ (твои, из GitHub) ==========
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"  # твой токен
CHAT_ID = "8564427714"  # твой ID
PROCESSOR = 3.5  # Чувствительность: уведомлять при изменении > 3.5%
CHECK_INTERVAL = 60  # Проверка каждые 60 секунд
# ================================================

bot = Bot(token=BOT_TOKEN)

def get_btc():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    data = requests.get(url).json()
    return float(data['price'])

async def send_alert(price, old_price, percent):
    if percent > 0:
        direction = "📈 ВЗЛЕТЕЛ НАХУЙ"
        emoji = "🚀"
    else:
        direction = "📉 ЕБНУЛСЯ ВНИЗ"
        emoji = "💀"
    
    msg = f"""{emoji} {direction}

💰 Было: ${old_price:,.0f}
💰 Стало: ${price:,.0f}
📊 Изменение: {percent:+.2f}%

⏰ {__import__('datetime').datetime.now().strftime('%H:%M:%S')}"""
    
    await bot.send_message(chat_id=CHAT_ID, text=msg)

async def main():
    print("🚀 BTC Монитор запущен!")
    print(f"📊 Чувствительность: {PROCESSOR}%")
    print(f"⏱️  Проверка каждые {CHECK_INTERVAL} сек")
    
    old = get_btc()
    print(f"💰 Текущая цена: ${old:,.0f}")
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"✅ BTC Монитор запущен!\n💰 Цена: ${old:,.0f}\n📊 Оповещение при изменении > {PROCESSOR}%"
    )
    
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
    asyncio.run(main())
