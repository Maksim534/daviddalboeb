#!/usr/bin/env python3
# BTC MONITOR - КИДАЕТ В ТЕЛЕГУ ПРИ РЕЗКИХ ДВИЖЕНИЯХ

import requests
import time
from datetime import datetime

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
CHAT_ID = "8564427714"

# Чувствительность (процент изменения для уведомления)
PROCESSOR = 0.5  # 2.5% - если меняется на столько - кидаем оповещение

# Как часто проверяем (в секундах)
CHECK_INTERVAL = 60  # каждую минуту
# ===============================================

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
        print("✅ Уведомление отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def get_btc():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    try:
        data = requests.get(url, timeout=10).json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Ошибка получения цены: {e}")
        return None

def format_message(price, old_price, percent):
    if percent > 0:
        direction = "🚀📈 ВЗЛЕТЕЛ НАХУЙ!"
        emoji = "🟢🟢🟢"
    else:
        direction = "💀📉 ЕБНУЛСЯ ВНИЗ!"
        emoji = "🔴🔴🔴"
    
    return f"""{emoji} {direction} {emoji}

💰 Было: ${old_price:,.0f}
💰 Стало: ${price:,.0f}
📊 Изменение: {percent:+.2f}%

⏰ {datetime.now().strftime('%H:%M:%S')}
"""

def main():
    print("=" * 50)
    print("🚀 BTC МОНИТОР ЗАПУЩЕН!")
    print(f"📊 Чувствительность: {PROCESSOR}%")
    print(f"⏱️  Проверка каждые {CHECK_INTERVAL} сек")
    print("=" * 50)
    
    send_telegram("✅ **BTC Монитор запущен!**\nБуду следить за биткоином.")
    
    old_price = get_btc()
    if not old_price:
        print("❌ Не удалось получить начальную цену")
        return
    
    print(f"💰 Текущая цена: ${old_price:,.0f}")
    send_telegram(f"📊 **Стартовая цена:** ${old_price:,.0f}")
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        try:
            new_price = get_btc()
            if not new_price:
                continue
            
            percent = (new_price - old_price) / old_price * 100
            
            print(f"💰 Цена: ${new_price:,.0f} ({percent:+.2f}%)")
            
            if abs(percent) >= PROCESSOR:
                msg = format_message(new_price, old_price, percent)
                send_telegram(msg)
                old_price = new_price
                
        except Exception as e:
            print(f"💥 Ошибка: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Остановлен")
        send_telegram("🛑 **BTC Монитор остановлен**")
    except Exception as e:
        print(f"💀 Ошибка: {e}")
        send_telegram(f"💀 Ошибка: {e}")
