# src/gorev_yoneticisi.py

import os
import requests
from dotenv import load_dotenv
from loguru import logger
import sqlite3
import time
from bs4 import BeautifulSoup

# .env dosyasını yükle
load_dotenv()

# ScraperAPI key'i al
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

# Loguru yapılandırması
logger.add("logs/gorev_yoneticisi.log", rotation="10 MB", retention="10 days", level="INFO")

def get_db_connection():
    """Veritabanı bağlantısı oluşturur."""
    return sqlite3.connect('data/trendyol.db')

def get_all_products(conn):
    """Veritabanındaki tüm ürünleri alır."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, url FROM products")
    products = cursor.fetchall()
    return products

def get_product_price(product_url):
    """ScraperAPI kullanarak ürünün fiyatını çeker."""
    if not SCRAPER_API_KEY:
        logger.error("SCRAPER_API_KEY not found in .env file.")
        return None

    logger.info(f"Fetching price for {product_url}")
    payload = {'api_key': SCRAPER_API_KEY, 'url': product_url}
    try:
        response = requests.get('http://api.scraperapi.com', params=payload)
        response.raise_for_status()  # HTTP hatalarını kontrol et

        # Fiyatı parse et
        soup = BeautifulSoup(response.text, 'html.parser')

        # Fiyat etiketini bulmak için doğru seçiciyi bulmamız gerekiyor.
        # Örnek bir seçici (bu, Trendyol'un yapısına göre değişebilir):
        price_element = soup.find('span', class_='prc-dsc')

        if price_element:
            price_text = price_element.text.strip().replace('TL', '').replace(',', '.').strip()
            logger.info(f"Found price: {price_text} for {product_url}")
            return float(price_text)
        else:
            logger.warning(f"Price element not found for {product_url}")
            # Sayfa kaynağını loglayarak hata ayıklama yapabiliriz
            with open(f"logs/price_not_found_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {product_url}: {e}")
        return None

def add_price(conn, product_id, price):
    """Veritabanına yeni bir fiyat ekler."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prices (product_id, price) VALUES (?, ?)", (product_id, price))
    conn.commit()
    logger.info(f"Added price {price} for product_id {product_id}")

def main():
    """Ana görev yöneticisi fonksiyonu."""
    logger.info("Starting price tracking task...")

    conn = get_db_connection()
    products = get_all_products(conn)

    if not products:
        logger.warning("No products found in the database. Run selenium_toplayici.py first.")
        return

    for product_id, product_url in products:
        price = get_product_price(product_url)
        if price:
            add_price(conn, product_id, price)

        # Trendyol'a karşı nazik olmak için istekler arasında bekleme ekleyelim
        time.sleep(5)

    conn.close()
    logger.info("Price tracking task finished.")

if __name__ == "__main__":
    main()
