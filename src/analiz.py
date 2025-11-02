# src/analiz.py

import sqlite3
from loguru import logger
from datetime import datetime, timedelta

# Loguru yapılandırması
logger.add("logs/analiz.log", rotation="10 MB", retention="10 days", level="INFO")

def get_db_connection():
    """Veritabanı bağlantısı oluşturur."""
    return sqlite3.connect('data/trendyol.db')

def get_all_products(conn):
    """Veritabanındaki tüm ürünleri alır."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, url FROM products")
    products = cursor.fetchall()
    return products

def get_price_history(conn, product_id, days=7):
    """Bir ürünün son 'days' günlük fiyat geçmişini alır."""
    cursor = conn.cursor()
    seven_days_ago = datetime.now() - timedelta(days=days)
    cursor.execute("""
        SELECT price, timestamp FROM prices
        WHERE product_id = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (product_id, seven_days_ago))
    return cursor.fetchall()

def calculate_average_price(price_history):
    """Fiyat geçmişinin ortalamasını hesaplar."""
    if not price_history:
        return 0
    total_price = sum(price for price, timestamp in price_history)
    return total_price / len(price_history)

def analyze_prices():
    """Fiyatları analiz eder ve indirimleri tespit eder."""
    logger.info("Starting price analysis...")
    conn = get_db_connection()
    products = get_all_products(conn)

    if not products:
        logger.warning("No products found in the database.")
        return

    for product_id, product_url in products:
        price_history = get_price_history(conn, product_id)

        if len(price_history) < 2:
            logger.info(f"Not enough price history for product {product_id} to analyze.")
            continue

        latest_price = price_history[0][0]
        # Son 7 günün ortalamasını alırken son fiyatı hariç tutabiliriz
        average_price = calculate_average_price(price_history[1:])

        if average_price == 0:
            continue

        price_drop_percentage = ((average_price - latest_price) / average_price) * 100

        if price_drop_percentage >= 25:
            logger.success(f"FIRSAT BULUNDU! Product: {product_url}")
            logger.success(f"  - Eski Ortalama Fiyat: {average_price:.2f} TL")
            logger.success(f"  - Yeni Fiyat: {latest_price:.2f} TL")
            logger.success(f"  - İndirim Oranı: {price_drop_percentage:.2f}%")
            # Burada telegram_bildirim.py'yi tetikleyebiliriz
            # send_telegram_notification(product_url, average_price, latest_price)

    conn.close()
    logger.info("Price analysis finished.")

if __name__ == "__main__":
    analyze_prices()
