import requests
from bs4 import BeautifulSoup
import sys

# Функция для выполнения поиска в Google
def google_search(query):
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("h3")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get_text()}")
    except requests.RequestException as e:
        print(f"Ошибка при запросе: {e}")

# Основная функция
if name == "main":
    if len(sys.argv) < 3:
        print("Использование: python script.py <ФИО> <номер_телефона>")
        sys.exit(1)
    
    fio = sys.argv[1]
    phone = sys.argv[2]
    query = f"{fio} {phone} site:vk.com | site:ok.ru | site:facebook.com"
    
    print(f"Поиск информации для: {fio}, номер: {phone}")
    google_search(query)
