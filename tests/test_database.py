# tests/test_database.py

import unittest
import sqlite3
import sys
import os

# src dizinini sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from database import create_tables, add_product

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Her testten önce çalışan setup fonksiyonu."""
        # Geçici bir in-memory veritabanı oluştur
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        create_tables(self.conn)

    def tearDown(self):
        """Her testten sonra çalışan teardown fonksiyonu."""
        self.conn.close()

    def test_create_tables(self):
        """Tabloların doğru oluşturulup oluşturulmadığını test eder."""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        self.assertIsNotNone(self.cursor.fetchone())

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        self.assertIsNotNone(self.cursor.fetchone())

    def test_add_product(self):
        """Ürün ekleme fonksiyonunu test eder."""
        test_url = "https://www.trendyol.com/test-urun"
        add_product(self.conn, test_url)

        self.cursor.execute("SELECT url FROM products WHERE url=?", (test_url,))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], test_url)

    def test_add_product_duplicate(self):
        """Aynı ürünün tekrar eklenmemesini test eder."""
        test_url = "https://www.trendyol.com/test-urun-duplicate"
        add_product(self.conn, test_url)
        add_product(self.conn, test_url)  # Tekrar eklemeyi dene

        self.cursor.execute("SELECT COUNT(id) FROM products WHERE url=?", (test_url,))
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()
