import sqlite3
from loguru import logger

def create_connection():
    """Veritabanı bağlantısı oluşturur."""
    try:
        conn = sqlite3.connect('data/trendyol.db')
        return conn
    except sqlite3.Error as e:
        logger.error(f"Veritabanı bağlantı hatası: {e}")
        return None

def create_tables(conn):
    """Veritabanı tablolarını oluşturur."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        conn.commit()
        logger.info("Tablolar başarıyla oluşturuldu.")
    except sqlite3.Error as e:
        logger.error(f"Tablo oluşturma hatası: {e}")

def add_product(conn, url):
    """Veritabanına yeni bir ürün ekler."""
    try:
        cursor = conn.cursor()
        # URL'nin zaten var olup olmadığını kontrol et
        cursor.execute("SELECT id FROM products WHERE url = ?", (url,))
        data = cursor.fetchone()
        if data is None:
            cursor.execute("INSERT INTO products (url) VALUES (?)", (url,))
            conn.commit()
            logger.info(f"Ürün eklendi: {url}")
        else:
            logger.info(f"Ürün zaten mevcut: {url}")
    except sqlite3.Error as e:
        logger.error(f"Ürün ekleme hatası: {e}")

if __name__ == '__main__':
    conn = create_connection()
    if conn:
        create_tables(conn)
        # Test için bir ürün ekleyelim
        add_product(conn, "https://www.trendyol.com/ornek-urun-linki")
        conn.close()
