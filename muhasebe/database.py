"""
Muhasebe Sistemi - Veritabanı Modülü
SQLite veritabanı işlemleri ve tablo tanımlamaları
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple, Any

DATABASE_PATH = "muhasebe.db"


def get_connection():
    """Veritabanı bağlantısı oluştur"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Veritabanı tablolarını oluştur"""
    conn = get_connection()
    cursor = conn.cursor()

    # Müşteriler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            tax_number TEXT,
            notes TEXT,
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tedarikçiler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            tax_number TEXT,
            notes TEXT,
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ürünler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT DEFAULT 'Adet',
            buy_price REAL DEFAULT 0,
            sell_price REAL DEFAULT 0,
            stock_quantity REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            barcode TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Satışlar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            invoice_no TEXT,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total REAL DEFAULT 0,
            payment_type TEXT DEFAULT 'nakit',
            paid_amount REAL DEFAULT 0,
            notes TEXT,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Satış detayları tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL DEFAULT 1,
            unit_price REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Alımlar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            invoice_no TEXT,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total REAL DEFAULT 0,
            payment_type TEXT DEFAULT 'nakit',
            paid_amount REAL DEFAULT 0,
            notes TEXT,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    """)

    # Alım detayları tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL DEFAULT 1,
            unit_price REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Ödemeler tablosu (müşteri ödemeleri)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            supplier_id INTEGER,
            payment_type TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'nakit',
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reference_no TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    """)

    # Kasa hareketleri tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cash_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            category TEXT,
            amount REAL NOT NULL,
            description TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ayarlar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT
        )
    """)

    # Varsayılan ayarları ekle
    default_settings = [
        ('company_name', 'Şirket Adı', 'Şirket adı'),
        ('company_address', '', 'Şirket adresi'),
        ('company_phone', '', 'Şirket telefonu'),
        ('company_email', '', 'Şirket e-posta'),
        ('company_tax_number', '', 'Vergi numarası'),
        ('company_tax_office', '', 'Vergi dairesi'),
        ('currency', 'TL', 'Para birimi'),
        ('tax_rate', '18', 'Varsayılan KDV oranı'),
        ('auto_backup', '1', 'Otomatik yedekleme'),
        ('backup_path', 'backups', 'Yedek klasörü'),
        ('invoice_prefix', 'INV', 'Fatura ön eki'),
        ('next_invoice_no', '1', 'Sonraki fatura numarası'),
    ]

    for key, value, desc in default_settings:
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value, description)
            VALUES (?, ?, ?)
        """, (key, value, desc))

    conn.commit()
    conn.close()


# ==================== Müşteri İşlemleri ====================

def get_all_customers(search: str = "") -> List[sqlite3.Row]:
    """Tüm müşterileri getir"""
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute("""
            SELECT * FROM customers
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
            ORDER BY name
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM customers ORDER BY name")
    result = cursor.fetchall()
    conn.close()
    return result


def get_customer(customer_id: int) -> Optional[sqlite3.Row]:
    """Müşteri detayını getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def add_customer(name: str, phone: str = "", email: str = "",
                 address: str = "", tax_number: str = "", notes: str = "") -> int:
    """Yeni müşteri ekle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customers (name, phone, email, address, tax_number, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, phone, email, address, tax_number, notes))
    conn.commit()
    customer_id = cursor.lastrowid
    conn.close()
    return customer_id


def update_customer(customer_id: int, name: str, phone: str = "",
                    email: str = "", address: str = "",
                    tax_number: str = "", notes: str = "") -> bool:
    """Müşteri güncelle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customers
        SET name=?, phone=?, email=?, address=?, tax_number=?, notes=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (name, phone, email, address, tax_number, notes, customer_id))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def delete_customer(customer_id: int) -> bool:
    """Müşteri sil"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def update_customer_balance(customer_id: int, amount: float) -> bool:
    """Müşteri bakiyesini güncelle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customers SET balance = balance + ?, updated_at=CURRENT_TIMESTAMP
        WHERE id = ?
    """, (amount, customer_id))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def get_customers_with_debt() -> List[sqlite3.Row]:
    """Borçlu müşterileri getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM customers WHERE balance > 0 ORDER BY balance DESC
    """)
    result = cursor.fetchall()
    conn.close()
    return result


# ==================== Tedarikçi İşlemleri ====================

def get_all_suppliers(search: str = "") -> List[sqlite3.Row]:
    """Tüm tedarikçileri getir"""
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute("""
            SELECT * FROM suppliers
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
            ORDER BY name
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM suppliers ORDER BY name")
    result = cursor.fetchall()
    conn.close()
    return result


