#!/usr/bin/env python3
# Playerok Brawl Stars Monitor - ФУЛЛ ВЕРСИЯ
# Мониторит дешёвые аккаунты и шлёт уведомления в Telegram

import requests
import time
import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError

# ========== НАСТРОЙКИ ==========
# Telegram (твои данные)
BOT_TOKEN = "8730800500:AAGET1CNnixecxcDhgHV62grw_zf6SWMyFQ"
CHAT_ID = "8564427714"

# Настройки мониторинга
CHECK_INTERVAL = 180      # Проверять каждые 3 минуты (не меньше 60)
MIN_DISCOUNT = 20         # Минимальная скидка в % (50 = половинная цена)
MIN_LEGENDS = 0           # Минимум легендарок (2-3)
MIN_TROPHIES = 0       # Минимум трофеев (0 если похуй)
MAX_PRICE = 5000           # Максимальная цена в рублях (0 если без ограничения)
SHOW_LOW_TROPHIES = True  # Показывать акки с низкими трофеями, но хорошей ценой

# Ссылки для мониторинга (можно добавить другие разделы)
URLS = {
    "accounts": "https://playerok.com/category/akkaunty-brawl-stars?sorting=newest",
    # "gems": "https://playerok.com/category/gemy-brawl-stars?sorting=newest",  # раскомментируй если нужно
    # "skins": "https://playerok.com/category/skiny-brawl-stars?sorting=newest",
}

# Файл для хранения ID просмотренных товаров
SEEN_FILE = "seen_ids.json"
# =================================

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

def load_seen_ids():
    """Загружает список просмотренных товаров"""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen_ids(seen_ids):
    """Сохраняет список просмотренных товаров"""
    # Ограничиваем размер до 500 последних
    if len(seen_ids) > 500:
        seen_ids = set(list(seen_ids)[-500:])
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen_ids), f)

def extract_number(text):
    """Вытаскивает число из строки"""
    numbers = re.findall(r'(\d+[,.]?\d*)', text.replace(',', '.'))
    if numbers:
        return float(numbers[0])
    return 0

def parse_listing(card):
    """Парсит одну карточку товара с Playerok"""
    try:
        # Цена
        price_elem = card.select_one('[data-testid="price-value"]')
        price_text = price_elem.text if price_elem else "0"
        price = int(extract_number(price_text))
        
        # Оригинальная цена и скидка
        old_price_elem = card.select_one('[data-testid="old-price"]')
        if old_price_elem:
            old_price = int(extract_number(old_price_elem.text))
            discount = round((1 - price / old_price) * 100) if old_price > 0 else 0
        else:
            discount = 0
        
        # Легендарки
        legends = 0
        legends_elem = card.select_one('[title*="Легендарные"], [title*="легендарных"]')
        if legends_elem:
            legends = int(extract_number(legends_elem.text))
        
        # Трофеи
        trophies = 0
        trophies_elem = card.select_one('[title*="Трофеи"], [title*="трофеев"]')
        if trophies_elem:
            trophies = int(extract_number(trophies_elem.text))
        
        # Название товара
        title_elem = card.select_one('h3, [data-testid="product-title"]')
        title = title_elem.text.strip() if title_elem else "Без названия"
        
        # Ссылка
        link_elem = card.select_one('a[href*="/products/"]')
        if link_elem and link_elem.get('href'):
            link = "https://playerok.com" + link_elem['href']
        else:
            link = ""
        
        # Уникальный ID товара (из ссылки)
        product_id = re.search(r'/products/(\d+)', link)
        product_id = product_id.group(1) if product_id else None
        
        if not product_id or price == 0:
            return None
        
        return {
            'id': product_id,
            'price': price,
            'discount': discount,
            'legends': legends,
            'trophies': trophies,
            'title': title,
            'link': link
        }
    except Exception as e:
        print(f"Ошибка парсинга карточки: {e}")
        return None

