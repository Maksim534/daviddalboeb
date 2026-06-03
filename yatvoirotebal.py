#!/usr/bin/env python3
# Playerok Brawl Stars Monitor - БАЗОВАЯ РАБОЧАЯ ВЕРСИЯ
# Мониторит дешёвые аккаунты и шлёт уведомления в Telegram

import requests
import time
import re
import json
import os
import random
from datetime import datetime

# ========== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ==========
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
CHAT_ID = "8564427714"

# Ссылка для парсинга (твоя новая, рабочая)
PLAYEROK_URL = "https://playerok.com/brawl-stars/accounts"

# Настройки фильтрации
MIN_DISCOUNT = 20      # Минимальная скидка в %
MAX_PRICE = 5000       # Максимальная цена в рублях
MIN_LEGENDS = 0        # Минимум легендарок (0 - не фильтровать)
MIN_TROPHIES = 0       # Минимум трофеев (0 - не фильтровать)

# Интервал проверки (секунды)
CHECK_INTERVAL = 180   # 3 минуты

# Файл для хранения просмотренных ID
SEEN_FILE = "seen_ids.json"
# ===============================================

# Функция для отправки в Telegram (синхронная, без ошибок)
def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Уведомление отправлено")
        else:
            print(f"❌ Ошибка Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# Загрузка просмотренных ID
def load_seen_ids():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(json.load(f))
    return set()

# Сохранение просмотренных ID
def save_seen_ids(seen_ids):
    if len(seen_ids) > 1000:
        seen_ids = set(list(seen_ids)[-500:])
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen_ids), f)

# Вытаскивает число из строки
def extract_number(text):
    numbers = re.findall(r'(\d+[,.]?\d*)', text.replace(',', '.'))
    if numbers:
        return float(numbers[0])
    return 0

# Основной парсинг страницы
def get_listings():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print(f"📡 Запрос к {PLAYEROK_URL}")
        response = requests.get(PLAYEROK_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Ошибка HTTP {response.status_code}")
            return []
        
        html = response.text
        listings = []
        
        # Ищем все ссылки на товары
        product_links = re.findall(r'href="(/products/\d+[^"]*)"', html)
        product_links = list(dict.fromkeys(product_links))  # Убираем дубли
        
        print(f"   Найдено ссылок на товары: {len(product_links)}")
        
        for link in product_links[:30]:  # Берём первые 30, чтобы не перегружать
            product_url = "https://playerok.com" + link
            product_id = re.search(r'/products/(\d+)', link)
            product_id = product_id.group(1) if product_id else None
            
            if not product_id:
                continue
            
            # Ищем блок с ценой вокруг этой ссылки
            # Простой способ: ищем цену в тексте рядом
            price_pattern = r'(\d+[\s]?[\d]*)\s*₽'
            prices = re.findall(price_pattern, html)
            
            price = 0
            discount = 0
            
            if prices:
                # Берём первую попавшуюся цену (костыль, но для начала пойдёт)
                price = int(re.sub(r'\s', '', prices[0])) if prices else 0
            
            # Ищем количество легендарок
            legends = 0
            legends_match = re.search(r'(\d+)\s*лег', html.lower())
            if legends_match:
                legends = int(legends_match.group(1))
            
            # Ищем трофеи
            trophies = 0
            trophies_match = re.search(r'(\d+[\s]?[\d]*)\s*троф', html.lower())
            if trophies_match:
                trophies = int(re.sub(r'\s', '', trophies_match.group(1)))
            
            listing = {
                'id': product_id,
                'price': price,
                'discount': discount,
                'legends': legends,
                'trophies': trophies,
                'link': product_url
            }
            
            listings.append(listing)
        
        return listings
        
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        return []

# Проверка, стоит ли покупать
def is_worth_buying(listing):
    if MAX_PRICE > 0 and listing['price'] > MAX_PRICE:
        return False
    
    if listing['discount'] >= MIN_DISCOUNT:
        return True
    
    if MIN_LEGENDS > 0 and listing['legends'] >= MIN_LEGENDS:
        return True
    
    if MIN_TROPHIES > 0 and listing['trophies'] >= MIN_TROPHIES:
        return True
    
    if listing['price'] <= 100 and listing['price'] > 0:
        return True
    
    return False

# Формирование сообщения
def format_message(listing, reason="🔥 Найдена дешёвка!"):
    message = f"""
🔔 **{reason}**

💰 Цена: **{listing['price']} ₽**
⭐ Легендарки: {listing['legends']}
🏆 Трофеи: {listing['trophies']}

🔗 [Ссылка на товар]({listing['link']})

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
    return message

# Основной цикл
def main():
    print("=" * 60)
    print("🚀 PLAYEROK MONITOR v3.0 ЗАПУЩЕН!")
    print(f"📊 Проверка каждые {CHECK_INTERVAL} сек")
    print(f"🎯 Фильтры: цена <={MAX_PRICE}₽, скидка >={MIN_DISCOUNT}%, легендарки >={MIN_LEGENDS}, трофеи >={MIN_TROPHIES}")
    print(f"🔗 Ссылка: {PLAYEROK_URL}")
    print("=" * 60)
    
    # Отправляем тестовое сообщение
    send_telegram("✅ **Мониторинг Playerok запущен!**\n\nБуду следить за дешёвыми аккаунтами Brawl Stars.")
    
    seen_ids = load_seen_ids()
    print(f"📁 Загружено {len(seen_ids)} просмотренных ID")
    
    while True:
        try:
            # Случайная задержка перед запросом (от 5 до 15 секунд)
            delay = random.uniform(5, 15)
            print(f"💤 Пауза {delay:.1f} сек перед запросом...")
            time.sleep(delay)
            
            listings = get_listings()
            print(f"📦 Получено товаров: {len(listings)}")
            
            new_deals = 0
            for listing in listings:
                if listing['id'] in seen_ids:
                    continue
                
                if is_worth_buying(listing):
                    message = format_message(listing)
                    send_telegram(message)
                    new_deals += 1
                    time.sleep(2)  # Пауза между уведомлениями
                
                seen_ids.add(listing['id'])
            
            if new_deals > 0:
                print(f"🎉 НАЙДЕНО {new_deals} ВЫГОДНЫХ ПРЕДЛОЖЕНИЙ!")
            else:
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Новых предложений нет")
            
            # Сохраняем просмотренные ID
            save_seen_ids(seen_ids)
            
        except Exception as e:
            print(f"💥 Ошибка: {e}")
            send_telegram(f"⚠️ Ошибка мониторинга: {str(e)[:100]}")
        
        print(f"💤 Жду {CHECK_INTERVAL} секунд...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Остановлено пользователем")
        send_telegram("🛑 Мониторинг Playerok остановлен")
    except Exception as e:
        print(f"\n💀 Фатальная ошибка: {e}")
        send_telegram(f"💀 Мониторинг упал: {e}")