def get_supplier(supplier_id: int) -> Optional[sqlite3.Row]:
    """Tedarikçi detayını getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def add_supplier(name: str, phone: str = "", email: str = "",
                 address: str = "", tax_number: str = "", notes: str = "") -> int:
    """Yeni tedarikçi ekle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO suppliers (name, phone, email, address, tax_number, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, phone, email, address, tax_number, notes))
    conn.commit()
    supplier_id = cursor.lastrowid
    conn.close()
    return supplier_id


def update_supplier(supplier_id: int, name: str, phone: str = "",
                    email: str = "", address: str = "",
                    tax_number: str = "", notes: str = "") -> bool:
    """Tedarikçi güncelle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE suppliers
        SET name=?, phone=?, email=?, address=?, tax_number=?, notes=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (name, phone, email, address, tax_number, notes, supplier_id))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def delete_supplier(supplier_id: int) -> bool:
    """Tedarikçi sil"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def update_supplier_balance(supplier_id: int, amount: float) -> bool:
    """Tedarikçi bakiyesini güncelle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE suppliers SET balance = balance + ?, updated_at=CURRENT_TIMESTAMP
        WHERE id = ?
    """, (amount, supplier_id))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


# ==================== Ürün İşlemleri ====================

def get_all_products(search: str = "") -> List[sqlite3.Row]:
    """Tüm ürünleri getir"""
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute("""
            SELECT * FROM products
            WHERE name LIKE ? OR code LIKE ? OR barcode LIKE ?
            ORDER BY name
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM products ORDER BY name")
    result = cursor.fetchall()
    conn.close()
    return result


def get_product(product_id: int) -> Optional[sqlite3.Row]:
    """Ürün detayını getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def add_product(code: str, name: str, category: str = "", unit: str = "Adet",
                buy_price: float = 0, sell_price: float = 0,
                stock_quantity: float = 0, min_stock: float = 0,
                barcode: str = "", notes: str = "") -> int:
    """Yeni ürün ekle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (code, name, category, unit, buy_price, sell_price,
                             stock_quantity, min_stock, barcode, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, name, category, unit, buy_price, sell_price,
          stock_quantity, min_stock, barcode, notes))
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id


def update_product(product_id: int, code: str, name: str, category: str = "",
                   unit: str = "Adet", buy_price: float = 0, sell_price: float = 0,
                   stock_quantity: float = 0, min_stock: float = 0,
                   barcode: str = "", notes: str = "") -> bool:
    """Ürün güncelle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products
        SET code=?, name=?, category=?, unit=?, buy_price=?, sell_price=?,
            stock_quantity=?, min_stock=?, barcode=?, notes=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (code, name, category, unit, buy_price, sell_price,
          stock_quantity, min_stock, barcode, notes, product_id))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def delete_product(product_id: int) -> bool:
    """Ürün sil"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def update_product_stock(product_id: int, quantity: float) -> bool:
    """Ürün stokunu güncelle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products SET stock_quantity = stock_quantity + ?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id = ?
    """, (quantity, product_id))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def get_low_stock_products() -> List[sqlite3.Row]:
    """Düşük stoklu ürünleri getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM products
        WHERE stock_quantity <= min_stock AND min_stock > 0
        ORDER BY stock_quantity
    """)
    result = cursor.fetchall()
    conn.close()
    return result


# ==================== Satış İşlemleri ====================

def create_sale(customer_id: Optional[int], items: List[dict],
                payment_type: str = "nakit", paid_amount: float = 0,
                discount: float = 0, notes: str = "") -> int:
    """Yeni satış oluştur"""
    conn = get_connection()
    cursor = conn.cursor()

    # Fatura numarası oluştur
    cursor.execute("SELECT value FROM settings WHERE key = 'invoice_prefix'")
    prefix = cursor.fetchone()['value']
    cursor.execute("SELECT value FROM settings WHERE key = 'next_invoice_no'")
    next_no = int(cursor.fetchone()['value'])
    invoice_no = f"{prefix}-{next_no:06d}"

    # Toplamları hesapla
    subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
    tax_rate = float(get_setting('tax_rate') or 18)
    tax = (subtotal - discount) * tax_rate / 100
    total = subtotal - discount + tax

    # Satış kaydı oluştur
    cursor.execute("""
        INSERT INTO sales (customer_id, invoice_no, subtotal, discount, tax,
                          total, payment_type, paid_amount, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, invoice_no, subtotal, discount, tax, total,
          payment_type, paid_amount, notes))
    sale_id = cursor.lastrowid

    # Satış detaylarını ekle
    for item in items:
        item_total = item['quantity'] * item['unit_price'] - item.get('discount', 0)
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price,
                                   discount, total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sale_id, item['product_id'], item['quantity'], item['unit_price'],
              item.get('discount', 0), item_total))

        # Stok güncelle
        cursor.execute("""
            UPDATE products SET stock_quantity = stock_quantity - ?
            WHERE id = ?
        """, (item['quantity'], item['product_id']))

    # Veresiye ise müşteri bakiyesini güncelle
    if payment_type == 'veresiye' and customer_id:
        remaining = total - paid_amount
        cursor.execute("""
            UPDATE customers SET balance = balance + ? WHERE id = ?
        """, (remaining, customer_id))

    # Nakit ise kasa hareketi oluştur
    if payment_type in ['nakit', 'kredi_karti'] and paid_amount > 0:
        cursor.execute("""
            INSERT INTO cash_transactions (transaction_type, category, amount,
                                          description, reference_type, reference_id)
            VALUES ('giris', 'satis', ?, ?, 'sale', ?)
        """, (paid_amount, f"Satış: {invoice_no}", sale_id))

    # Fatura numarasını artır
    cursor.execute("""
        UPDATE settings SET value = ? WHERE key = 'next_invoice_no'
    """, (str(next_no + 1),))

    conn.commit()
    conn.close()
    return sale_id