def get_listings(url):
    """Получает список товаров с указанной страницы"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        listings = []
        # Пробуем разные селекторы для карточек товаров
        cards = soup.select('[data-testid="product-card"]')
        if not cards:
            cards = soup.select('.product-card')
        if not cards:
            cards = soup.select('article')
        
        for card in cards:
            listing = parse_listing(card)
            if listing:
                listings.append(listing)
        
        return listings
    except Exception as e:
        print(f"Ошибка получения страницы {url}: {e}")
        return []

def is_worth_buying(listing):
    """Проверяет, стоит ли покупать этот аккаунт"""
    # Проверка по цене
    if MAX_PRICE > 0 and listing['price'] > MAX_PRICE:
        return False, ""
    
    # Проверка по скидке (если есть скидка)
    if listing['discount'] >= MIN_DISCOUNT:
        return True, f"🔥 СКИДКА {listing['discount']}%!"
    
    # Проверка по легендаркам (если есть)
    if listing['legends'] >= MIN_LEGENDS:
        return True, f"🎯 {listing['legends']} ЛЕГЕНДАРКИ за {listing['price']}₽"
    
    # Проверка по трофеям (если есть)
    if SHOW_LOW_TROPHIES and listing['trophies'] >= MIN_TROPHIES:
        return True, f"🏆 {listing['trophies']} ТРОФЕЕВ за {listing['price']}₽"
    
    # Если цена очень низкая (меньше 100₽) — тоже стоит глянуть
    if listing['price'] <= 100 and (listing['legends'] > 0 or listing['trophies'] > 1000):
        return True, f"💎 КОПЕЙКИ - {listing['price']}₽!"
    
    return False, ""

def format_message(listing, reason):
    """Форматирует сообщение для отправки"""
    # Эмодзи в зависимости от типа сделки
    if "СКИДКА" in reason:
        emoji = "🔥🔥🔥"
    elif "ЛЕГЕНДАРКИ" in reason:
        emoji = "⭐️⭐️⭐️"
    elif "ТРОФЕЕВ" in reason:
        emoji = "🏆🏆🏆"
    else:
        emoji = "💰"
    
    message = f"""
{emoji} **НАЙДЕНА ДЕШЁВКА НА PLAYEROK!** {emoji}

{reason}

💰 Цена: **{listing['price']} ₽**
📉 Скидка: {listing['discount']}%
⭐ Легендарки: {listing['legends']}
🏆 Трофеи: {listing['trophies']}

📝 {listing['title'][:100]}

🔗 [Ссылка на товар]({listing['link']})

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
    return message

def send_telegram(text):
    """Отправляет сообщение в Telegram"""
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown', disable_web_page_preview=False)
        print(f"✅ Уведомление отправлено")
    except TelegramError as e:
        print(f"❌ Ошибка Telegram: {e}")

def monitor():
    """Основной цикл мониторинга"""
    print("=" * 60)
    print("🚀 PLAYEROK MONITOR v2.0 ЗАПУЩЕН!")
    print(f"📊 Проверка каждые {CHECK_INTERVAL} сек")
    print(f"🎯 Фильтры: скидка >={MIN_DISCOUNT}%, цена <={MAX_PRICE}₽, легендарки >={MIN_LEGENDS}, трофеи >={MIN_TROPHIES}")
    print(f"🔗 Мониторим разделы: {', '.join(URLS.keys())}")
    print("=" * 60)
    
    # Отправляем тестовое сообщение
    send_telegram("✅ **Мониторинг Playerok запущен!**\n\nБуду следить за дешёвыми аккаунтами Brawl Stars.")
    
    seen_ids = load_seen_ids()
    
    while True:
        try:
            all_listings = []
            for name, url in URLS.items():
                print(f"📡 Проверяю раздел: {name}...")
                listings = get_listings(url)
                all_listings.extend(listings)
                print(f"   Найдено {len(listings)} товаров")
            
            # Сортируем по цене (дешёвые первыми)
            all_listings.sort(key=lambda x: x['price'])
            
            new_deals = 0
            for listing in all_listings:
                if listing['id'] in seen_ids:
                    continue
                
                worth, reason = is_worth_buying(listing)
                if worth:
                    message = format_message(listing, reason)
                    send_telegram(message)
                    new_deals += 1
                    # Не спамим слишком быстро
                    time.sleep(2)
                
                seen_ids.add(listing['id'])
            
            if new_deals > 0:
                print(f"🎉 Найдено {new_deals} выгодных предложений!")
            else:
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Новых выгодных предложений нет")
            
            # Сохраняем просмотренные ID
            save_seen_ids(seen_ids)
            
        except Exception as e:
            print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
            send_telegram(f"⚠️ Ошибка в мониторинге: {str(e)[:100]}")
        
        # Ждём перед следующим циклом
        print(f"💤 Жду {CHECK_INTERVAL} секунд...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен вручную")
        send_telegram("🛑 Мониторинг Playerok остановлен")
    except Exception as e:
        print(f"\n💀 Фатальная ошибка: {e}")
        send_telegram(f"💀 Мониторинг упал: {e}")
