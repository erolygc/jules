# src/telegram_bildirim.py

import os
import requests
from dotenv import load_dotenv
from loguru import logger

# .env dosyasını yükle
load_dotenv()

# Telegram Bot Token ve Chat ID'yi al
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Loguru yapılandırması
logger.add("logs/telegram_bildirim.log", rotation="10 MB", retention="10 days", level="INFO")

def send_telegram_notification(product_url, old_price, new_price):
    """Telegram'a bildirim gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in .env file.")
        return

    discount_percentage = ((old_price - new_price) / old_price) * 100

    message = (
        f"🚨 FIRSAT BULUNDU! 🚨\n\n"
        f"Ürün: {product_url}\n"
        f"Eski Fiyat: {old_price:.2f} TL\n"
        f"Yeni Fiyat: {new_price:.2f} TL\n"
        f"İndirim Oranı: {discount_percentage:.2f}%\n\n"
        f"Hemen incele: {product_url}"
    )

    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(send_url, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully sent notification for {product_url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Telegram notification: {e}")
        logger.error(f"Response: {response.text}")

if __name__ == '__main__':
    # Test için örnek bir bildirim gönder
    logger.info("Sending a test notification...")
    # .env dosyasında test için değerler olduğundan emin olun
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_notification(
            product_url="https://www.trendyol.com/ornek-urun",
            old_price=100.0,
            new_price=75.0
        )
    else:
        logger.warning("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are not set in .env. Skipping test notification.")
    logger.info("Test notification script finished.")