def get_all_sales(start_date: str = "", end_date: str = "",
                  customer_id: int = None) -> List[sqlite3.Row]:
    """Tüm satışları getir"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT s.*, c.name as customer_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND DATE(s.sale_date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(s.sale_date) <= ?"
        params.append(end_date)
    if customer_id:
        query += " AND s.customer_id = ?"
        params.append(customer_id)

    query += " ORDER BY s.sale_date DESC"

    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def get_sale(sale_id: int) -> Optional[sqlite3.Row]:
    """Satış detayını getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, c.name as customer_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE s.id = ?
    """, (sale_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def get_sale_items(sale_id: int) -> List[sqlite3.Row]:
    """Satış kalemlerini getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT si.*, p.name as product_name, p.code as product_code
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    """, (sale_id,))
    result = cursor.fetchall()
    conn.close()
    return result


def delete_sale(sale_id: int) -> bool:
    """Satış sil ve stokları geri yükle"""
    conn = get_connection()
    cursor = conn.cursor()

    # Önce satış kalemlerini al
    cursor.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,))
    items = cursor.fetchall()

    # Satış bilgisini al
    cursor.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
    sale = cursor.fetchone()

    if sale:
        # Stokları geri yükle
        for item in items:
            cursor.execute("""
                UPDATE products SET stock_quantity = stock_quantity + ?
                WHERE id = ?
            """, (item['quantity'], item['product_id']))

        # Müşteri bakiyesini güncelle
        if sale['customer_id'] and sale['payment_type'] == 'veresiye':
            remaining = sale['total'] - sale['paid_amount']
            cursor.execute("""
                UPDATE customers SET balance = balance - ? WHERE id = ?
            """, (remaining, sale['customer_id']))

        # Satışı sil
        cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))

    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


# ==================== Alım İşlemleri ====================

def create_purchase(supplier_id: Optional[int], items: List[dict],
                    payment_type: str = "nakit", paid_amount: float = 0,
                    discount: float = 0, notes: str = "") -> int:
    """Yeni alım oluştur"""
    conn = get_connection()
    cursor = conn.cursor()

    # Fatura numarası oluştur
    invoice_no = f"PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Toplamları hesapla
    subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
    tax_rate = float(get_setting('tax_rate') or 18)
    tax = (subtotal - discount) * tax_rate / 100
    total = subtotal - discount + tax

    # Alım kaydı oluştur
    cursor.execute("""
        INSERT INTO purchases (supplier_id, invoice_no, subtotal, discount, tax,
                              total, payment_type, paid_amount, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (supplier_id, invoice_no, subtotal, discount, tax, total,
          payment_type, paid_amount, notes))
    purchase_id = cursor.lastrowid

    # Alım detaylarını ekle
    for item in items:
        item_total = item['quantity'] * item['unit_price'] - item.get('discount', 0)
        cursor.execute("""
            INSERT INTO purchase_items (purchase_id, product_id, quantity,
                                        unit_price, discount, total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (purchase_id, item['product_id'], item['quantity'],
              item['unit_price'], item.get('discount', 0), item_total))

        # Stok güncelle
        cursor.execute("""
            UPDATE products SET stock_quantity = stock_quantity + ?
            WHERE id = ?
        """, (item['quantity'], item['product_id']))

    # Veresiye ise tedarikçi bakiyesini güncelle
    if payment_type == 'veresiye' and supplier_id:
        remaining = total - paid_amount
        cursor.execute("""
            UPDATE suppliers SET balance = balance + ? WHERE id = ?
        """, (remaining, supplier_id))

    # Nakit ise kasa hareketi oluştur
    if payment_type in ['nakit', 'kredi_karti'] and paid_amount > 0:
        cursor.execute("""
            INSERT INTO cash_transactions (transaction_type, category, amount,
                                          description, reference_type, reference_id)
            VALUES ('cikis', 'alim', ?, ?, 'purchase', ?)
        """, (paid_amount, f"Alım: {invoice_no}", purchase_id))

    conn.commit()
    conn.close()
    return purchase_id


def get_all_purchases(start_date: str = "", end_date: str = "",
                      supplier_id: int = None) -> List[sqlite3.Row]:
    """Tüm alımları getir"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT p.*, s.name as supplier_name
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND DATE(p.purchase_date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(p.purchase_date) <= ?"
        params.append(end_date)
    if supplier_id:
        query += " AND p.supplier_id = ?"
        params.append(supplier_id)

    query += " ORDER BY p.purchase_date DESC"

    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def get_purchase(purchase_id: int) -> Optional[sqlite3.Row]:
    """Alım detayını getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, s.name as supplier_name
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.id = ?
    """, (purchase_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def get_purchase_items(purchase_id: int) -> List[sqlite3.Row]:
    """Alım kalemlerini getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pi.*, p.name as product_name, p.code as product_code
        FROM purchase_items pi
        JOIN products p ON pi.product_id = p.id
        WHERE pi.purchase_id = ?
    """, (purchase_id,))
    result = cursor.fetchall()
    conn.close()
    return result


# ==================== Ödeme İşlemleri ====================

def add_payment(customer_id: int = None, supplier_id: int = None,
                payment_type: str = "tahsilat", amount: float = 0,
                payment_method: str = "nakit", notes: str = "") -> int:
    """Ödeme ekle"""
    conn = get_connection()
    cursor = conn.cursor()

    reference_no = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    cursor.execute("""
        INSERT INTO payments (customer_id, supplier_id, payment_type, amount,
                             payment_method, reference_no, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, supplier_id, payment_type, amount,
          payment_method, reference_no, notes))
    payment_id = cursor.lastrowid

    # Bakiye güncelle
    if payment_type == 'tahsilat' and customer_id:
        cursor.execute("""
            UPDATE customers SET balance = balance - ? WHERE id = ?
        """, (amount, customer_id))
        # Kasa girişi
        cursor.execute("""
            INSERT INTO cash_transactions (transaction_type, category, amount,
                                          description, reference_type, reference_id)
            VALUES ('giris', 'tahsilat', ?, ?, 'payment', ?)
        """, (amount, f"Müşteri tahsilatı: {reference_no}", payment_id))

    elif payment_type == 'odeme' and supplier_id:
        cursor.execute("""
            UPDATE suppliers SET balance = balance - ? WHERE id = ?
        """, (amount, supplier_id))
        # Kasa çıkışı
        cursor.execute("""
            INSERT INTO cash_transactions (transaction_type, category, amount,
                                          description, reference_type, reference_id)
            VALUES ('cikis', 'odeme', ?, ?, 'payment', ?)
        """, (amount, f"Tedarikçi ödemesi: {reference_no}", payment_id))

    conn.commit()
    conn.close()
    return payment_id


def get_all_payments(customer_id: int = None, supplier_id: int = None,
                     start_date: str = "", end_date: str = "") -> List[sqlite3.Row]:
    """Tüm ödemeleri getir"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT p.*, c.name as customer_name, s.name as supplier_name
        FROM payments p
        LEFT JOIN customers c ON p.customer_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE 1=1
    """
    params = []

    if customer_id:
        query += " AND p.customer_id = ?"
        params.append(customer_id)
    if supplier_id:
        query += " AND p.supplier_id = ?"
        params.append(supplier_id)
    if start_date:
        query += " AND DATE(p.payment_date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(p.payment_date) <= ?"
        params.append(end_date)

    query += " ORDER BY p.payment_date DESC"

    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


# ==================== Kasa İşlemleri ====================

def add_cash_transaction(transaction_type: str, category: str,
                         amount: float, description: str = "") -> int:
    """Kasa hareketi ekle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cash_transactions (transaction_type, category, amount, description)
        VALUES (?, ?, ?, ?)
    """, (transaction_type, category, amount, description))
    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()
    return transaction_id


def get_cash_transactions(start_date: str = "", end_date: str = "",
                          transaction_type: str = "") -> List[sqlite3.Row]:
    """Kasa hareketlerini getir"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM cash_transactions WHERE 1=1"
    params = []

    if start_date:
        query += " AND DATE(transaction_date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(transaction_date) <= ?"
        params.append(end_date)
    if transaction_type:
        query += " AND transaction_type = ?"
        params.append(transaction_type)

    query += " ORDER BY transaction_date DESC"

    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def get_cash_balance() -> float:
    """Kasa bakiyesini hesapla"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN transaction_type = 'giris' THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN transaction_type = 'cikis' THEN amount ELSE 0 END), 0)
            as balance
        FROM cash_transactions
    """)
    result = cursor.fetchone()['balance']
    conn.close()
    return result or 0


# ==================== Ayarlar İşlemleri ====================

def get_setting(key: str) -> Optional[str]:
    """Ayar değerini getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result['value'] if result else None


def update_setting(key: str, value: str) -> bool:
    """Ayar güncelle"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    """, (key, value))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result


def get_all_settings() -> List[sqlite3.Row]:
    """Tüm ayarları getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings ORDER BY key")
    result = cursor.fetchall()
    conn.close()
    return result


# ==================== Raporlar ====================

def get_sales_summary(start_date: str = "", end_date: str = "") -> dict:
    """Satış özeti"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            COUNT(*) as total_count,
            COALESCE(SUM(total), 0) as total_amount,
            COALESCE(SUM(paid_amount), 0) as total_paid,
            COALESCE(SUM(total - paid_amount), 0) as total_debt
        FROM sales WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND DATE(sale_date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(sale_date) <= ?"
        params.append(end_date)

    cursor.execute(query, params)
    result = dict(cursor.fetchone())
    conn.close()
    return result


def get_purchases_summary(start_date: str = "", end_date: str = "") -> dict:
    """Alım özeti"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            COUNT(*) as total_count,
            COALESCE(SUM(total), 0) as total_amount,
            COALESCE(SUM(paid_amount), 0) as total_paid,
            COALESCE(SUM(total - paid_amount), 0) as total_debt
        FROM purchases WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND DATE(purchase_date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(purchase_date) <= ?"
        params.append(end_date)

    cursor.execute(query, params)
    result = dict(cursor.fetchone())
    conn.close()
    return result


def get_top_products(limit: int = 10, start_date: str = "",
                     end_date: str = "") -> List[sqlite3.Row]:
    """En çok satan ürünler"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT p.id, p.name, p.code,
               SUM(si.quantity) as total_quantity,
               SUM(si.total) as total_amount
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        JOIN sales s ON si.sale_id = s.id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND DATE(s.sale_date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(s.sale_date) <= ?"
        params.append(end_date)

    query += " GROUP BY p.id ORDER BY total_quantity DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def get_customer_sales(customer_id: int) -> List[sqlite3.Row]:
    """Müşterinin satışlarını getir"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sales
        WHERE customer_id = ?
        ORDER BY sale_date DESC
    """, (customer_id,))
    result = cursor.fetchall()
    conn.close()
    return result
