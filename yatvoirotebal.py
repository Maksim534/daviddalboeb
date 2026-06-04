#!/usr/bin/env python3
# Playerok Monitor - ФИКС 403 ОШИБКИ
# Мониторит дешёвые аккаунты Brawl Stars

import requests
import time
import re
import json
import os
import random
from datetime import datetime

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
CHAT_ID = "8564427714"

# ТРИ ВАРИАНТА ССЫЛОК (пробуем по очереди, какая пройдёт)
URLS_TO_TRY = [
    "https://playerok.com/category/akkaunty-brawl-stars",
    "https://playerok.com/brawl-stars/accounts",
    "https://playerok.com/category/akkaunty-brawl-stars?sorting=newest"
]

# Настройки фильтрации
MIN_DISCOUNT = 20
MAX_PRICE = 5000
MIN_LEGENDS = 0
MIN_TROPHIES = 0

# Интервал проверки (секунды)
CHECK_INTERVAL = 300  # 5 минут, чтобы не бесить сайт

# Файл для хранения просмотренных ID
SEEN_FILE = "seen_ids.json"
# =================================

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Уведомление отправлено")
        else:
            print(f"❌ Ошибка Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

def load_seen_ids():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen_ids(seen_ids):
    if len(seen_ids) > 1000:
        seen_ids = set(list(seen_ids)[-500:])
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen_ids), f)

def get_listings(url, attempt=1):
    """Парсит страницу с разными заголовками при повторах"""
    
    # Разные варианты User-Agent
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': user_agents[attempt % len(user_agents)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://playerok.com/',
    }
    
    # Куки (имитация сессии)
    cookies = {
        'playerok_lang': 'ru',
        '_ga': 'GA1.2.123456789.123456789',
    }
    
    try:
        print(f"📡 Запрос к {url} (попытка {attempt})")
        response = requests.get(url, headers=headers, cookies=cookies, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return []
        
        html = response.text
        
        # Проверяем, не попали ли на капчу
        if "captcha" in html.lower() or "доступ запрещен" in html.lower():
            print("❌ Обнаружена капча или блокировка!")
            return []
        
        # Ищем ссылки на товары
        product_links = re.findall(r'href="(/products/\d+[^"]*)"', html)
        product_links = list(dict.fromkeys(product_links))
        
        print(f"   Найдено ссылок на товары: {len(product_links)}")
        
        # Парсим цены и характеристики из карточек
        listings = []
        
        for link in product_links[:40]:  # Берём первые 40
            product_url = "https://playerok.com" + link
            product_id = re.search(r'/products/(\d+)', link)
            product_id = product_id.group(1) if product_id else None
            
            if not product_id:
                continue
            
            # Ищем цену вокруг этой ссылки (контекстный поиск)
            # Находим кусок HTML вокруг ссылки
            link_pos = html.find(link)
            context = html[max(0, link_pos-1000):min(len(html), link_pos+2000)]
            
            # Ищем цену в контексте
            price_match = re.search(r'(\d+[\s]?[\d]*)\s*₽', context)
            price = int(re.sub(r'\s', '', price_match.group(1))) if price_match else 0
            
            # Ищем скидку
            discount_match = re.search(r'-(\d+)%', context)
            discount = int(discount_match.group(1)) if discount_match else 0
            
            # Ищем легендарки
            legends = 0
            legends_match = re.search(r'(\d+)\s*(?:легендарных|легендарки|legendary)', context.lower())
            if legends_match:
                legends = int(legends_match.group(1))
            
            # Ищем трофеи
            trophies = 0
            trophies_match = re.search(r'(\d+[\s]?[\d]*)\s*(?:трофеев|трофеи|trophy)', context.lower())
            if trophies_match:
                trophies = int(re.sub(r'\s', '', trophies_match.group(1)))
            
            if price > 0:
                listings.append({
                    'id': product_id,
                    'price': price,
                    'discount': discount,
                    'legends': legends,
                    'trophies': trophies,
                    'link': product_url
                })
        
        return listings
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

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

def format_message(listing):
    reason = []
    if listing['discount'] >= MIN_DISCOUNT:
        reason.append(f"🔥 Скидка {listing['discount']}%")
    if listing['legends'] >= 1:
        reason.append(f"⭐️ {listing['legends']} легендарок")
    if listing['trophies'] >= 1:
        reason.append(f"🏆 {listing['trophies']} трофеев")
    
    reason_text = ", ".join(reason) if reason else "💰 Дешёвый аккаунт!"
    
    return f"""
🔔 **{reason_text}**

💰 Цена: **{listing['price']} ₽**
⭐ Легендарки: {listing['legends']}
🏆 Трофеи: {listing['trophies']}

🔗 [Ссылка на товар]({listing['link']})

⏰ {datetime.now().strftime('%H:%M:%S')}
"""

def main():
    print("=" * 60)
    print("🚀 PLAYEROK MONITOR v4.0 (ФИКС 403)")
    print(f"📊 Проверка каждые {CHECK_INTERVAL} сек")
    print(f"🎯 Фильтры: цена <={MAX_PRICE}₽, скидка >={MIN_DISCOUNT}%")
    print(f"🔗 Будет проверено {len(URLS_TO_TRY)} ссылок")
    print("=" * 60)
    
    send_telegram("✅ **Мониторинг Playerok v4 запущен!**\n\nИсправлена ошибка 403, пробуем обойти защиту.")
    
    seen_ids = load_seen_ids()
    print(f"📁 Загружено {len(seen_ids)} просмотренных ID")
    
    url_attempt = 0
    request_attempt = 0
    
    while True:
        try:
            # Случайная задержка перед запросом (от 30 до 90 секунд)
            delay = random.uniform(30, 90)
            print(f"💤 Пауза {delay:.1f} сек...")
            time.sleep(delay)
            
            # Берём следующую ссылку из списка (по кругу)
            current_url = URLS_TO_TRY[url_attempt % len(URLS_TO_TRY)]
            url_attempt += 1
            request_attempt += 1
            
            listings = get_listings(current_url, request_attempt)
            print(f"📦 Получено товаров: {len(listings)}")
            
            if len(listings) == 0 and request_attempt > 3:
                print("⚠️ Долгое время нет результатов. Возможно, IP заблокирован.")
                send_telegram("⚠️ Внимание! Playerok блокирует запросы. Возможно, нужна смена IP или настройка прокси.")
                request_attempt = 0
            
            new_deals = 0
            for listing in listings:
                if listing['id'] in seen_ids:
                    continue
                
                if is_worth_buying(listing):
                    message = format_message(listing)
                    send_telegram(message)
                    new_deals += 1
                    time.sleep(3)
                
                seen_ids.add(listing['id'])
            
            if new_deals > 0:
                print(f"🎉 НАЙДЕНО {new_deals} ВЫГОДНЫХ ПРЕДЛОЖЕНИЙ!")
            else:
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Новых предложений нет")
            
            save_seen_ids(seen_ids)
            
            # Если успешно получили товары, сбрасываем счётчик попыток
            if len(listings) > 0:
                request_attempt = 0
                
        except Exception as e:
            print(f"💥 Ошибка: {e}")
            send_telegram(f"⚠️ Ошибка: {str(e)[:100]}")
        
        print(f"💤 Жду {CHECK_INTERVAL} секунд...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Остановлено")
        send_telegram("🛑 Мониторинг остановлен")
    except Exception as e:
        print(f"\n💀 Ошибка: {e}")
        send_telegram(f"💀 Ошибка: {e}")
