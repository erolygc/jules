import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
from pyvirtualdisplay import Display
from loguru import logger
import database

# Log yapılandırması
logger.add("logs/selenium_toplayici.log", rotation="10 MB", level="DEBUG")

def get_product_links(url):
    """
    Verilen URL'deki ürün linklerini toplar.
    """
    links = []
    display = None
    driver = None
    try:
        logger.info("Starting virtual display...")
        display = Display(visible=0, size=(1920, 1080))
        display.start()
        logger.info("Virtual display started.")

        logger.info("Setting up Chrome options...")
        options = uc.ChromeOptions()
        # options.add_argument('--headless') # Headless modu GUI olmayan sunucular için
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--window-size=1920,1080")
        logger.info("Chrome options set.")

        logger.info("Initializing undetected_chromedriver...")
        driver = uc.Chrome(options=options)
        logger.info("WebDriver initialized.")

        logger.info(f"Navigating to URL: {url}")
        driver.get(url)
        logger.info("Page loaded.")

        # OneTrust çerez banner'ını bekleyip kabul et
        try:
            logger.info("Waiting for OneTrust cookie banner...")
            wait = WebDriverWait(driver, 20)
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            logger.info("Cookie banner found. Clicking 'Accept All'...")
            accept_button.click()
            logger.info("Clicked 'Accept All' on cookie banner.")
            # Sayfanın yüklenmesi için ek süre
            time.sleep(5)
        except Exception as e:
            logger.warning(f"Cookie banner not found or could not be clicked: {e}")
            driver.save_screenshot('cookie_banner_error.png')

        # Debug için sayfa kaynağını ve ekran görüntüsünü kaydet
        logger.info("Saving page source and screenshot for debugging...")
        with open("page_source_elektronik.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot('screenshot_after_cookie.png')
        logger.info("Debug files saved.")


        # Ürün linklerini bul
        logger.info("Searching for product links...")
        product_elements = driver.find_elements(By.CSS_SELECTOR, "a.product-card")
        links = [element.get_attribute('href') for element in product_elements]
        logger.info(f"Found {len(links)} product links.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if driver:
            driver.save_screenshot('error_screenshot.png')
    finally:
        if driver:
            logger.info("Closing WebDriver.")
            driver.quit()
        if display:
            logger.info("Stopping virtual display.")
            display.stop()
    return links

def main():
    """
    Ana çalışma fonksiyonu.
    """
    conn = database.create_connection()
    if not conn:
        return

    # Veritabanını başlat
    database.create_tables(conn)

    # Trendyol elektronik kategorisi URL'si
    url = "https://www.trendyol.com/elektronik-x-c109"

    # Ürün linklerini topla
    product_links = get_product_links(url)

    if not product_links:
        logger.warning("No product links found.")
        conn.close()
        return

    # Linkleri veritabanına ekle
    for link in product_links:
        database.add_product(conn, link)
    logger.info(f"{len(product_links)} links added to the database.")

    conn.close()

if __name__ == "__main__":
    main()
