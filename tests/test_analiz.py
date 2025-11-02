# tests/test_analiz.py

import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import sys
import os
from datetime import datetime, timedelta

# src dizinini sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# analiz.py'yi import etmeden önce loguru'yu mock'la
# Bu, analiz.py'nin dosya sistemine log yazmasını engeller
mock_logger = MagicMock()
sys.modules['loguru'] = MagicMock()
sys.modules['loguru'].logger = mock_logger

import analiz
from database import create_tables

class TestAnaliz(unittest.TestCase):

    def setUp(self):
        """Her testten önce çalışan setup fonksiyonu."""
        self.conn = sqlite3.connect(":memory:")
        # DeprecationWarning'u önlemek için
        self.conn.execute("PRAGMA foreign_keys = ON")
        create_tables(self.conn)
        self.cursor = self.conn.cursor()

        # Test için bir ürün ekle
        self.test_url = "https://www.trendyol.com/test-urun"
        self.cursor.execute("INSERT INTO products (url) VALUES (?)", (self.test_url,))
        self.product_id = self.cursor.lastrowid
        self.conn.commit()

        # Mock logger'ı her testten önce sıfırla
        mock_logger.reset_mock()


    def tearDown(self):
        """Her testten sonra çalışan teardown fonksiyonu."""
        self.conn.close()

    def add_price_entry(self, product_id, price, days_ago):
        """Test için belirli bir tarihte fiyat verisi ekler."""
        timestamp = datetime.now() - timedelta(days=days_ago)
        self.cursor.execute(
            "INSERT INTO prices (product_id, price, timestamp) VALUES (?, ?, ?)",
            (product_id, price, timestamp)
        )
        self.conn.commit()

    def test_deal_found(self):
        """Fiyat düşüşü %25'ten fazla olduğunda firsat bulunmasını test eder."""
        # Geçmiş fiyatlar (ortalama 100 TL)
        self.add_price_entry(self.product_id, 110, 5)
        self.add_price_entry(self.product_id, 90, 4)

        # Son fiyat (ciddi bir düşüş)
        self.add_price_entry(self.product_id, 70, 0)

        # Analiz fonksiyonunu çalıştır
        with patch('analiz.get_db_connection', return_value=self.conn):
            analiz.analyze_prices()

        # logger.success'in çağrıldığını doğrula
        self.assertTrue(mock_logger.success.called)

        # logger.success'e yapılan tüm çağrıların argümanlarını al
        all_call_args = [call[0][0] for call in mock_logger.success.call_args_list]

        # Herhangi bir çağrının "FIRSAT BULUNDU!" içerip içermediğini kontrol et
        self.assertTrue(any("FIRSAT BULUNDU!" in arg for arg in all_call_args))

    def test_no_deal_found(self):
        """Fiyat düşüşü %25'ten az olduğunda firsat bulunmamasını test eder."""
        # Geçmiş fiyatlar (ortalama 100 TL)
        self.add_price_entry(self.product_id, 110, 5)
        self.add_price_entry(self.product_id, 90, 4)

        # Son fiyat (küçük bir düşüş)
        self.add_price_entry(self.product_id, 80, 0)

        with patch('analiz.get_db_connection', return_value=self.conn):
            analiz.analyze_prices()

        # logger.success'in çağrılmadığını doğrula
        self.assertFalse(mock_logger.success.called)

    def test_not_enough_history(self):
        """Yeterli fiyat geçmişi olmadığında analizin atlanmasını test eder."""
        # Sadece bir fiyat noktası var
        self.add_price_entry(self.product_id, 100, 1)

        with patch('analiz.get_db_connection', return_value=self.conn):
            analiz.analyze_prices()

        # logger.info'nun doğru mesajla çağrıldığını doğrula
        mock_logger.info.assert_any_call(f"Not enough price history for product {self.product_id} to analyze.")
        # Fırsat bulunmadığını doğrula
        self.assertFalse(mock_logger.success.called)


if __name__ == '__main__':
    # Loguru mock'unu kaldırmak için
    del sys.modules['loguru']
    unittest.main()
