"""
Muhasebe Sistemi - Ana Uygulama
PyQt6 ile geliştirilmiş kapsamlı muhasebe yazılımı
"""

import sys
import os
import shutil
from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit, QMessageBox, QDialog,
    QFormLayout, QGroupBox, QTabWidget, QFrame, QSplitter,
    QFileDialog, QCheckBox, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QAction

# Veritabanı modülünü import et
import database as db

# Stil sabitleri
STYLE_SHEET = """
QMainWindow {
    background-color: #f5f6fa;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* Sidebar Stili */
#sidebar {
    background-color: #2c3e50;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #ecf0f1;
    border: none;
    padding: 15px 20px;
    text-align: left;
    font-size: 14px;
    border-left: 3px solid transparent;
}

#sidebar QPushButton:hover {
    background-color: #34495e;
    border-left: 3px solid #3498db;
}

#sidebar QPushButton:checked {
    background-color: #3498db;
    border-left: 3px solid #2980b9;
}

#sidebar QLabel {
    color: #ecf0f1;
    padding: 20px;
    font-size: 18px;
    font-weight: bold;
}

/* Ana içerik */
#content {
    background-color: #f5f6fa;
    padding: 20px;
}

/* Kartlar */
.card {
    background-color: white;
    border-radius: 10px;
    padding: 20px;
}

/* Butonlar */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton#btnSuccess {
    background-color: #27ae60;
}

QPushButton#btnSuccess:hover {
    background-color: #219a52;
}

QPushButton#btnDanger {
    background-color: #e74c3c;
}

QPushButton#btnDanger:hover {
    background-color: #c0392b;
}

QPushButton#btnWarning {
    background-color: #f39c12;
}

QPushButton#btnWarning:hover {
    background-color: #d68910;
}

/* Tablolar */
QTableWidget {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 5px;
    gridline-color: #ecf0f1;
}

QTableWidget::item {
    padding: 10px;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #34495e;
    color: white;
    padding: 10px;
    border: none;
    font-weight: bold;
}

/* Input alanları */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    padding: 10px;
    border: 2px solid #ddd;
    border-radius: 5px;
    background-color: white;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border-color: #3498db;
}

/* Grup kutusu */
QGroupBox {
    font-weight: bold;
    border: 2px solid #ddd;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 20px;
    padding: 0 10px;
    color: #2c3e50;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #ddd;
    border-radius: 5px;
    background-color: white;
}

QTabBar::tab {
    background-color: #ecf0f1;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QTabBar::tab:selected {
    background-color: #3498db;
    color: white;
}

/* ScrollBar */
QScrollBar:vertical {
    background-color: #f5f6fa;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}
"""


class DashboardWidget(QWidget):
    """Ana sayfa / Dashboard"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Başlık
        title = QLabel("Dashboard")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # Özet kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Kasa bakiyesi
        cash_balance = db.get_cash_balance()
        cards_layout.addWidget(self.create_card("Kasa Bakiyesi", f"{cash_balance:,.2f} TL", "#27ae60"))

        # Bugünkü satış
        today = datetime.now().strftime('%Y-%m-%d')
        sales_summary = db.get_sales_summary(today, today)
        cards_layout.addWidget(self.create_card("Bugünkü Satış", f"{sales_summary['total_amount']:,.2f} TL", "#3498db"))

        # Toplam borç (müşterilerden alacak)
        debtors = db.get_customers_with_debt()
        total_debt = sum(c['balance'] for c in debtors)
        cards_layout.addWidget(self.create_card("Toplam Alacak", f"{total_debt:,.2f} TL", "#e74c3c"))

        # Düşük stoklu ürünler
        low_stock = db.get_low_stock_products()
        cards_layout.addWidget(self.create_card("Düşük Stok", f"{len(low_stock)} Ürün", "#f39c12"))

        layout.addLayout(cards_layout)

        # Alt kısım - İki sütun
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        # Son satışlar
        sales_group = QGroupBox("Son Satışlar")
        sales_layout = QVBoxLayout(sales_group)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels(["Tarih", "Müşteri", "Tutar", "Durum"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sales_table.setMaximumHeight(300)
        sales_layout.addWidget(self.sales_table)
        bottom_layout.addWidget(sales_group)

        # Borçlu müşteriler
        debt_group = QGroupBox("Borçlu Müşteriler")
        debt_layout = QVBoxLayout(debt_group)
        self.debt_table = QTableWidget()
        self.debt_table.setColumnCount(3)
        self.debt_table.setHorizontalHeaderLabels(["Müşteri", "Telefon", "Borç"])
        self.debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.debt_table.setMaximumHeight(300)
        debt_layout.addWidget(self.debt_table)
        bottom_layout.addWidget(debt_group)

        layout.addLayout(bottom_layout)
        layout.addStretch()

        self.load_data()

    def create_card(self, title: str, value: str, color: str) -> QFrame:
        """Özet kartı oluştur"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid {color};
            }}
        """)
        card.setMinimumHeight(120)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)

        return card

    def load_data(self):
        """Verileri yükle"""
        # Son satışlar
        sales = db.get_all_sales()[:10]
        self.sales_table.setRowCount(len(sales))
        for i, sale in enumerate(sales):
            self.sales_table.setItem(i, 0, QTableWidgetItem(str(sale['sale_date'])[:10]))
            self.sales_table.setItem(i, 1, QTableWidgetItem(sale['customer_name'] or 'Perakende'))
            self.sales_table.setItem(i, 2, QTableWidgetItem(f"{sale['total']:,.2f} TL"))
            status = "Ödendi" if sale['paid_amount'] >= sale['total'] else "Veresiye"
            self.sales_table.setItem(i, 3, QTableWidgetItem(status))

        # Borçlu müşteriler
        debtors = db.get_customers_with_debt()[:10]
        self.debt_table.setRowCount(len(debtors))
        for i, customer in enumerate(debtors):
            self.debt_table.setItem(i, 0, QTableWidgetItem(customer['name']))
            self.debt_table.setItem(i, 1, QTableWidgetItem(customer['phone'] or '-'))
            self.debt_table.setItem(i, 2, QTableWidgetItem(f"{customer['balance']:,.2f} TL"))

    def refresh(self):
        """Verileri yenile"""
        self.load_data()


class CustomerDialog(QDialog):
    """Müşteri ekleme/düzenleme dialogu"""

    def __init__(self, parent=None, customer_id: int = None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.init_ui()
        if customer_id:
            self.load_customer()

    def init_ui(self):
        self.setWindowTitle("Müşteri Ekle" if not self.customer_id else "Müşteri Düzenle")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        layout.setSpacing(15)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Müşteri adı")
        layout.addRow("Ad Soyad:", self.name_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("05XX XXX XX XX")
        layout.addRow("Telefon:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("ornek@email.com")
        layout.addRow("E-posta:", self.email_edit)

        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setPlaceholderText("Adres bilgisi")
        layout.addRow("Adres:", self.address_edit)

        self.tax_edit = QLineEdit()
        self.tax_edit.setPlaceholderText("Vergi numarası")
        layout.addRow("Vergi No:", self.tax_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Notlar")
        layout.addRow("Notlar:", self.notes_edit)

        # Butonlar
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Kaydet")
        save_btn.setObjectName("btnSuccess")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setObjectName("btnDanger")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)

    def load_customer(self):
        """Müşteri bilgilerini yükle"""
        customer = db.get_customer(self.customer_id)
        if customer:
            self.name_edit.setText(customer['name'])
            self.phone_edit.setText(customer['phone'] or '')
            self.email_edit.setText(customer['email'] or '')
            self.address_edit.setText(customer['address'] or '')
            self.tax_edit.setText(customer['tax_number'] or '')
            self.notes_edit.setText(customer['notes'] or '')

    def save(self):
        """Müşteriyi kaydet"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Müşteri adı zorunludur!")
            return

        if self.customer_id:
            db.update_customer(
                self.customer_id, name,
                self.phone_edit.text().strip(),
                self.email_edit.text().strip(),
                self.address_edit.toPlainText().strip(),
                self.tax_edit.text().strip(),
                self.notes_edit.toPlainText().strip()
            )
        else:
            db.add_customer(
                name,
                self.phone_edit.text().strip(),
                self.email_edit.text().strip(),
                self.address_edit.toPlainText().strip(),
                self.tax_edit.text().strip(),
                self.notes_edit.toPlainText().strip()
            )

        self.accept()


class CustomersWidget(QWidget):
    """Müşteri yönetimi"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Başlık ve butonlar
        header = QHBoxLayout()

        title = QLabel("Müşteriler")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header.addWidget(title)

        header.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ara...")
        self.search_edit.setMaximumWidth(250)
        self.search_edit.textChanged.connect(self.load_data)
        header.addWidget(self.search_edit)

        add_btn = QPushButton("+ Yeni Müşteri")
        add_btn.setObjectName("btnSuccess")
        add_btn.clicked.connect(self.add_customer)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Ad Soyad", "Telefon", "E-posta", "Bakiye", "Düzenle", "Sil"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        """Müşterileri yükle"""
        search = self.search_edit.text().strip()
        customers = db.get_all_customers(search)

        self.table.setRowCount(len(customers))
        for i, customer in enumerate(customers):
            self.table.setItem(i, 0, QTableWidgetItem(str(customer['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(customer['name']))
            self.table.setItem(i, 2, QTableWidgetItem(customer['phone'] or '-'))
            self.table.setItem(i, 3, QTableWidgetItem(customer['email'] or '-'))

            balance_item = QTableWidgetItem(f"{customer['balance']:,.2f} TL")
            if customer['balance'] > 0:
                balance_item.setForeground(QColor('#e74c3c'))
            self.table.setItem(i, 4, balance_item)

            # Düzenle butonu
            edit_btn = QPushButton("Düzenle")
            edit_btn.setStyleSheet("padding: 5px;")
            edit_btn.clicked.connect(lambda checked, cid=customer['id']: self.edit_customer(cid))
            self.table.setCellWidget(i, 5, edit_btn)

            # Sil butonu
            del_btn = QPushButton("Sil")
            del_btn.setObjectName("btnDanger")
            del_btn.setStyleSheet("padding: 5px;")
            del_btn.clicked.connect(lambda checked, cid=customer['id']: self.delete_customer(cid))
            self.table.setCellWidget(i, 6, del_btn)

    def add_customer(self):
        """Yeni müşteri ekle"""
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_customer(self, customer_id: int):
        """Müşteri düzenle"""
        dialog = CustomerDialog(self, customer_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def delete_customer(self, customer_id: int):
        """Müşteri sil"""
        reply = QMessageBox.question(
            self, "Onay", "Bu müşteriyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_customer(customer_id)
            self.load_data()

    def refresh(self):
        self.load_data()


class SupplierDialog(QDialog):
    """Tedarikçi ekleme/düzenleme dialogu"""

    def __init__(self, parent=None, supplier_id: int = None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.init_ui()
        if supplier_id:
            self.load_supplier()

    def init_ui(self):
        self.setWindowTitle("Tedarikçi Ekle" if not self.supplier_id else "Tedarikçi Düzenle")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        layout.setSpacing(15)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Tedarikçi adı")
        layout.addRow("Ad:", self.name_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("05XX XXX XX XX")
        layout.addRow("Telefon:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("ornek@email.com")
        layout.addRow("E-posta:", self.email_edit)

        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setPlaceholderText("Adres bilgisi")
        layout.addRow("Adres:", self.address_edit)

        self.tax_edit = QLineEdit()
        self.tax_edit.setPlaceholderText("Vergi numarası")
        layout.addRow("Vergi No:", self.tax_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Notlar")
        layout.addRow("Notlar:", self.notes_edit)

        # Butonlar
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Kaydet")
        save_btn.setObjectName("btnSuccess")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setObjectName("btnDanger")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)

    def load_supplier(self):
        """Tedarikçi bilgilerini yükle"""
        supplier = db.get_supplier(self.supplier_id)
        if supplier:
            self.name_edit.setText(supplier['name'])
            self.phone_edit.setText(supplier['phone'] or '')
            self.email_edit.setText(supplier['email'] or '')
            self.address_edit.setText(supplier['address'] or '')
            self.tax_edit.setText(supplier['tax_number'] or '')
            self.notes_edit.setText(supplier['notes'] or '')

    def save(self):
        """Tedarikçiyi kaydet"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Tedarikçi adı zorunludur!")
            return

        if self.supplier_id:
            db.update_supplier(
                self.supplier_id, name,
                self.phone_edit.text().strip(),
                self.email_edit.text().strip(),
                self.address_edit.toPlainText().strip(),
                self.tax_edit.text().strip(),
                self.notes_edit.toPlainText().strip()
            )
        else:
            db.add_supplier(
                name,
                self.phone_edit.text().strip(),
                self.email_edit.text().strip(),
                self.address_edit.toPlainText().strip(),
                self.tax_edit.text().strip(),
                self.notes_edit.toPlainText().strip()
            )

        self.accept()


class SuppliersWidget(QWidget):
    """Tedarikçi yönetimi"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Başlık ve butonlar
        header = QHBoxLayout()

        title = QLabel("Tedarikçiler")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header.addWidget(title)

        header.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ara...")
        self.search_edit.setMaximumWidth(250)
        self.search_edit.textChanged.connect(self.load_data)
        header.addWidget(self.search_edit)

        add_btn = QPushButton("+ Yeni Tedarikçi")
        add_btn.setObjectName("btnSuccess")
        add_btn.clicked.connect(self.add_supplier)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Ad", "Telefon", "E-posta", "Bakiye", "Düzenle", "Sil"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        """Tedarikçileri yükle"""
        search = self.search_edit.text().strip()
        suppliers = db.get_all_suppliers(search)

        self.table.setRowCount(len(suppliers))
        for i, supplier in enumerate(suppliers):
            self.table.setItem(i, 0, QTableWidgetItem(str(supplier['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(supplier['name']))
            self.table.setItem(i, 2, QTableWidgetItem(supplier['phone'] or '-'))
            self.table.setItem(i, 3, QTableWidgetItem(supplier['email'] or '-'))

            balance_item = QTableWidgetItem(f"{supplier['balance']:,.2f} TL")
            if supplier['balance'] > 0:
                balance_item.setForeground(QColor('#e74c3c'))
            self.table.setItem(i, 4, balance_item)

            # Düzenle butonu
            edit_btn = QPushButton("Düzenle")
            edit_btn.setStyleSheet("padding: 5px;")
            edit_btn.clicked.connect(lambda checked, sid=supplier['id']: self.edit_supplier(sid))
            self.table.setCellWidget(i, 5, edit_btn)

            # Sil butonu
            del_btn = QPushButton("Sil")
            del_btn.setObjectName("btnDanger")
            del_btn.setStyleSheet("padding: 5px;")
            del_btn.clicked.connect(lambda checked, sid=supplier['id']: self.delete_supplier(sid))
            self.table.setCellWidget(i, 6, del_btn)

    def add_supplier(self):
        """Yeni tedarikçi ekle"""
        dialog = SupplierDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_supplier(self, supplier_id: int):
        """Tedarikçi düzenle"""
        dialog = SupplierDialog(self, supplier_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def delete_supplier(self, supplier_id: int):
        """Tedarikçi sil"""
        reply = QMessageBox.question(
            self, "Onay", "Bu tedarikçiyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_supplier(supplier_id)
            self.load_data()

    def refresh(self):
        self.load_data()


class ProductDialog(QDialog):
    """Ürün ekleme/düzenleme dialogu"""

    def __init__(self, parent=None, product_id: int = None):
        super().__init__(parent)
        self.product_id = product_id
        self.init_ui()
        if product_id:
            self.load_product()

    def init_ui(self):
        self.setWindowTitle("Ürün Ekle" if not self.product_id else "Ürün Düzenle")
        self.setMinimumWidth(450)

        layout = QFormLayout(self)
        layout.setSpacing(15)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Ürün kodu")
        layout.addRow("Kod:", self.code_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ürün adı")
        layout.addRow("Ad:", self.name_edit)

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Kategori")
        layout.addRow("Kategori:", self.category_edit)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Adet", "Kg", "Lt", "Mt", "Paket", "Kutu"])
        self.unit_combo.setEditable(True)
        layout.addRow("Birim:", self.unit_combo)

        self.buy_price_spin = QDoubleSpinBox()
        self.buy_price_spin.setRange(0, 9999999)
        self.buy_price_spin.setDecimals(2)
        self.buy_price_spin.setSuffix(" TL")
        layout.addRow("Alış Fiyatı:", self.buy_price_spin)

        self.sell_price_spin = QDoubleSpinBox()
        self.sell_price_spin.setRange(0, 9999999)
        self.sell_price_spin.setDecimals(2)
        self.sell_price_spin.setSuffix(" TL")
        layout.addRow("Satış Fiyatı:", self.sell_price_spin)

        self.stock_spin = QDoubleSpinBox()
        self.stock_spin.setRange(-99999, 999999)
        self.stock_spin.setDecimals(2)
        layout.addRow("Stok Miktarı:", self.stock_spin)

        self.min_stock_spin = QDoubleSpinBox()
        self.min_stock_spin.setRange(0, 99999)
        self.min_stock_spin.setDecimals(2)
        layout.addRow("Minimum Stok:", self.min_stock_spin)

        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText("Barkod")
        layout.addRow("Barkod:", self.barcode_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Notlar")
        layout.addRow("Notlar:", self.notes_edit)

        # Butonlar
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Kaydet")
        save_btn.setObjectName("btnSuccess")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setObjectName("btnDanger")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)

    def load_product(self):
        """Ürün bilgilerini yükle"""
        product = db.get_product(self.product_id)
        if product:
            self.code_edit.setText(product['code'] or '')
            self.name_edit.setText(product['name'])
            self.category_edit.setText(product['category'] or '')
            self.unit_combo.setCurrentText(product['unit'] or 'Adet')
            self.buy_price_spin.setValue(product['buy_price'] or 0)
            self.sell_price_spin.setValue(product['sell_price'] or 0)
            self.stock_spin.setValue(product['stock_quantity'] or 0)
            self.min_stock_spin.setValue(product['min_stock'] or 0)
            self.barcode_edit.setText(product['barcode'] or '')
            self.notes_edit.setText(product['notes'] or '')

    def save(self):
        """Ürünü kaydet"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Ürün adı zorunludur!")
            return

        code = self.code_edit.text().strip()
        if not code:
            code = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if self.product_id:
            db.update_product(
                self.product_id, code, name,
                self.category_edit.text().strip(),
                self.unit_combo.currentText(),
                self.buy_price_spin.value(),
                self.sell_price_spin.value(),
                self.stock_spin.value(),
                self.min_stock_spin.value(),
                self.barcode_edit.text().strip(),
                self.notes_edit.toPlainText().strip()
            )
        else:
            db.add_product(
                code, name,
                self.category_edit.text().strip(),
                self.unit_combo.currentText(),
                self.buy_price_spin.value(),
                self.sell_price_spin.value(),
                self.stock_spin.value(),
                self.min_stock_spin.value(),
                self.barcode_edit.text().strip(),
                self.notes_edit.toPlainText().strip()
            )

        self.accept()


class ProductsWidget(QWidget):
    """Ürün yönetimi"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Başlık ve butonlar
        header = QHBoxLayout()

        title = QLabel("Ürünler / Stok")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header.addWidget(title)

        header.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ara...")
        self.search_edit.setMaximumWidth(250)
        self.search_edit.textChanged.connect(self.load_data)
        header.addWidget(self.search_edit)

        add_btn = QPushButton("+ Yeni Ürün")
        add_btn.setObjectName("btnSuccess")
        add_btn.clicked.connect(self.add_product)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Kod", "Ad", "Kategori", "Birim", "Alış", "Satış", "Stok", "Düzenle", "Sil"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        """Ürünleri yükle"""
        search = self.search_edit.text().strip()
        products = db.get_all_products(search)

        self.table.setRowCount(len(products))
        for i, product in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(product['code'] or '-'))
            self.table.setItem(i, 1, QTableWidgetItem(product['name']))
            self.table.setItem(i, 2, QTableWidgetItem(product['category'] or '-'))
            self.table.setItem(i, 3, QTableWidgetItem(product['unit'] or 'Adet'))
            self.table.setItem(i, 4, QTableWidgetItem(f"{product['buy_price']:,.2f} TL"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{product['sell_price']:,.2f} TL"))

            stock_item = QTableWidgetItem(f"{product['stock_quantity']:,.2f}")
            if product['min_stock'] and product['stock_quantity'] <= product['min_stock']:
                stock_item.setForeground(QColor('#e74c3c'))
            self.table.setItem(i, 6, stock_item)

            # Düzenle butonu
            edit_btn = QPushButton("Düzenle")
            edit_btn.setStyleSheet("padding: 5px;")
            edit_btn.clicked.connect(lambda checked, pid=product['id']: self.edit_product(pid))
            self.table.setCellWidget(i, 7, edit_btn)

            # Sil butonu
            del_btn = QPushButton("Sil")
            del_btn.setObjectName("btnDanger")
            del_btn.setStyleSheet("padding: 5px;")
            del_btn.clicked.connect(lambda checked, pid=product['id']: self.delete_product(pid))
            self.table.setCellWidget(i, 8, del_btn)

    def add_product(self):
        """Yeni ürün ekle"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_product(self, product_id: int):
        """Ürün düzenle"""
        dialog = ProductDialog(self, product_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def delete_product(self, product_id: int):
        """Ürün sil"""
        reply = QMessageBox.question(
            self, "Onay", "Bu ürünü silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_product(product_id)
            self.load_data()

    def refresh(self):
        self.load_data()


class SalesWidget(QWidget):
    """Satış modülü - Sepetli satış"""

    def __init__(self):
        super().__init__()
        self.cart = []
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)

        # Sol panel - Ürün seçimi ve sepet
        left_panel = QVBoxLayout()

        title = QLabel("Satış")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        left_panel.addWidget(title)

        # Müşteri seçimi
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Müşteri:"))
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Perakende Satış", None)
        for customer in db.get_all_customers():
            self.customer_combo.addItem(customer['name'], customer['id'])
        customer_layout.addWidget(self.customer_combo)
        left_panel.addLayout(customer_layout)

        # Ürün arama ve ekleme
        product_group = QGroupBox("Ürün Ekle")
        product_layout = QVBoxLayout(product_group)

        search_layout = QHBoxLayout()
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Ürün ara (ad, kod, barkod)")
        self.product_search.textChanged.connect(self.search_products)
        search_layout.addWidget(self.product_search)
        product_layout.addLayout(search_layout)

        self.product_list = QTableWidget()
        self.product_list.setColumnCount(4)
        self.product_list.setHorizontalHeaderLabels(["Kod", "Ad", "Fiyat", "Stok"])
        self.product_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_list.setMaximumHeight(200)
        self.product_list.doubleClicked.connect(self.add_to_cart)
        product_layout.addWidget(self.product_list)

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Miktar:"))
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setDecimals(2)
        add_layout.addWidget(self.quantity_spin)

        add_btn = QPushButton("Sepete Ekle")
        add_btn.clicked.connect(self.add_to_cart)
        add_layout.addWidget(add_btn)
        product_layout.addLayout(add_layout)

        left_panel.addWidget(product_group)

        # Sepet
        cart_group = QGroupBox("Sepet")
        cart_layout = QVBoxLayout(cart_group)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(["Ürün", "Miktar", "Birim Fiyat", "Toplam", "İndirim", "Sil"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cart_layout.addWidget(self.cart_table)

        left_panel.addWidget(cart_group)

        layout.addLayout(left_panel, 2)

        # Sağ panel - Ödeme
        right_panel = QVBoxLayout()

        payment_group = QGroupBox("Ödeme")
        payment_layout = QFormLayout(payment_group)

        self.subtotal_label = QLabel("0.00 TL")
        self.subtotal_label.setFont(QFont('Segoe UI', 14))
        payment_layout.addRow("Ara Toplam:", self.subtotal_label)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 999999)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setSuffix(" TL")
        self.discount_spin.valueChanged.connect(self.update_totals)
        payment_layout.addRow("İndirim:", self.discount_spin)

        self.tax_label = QLabel("0.00 TL")
        self.tax_label.setFont(QFont('Segoe UI', 14))
        payment_layout.addRow("KDV:", self.tax_label)

        self.total_label = QLabel("0.00 TL")
        self.total_label.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #27ae60;")
        payment_layout.addRow("Toplam:", self.total_label)

        payment_layout.addRow(QLabel(""))  # Boşluk

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Nakit", "Kredi Kartı", "Veresiye"])
        self.payment_combo.currentTextChanged.connect(self.payment_type_changed)
        payment_layout.addRow("Ödeme Tipi:", self.payment_combo)

        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 9999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setSuffix(" TL")
        payment_layout.addRow("Ödenen:", self.paid_spin)

        self.remaining_label = QLabel("0.00 TL")
        self.remaining_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        payment_layout.addRow("Kalan Borç:", self.remaining_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Notlar...")
        payment_layout.addRow("Not:", self.notes_edit)

        right_panel.addWidget(payment_group)

        # Butonlar
        btn_layout = QVBoxLayout()

        complete_btn = QPushButton("Satışı Tamamla")
        complete_btn.setObjectName("btnSuccess")
        complete_btn.setMinimumHeight(50)
        complete_btn.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        complete_btn.clicked.connect(self.complete_sale)
        btn_layout.addWidget(complete_btn)

        clear_btn = QPushButton("Sepeti Temizle")
        clear_btn.setObjectName("btnDanger")
        clear_btn.clicked.connect(self.clear_cart)
        btn_layout.addWidget(clear_btn)

        right_panel.addLayout(btn_layout)
        right_panel.addStretch()

        layout.addLayout(right_panel, 1)

        self.search_products()

    def search_products(self):
        """Ürün ara"""
        search = self.product_search.text().strip()
        products = db.get_all_products(search)

        self.product_list.setRowCount(len(products))
        for i, product in enumerate(products):
            self.product_list.setItem(i, 0, QTableWidgetItem(product['code'] or '-'))
            self.product_list.setItem(i, 1, QTableWidgetItem(product['name']))
            self.product_list.setItem(i, 2, QTableWidgetItem(f"{product['sell_price']:,.2f} TL"))
            self.product_list.setItem(i, 3, QTableWidgetItem(str(product['stock_quantity'])))

    def add_to_cart(self):
        """Sepete ürün ekle"""
        row = self.product_list.currentRow()
        if row < 0:
            return

        search = self.product_search.text().strip()
        products = db.get_all_products(search)
        if row >= len(products):
            return

        product = products[row]
        quantity = self.quantity_spin.value()

        # Sepette aynı ürün var mı kontrol et
        for item in self.cart:
            if item['product_id'] == product['id']:
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['unit_price']
                self.update_cart_table()
                return

        self.cart.append({
            'product_id': product['id'],
            'product_name': product['name'],
            'quantity': quantity,
            'unit_price': product['sell_price'],
            'discount': 0,
            'total': quantity * product['sell_price']
        })

        self.update_cart_table()

    def update_cart_table(self):
        """Sepet tablosunu güncelle"""
        self.cart_table.setRowCount(len(self.cart))
        for i, item in enumerate(self.cart):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(f"{item['quantity']:.2f}"))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"{item['unit_price']:.2f} TL"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{item['total']:.2f} TL"))
            self.cart_table.setItem(i, 4, QTableWidgetItem(f"{item['discount']:.2f} TL"))

            del_btn = QPushButton("Sil")
            del_btn.setObjectName("btnDanger")
            del_btn.setStyleSheet("padding: 3px;")
            del_btn.clicked.connect(lambda checked, idx=i: self.remove_from_cart(idx))
            self.cart_table.setCellWidget(i, 5, del_btn)

        self.update_totals()

    def remove_from_cart(self, index: int):
        """Sepetten ürün çıkar"""
        if 0 <= index < len(self.cart):
            del self.cart[index]
            self.update_cart_table()

    def update_totals(self):
        """Toplamları güncelle"""
        subtotal = sum(item['total'] - item['discount'] for item in self.cart)
        discount = self.discount_spin.value()
        tax_rate = float(db.get_setting('tax_rate') or 18)
        tax = (subtotal - discount) * tax_rate / 100
        total = subtotal - discount + tax

        self.subtotal_label.setText(f"{subtotal:,.2f} TL")
        self.tax_label.setText(f"{tax:,.2f} TL")
        self.total_label.setText(f"{total:,.2f} TL")

        paid = self.paid_spin.value()
        remaining = max(0, total - paid)
        self.remaining_label.setText(f"{remaining:,.2f} TL")

    def payment_type_changed(self, text: str):
        """Ödeme tipi değişti"""
        if text == "Nakit" or text == "Kredi Kartı":
            subtotal = sum(item['total'] - item['discount'] for item in self.cart)
            discount = self.discount_spin.value()
            tax_rate = float(db.get_setting('tax_rate') or 18)
            tax = (subtotal - discount) * tax_rate / 100
            total = subtotal - discount + tax
            self.paid_spin.setValue(total)
        else:
            self.paid_spin.setValue(0)
        self.update_totals()

    def clear_cart(self):
        """Sepeti temizle"""
        self.cart = []
        self.update_cart_table()
        self.discount_spin.setValue(0)
        self.paid_spin.setValue(0)
        self.notes_edit.clear()

    def complete_sale(self):
        """Satışı tamamla"""
        if not self.cart:
            QMessageBox.warning(self, "Hata", "Sepet boş!")
            return

        customer_id = self.customer_combo.currentData()
        payment_type = self.payment_combo.currentText().lower().replace(" ", "_")
        if payment_type == "kredi_kartı":
            payment_type = "kredi_karti"

        # Veresiye ise müşteri seçilmeli
        if payment_type == "veresiye" and not customer_id:
            QMessageBox.warning(self, "Hata", "Veresiye satış için müşteri seçmelisiniz!")
            return

        try:
            sale_id = db.create_sale(
                customer_id=customer_id,
                items=self.cart,
                payment_type=payment_type,
                paid_amount=self.paid_spin.value(),
                discount=self.discount_spin.value(),
                notes=self.notes_edit.toPlainText().strip()
            )

            QMessageBox.information(self, "Başarılı", f"Satış tamamlandı! (#{sale_id})")
            self.clear_cart()
            self.search_products()  # Stok güncellendi

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Satış oluşturulamadı: {str(e)}")

    def refresh(self):
        """Verileri yenile"""
        # Müşteri listesini güncelle
        self.customer_combo.clear()
        self.customer_combo.addItem("Perakende Satış", None)
        for customer in db.get_all_customers():
            self.customer_combo.addItem(customer['name'], customer['id'])
        self.search_products()


class PurchasesWidget(QWidget):
    """Alım modülü - Sepetli alım"""

    def __init__(self):
        super().__init__()
        self.cart = []
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)

        # Sol panel - Ürün seçimi ve sepet
        left_panel = QVBoxLayout()

        title = QLabel("Alım")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        left_panel.addWidget(title)

        # Tedarikçi seçimi
        supplier_layout = QHBoxLayout()
        supplier_layout.addWidget(QLabel("Tedarikçi:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("Tedarikçi Seçin", None)
        for supplier in db.get_all_suppliers():
            self.supplier_combo.addItem(supplier['name'], supplier['id'])
        supplier_layout.addWidget(self.supplier_combo)
        left_panel.addLayout(supplier_layout)

        # Ürün arama ve ekleme
        product_group = QGroupBox("Ürün Ekle")
        product_layout = QVBoxLayout(product_group)

        search_layout = QHBoxLayout()
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Ürün ara (ad, kod, barkod)")
        self.product_search.textChanged.connect(self.search_products)
        search_layout.addWidget(self.product_search)
        product_layout.addLayout(search_layout)

        self.product_list = QTableWidget()
        self.product_list.setColumnCount(4)
        self.product_list.setHorizontalHeaderLabels(["Kod", "Ad", "Alış Fiyatı", "Stok"])
        self.product_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_list.setMaximumHeight(200)
        self.product_list.doubleClicked.connect(self.add_to_cart)
        product_layout.addWidget(self.product_list)

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Miktar:"))
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setDecimals(2)
        add_layout.addWidget(self.quantity_spin)

        add_layout.addWidget(QLabel("Fiyat:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 9999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" TL")
        add_layout.addWidget(self.price_spin)

        add_btn = QPushButton("Sepete Ekle")
        add_btn.clicked.connect(self.add_to_cart)
        add_layout.addWidget(add_btn)
        product_layout.addLayout(add_layout)

        left_panel.addWidget(product_group)

        # Sepet
        cart_group = QGroupBox("Sepet")
        cart_layout = QVBoxLayout(cart_group)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Ürün", "Miktar", "Birim Fiyat", "Toplam", "Sil"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cart_layout.addWidget(self.cart_table)

        left_panel.addWidget(cart_group)

        layout.addLayout(left_panel, 2)

        # Sağ panel - Ödeme
        right_panel = QVBoxLayout()

        payment_group = QGroupBox("Ödeme")
        payment_layout = QFormLayout(payment_group)

        self.subtotal_label = QLabel("0.00 TL")
        self.subtotal_label.setFont(QFont('Segoe UI', 14))
        payment_layout.addRow("Ara Toplam:", self.subtotal_label)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 999999)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setSuffix(" TL")
        self.discount_spin.valueChanged.connect(self.update_totals)
        payment_layout.addRow("İndirim:", self.discount_spin)

        self.tax_label = QLabel("0.00 TL")
        self.tax_label.setFont(QFont('Segoe UI', 14))
        payment_layout.addRow("KDV:", self.tax_label)

        self.total_label = QLabel("0.00 TL")
        self.total_label.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #e74c3c;")
        payment_layout.addRow("Toplam:", self.total_label)

        payment_layout.addRow(QLabel(""))

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Nakit", "Kredi Kartı", "Veresiye"])
        self.payment_combo.currentTextChanged.connect(self.payment_type_changed)
        payment_layout.addRow("Ödeme Tipi:", self.payment_combo)

        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 9999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setSuffix(" TL")
        payment_layout.addRow("Ödenen:", self.paid_spin)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Notlar...")
        payment_layout.addRow("Not:", self.notes_edit)

        right_panel.addWidget(payment_group)

        # Butonlar
        btn_layout = QVBoxLayout()

        complete_btn = QPushButton("Alımı Tamamla")
        complete_btn.setObjectName("btnSuccess")
        complete_btn.setMinimumHeight(50)
        complete_btn.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        complete_btn.clicked.connect(self.complete_purchase)
        btn_layout.addWidget(complete_btn)

        clear_btn = QPushButton("Sepeti Temizle")
        clear_btn.setObjectName("btnDanger")
        clear_btn.clicked.connect(self.clear_cart)
        btn_layout.addWidget(clear_btn)

        right_panel.addLayout(btn_layout)
        right_panel.addStretch()

        layout.addLayout(right_panel, 1)

        self.search_products()

    def search_products(self):
        """Ürün ara"""
        search = self.product_search.text().strip()
        products = db.get_all_products(search)

        self.product_list.setRowCount(len(products))
        for i, product in enumerate(products):
            self.product_list.setItem(i, 0, QTableWidgetItem(product['code'] or '-'))
            self.product_list.setItem(i, 1, QTableWidgetItem(product['name']))
            self.product_list.setItem(i, 2, QTableWidgetItem(f"{product['buy_price']:,.2f} TL"))
            self.product_list.setItem(i, 3, QTableWidgetItem(str(product['stock_quantity'])))

        # İlk ürünün alış fiyatını göster
        if products:
            self.price_spin.setValue(products[0]['buy_price'])

    def add_to_cart(self):
        """Sepete ürün ekle"""
        row = self.product_list.currentRow()
        if row < 0:
            return

        search = self.product_search.text().strip()
        products = db.get_all_products(search)
        if row >= len(products):
            return

        product = products[row]
        quantity = self.quantity_spin.value()
        unit_price = self.price_spin.value()

        # Sepette aynı ürün var mı kontrol et
        for item in self.cart:
            if item['product_id'] == product['id']:
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['unit_price']
                self.update_cart_table()
                return

        self.cart.append({
            'product_id': product['id'],
            'product_name': product['name'],
            'quantity': quantity,
            'unit_price': unit_price,
            'discount': 0,
            'total': quantity * unit_price
        })

        self.update_cart_table()

    def update_cart_table(self):
        """Sepet tablosunu güncelle"""
        self.cart_table.setRowCount(len(self.cart))
        for i, item in enumerate(self.cart):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(f"{item['quantity']:.2f}"))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"{item['unit_price']:.2f} TL"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{item['total']:.2f} TL"))

            del_btn = QPushButton("Sil")
            del_btn.setObjectName("btnDanger")
            del_btn.setStyleSheet("padding: 3px;")
            del_btn.clicked.connect(lambda checked, idx=i: self.remove_from_cart(idx))
            self.cart_table.setCellWidget(i, 4, del_btn)

        self.update_totals()

    def remove_from_cart(self, index: int):
        """Sepetten ürün çıkar"""
        if 0 <= index < len(self.cart):
            del self.cart[index]
            self.update_cart_table()

    def update_totals(self):
        """Toplamları güncelle"""
        subtotal = sum(item['total'] for item in self.cart)
        discount = self.discount_spin.value()
        tax_rate = float(db.get_setting('tax_rate') or 18)
        tax = (subtotal - discount) * tax_rate / 100
        total = subtotal - discount + tax

        self.subtotal_label.setText(f"{subtotal:,.2f} TL")
        self.tax_label.setText(f"{tax:,.2f} TL")
        self.total_label.setText(f"{total:,.2f} TL")

    def payment_type_changed(self, text: str):
        """Ödeme tipi değişti"""
        if text == "Nakit" or text == "Kredi Kartı":
            subtotal = sum(item['total'] for item in self.cart)
            discount = self.discount_spin.value()
            tax_rate = float(db.get_setting('tax_rate') or 18)
            tax = (subtotal - discount) * tax_rate / 100
            total = subtotal - discount + tax
            self.paid_spin.setValue(total)
        else:
            self.paid_spin.setValue(0)

    def clear_cart(self):
        """Sepeti temizle"""
        self.cart = []
        self.update_cart_table()
        self.discount_spin.setValue(0)
        self.paid_spin.setValue(0)
        self.notes_edit.clear()

    def complete_purchase(self):
        """Alımı tamamla"""
        if not self.cart:
            QMessageBox.warning(self, "Hata", "Sepet boş!")
            return

        supplier_id = self.supplier_combo.currentData()
        payment_type = self.payment_combo.currentText().lower().replace(" ", "_")
        if payment_type == "kredi_kartı":
            payment_type = "kredi_karti"

        try:
            purchase_id = db.create_purchase(
                supplier_id=supplier_id,
                items=self.cart,
                payment_type=payment_type,
                paid_amount=self.paid_spin.value(),
                discount=self.discount_spin.value(),
                notes=self.notes_edit.toPlainText().strip()
            )

            QMessageBox.information(self, "Başarılı", f"Alım tamamlandı! (#{purchase_id})")
            self.clear_cart()
            self.search_products()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Alım oluşturulamadı: {str(e)}")

    def refresh(self):
        """Verileri yenile"""
        self.supplier_combo.clear()
        self.supplier_combo.addItem("Tedarikçi Seçin", None)
        for supplier in db.get_all_suppliers():
            self.supplier_combo.addItem(supplier['name'], supplier['id'])
        self.search_products()


class PaymentsWidget(QWidget):
    """Ödeme/Tahsilat modülü"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Ödemeler / Tahsilatlar")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Üst panel - Yeni ödeme/tahsilat
        top_layout = QHBoxLayout()

        # Müşteri tahsilatı
        customer_group = QGroupBox("Müşteri Tahsilatı")
        customer_layout = QFormLayout(customer_group)

        self.customer_combo = QComboBox()
        self.load_customers()
        customer_layout.addRow("Müşteri:", self.customer_combo)

        self.customer_amount = QDoubleSpinBox()
        self.customer_amount.setRange(0, 9999999)
        self.customer_amount.setDecimals(2)
        self.customer_amount.setSuffix(" TL")
        customer_layout.addRow("Tutar:", self.customer_amount)

        self.customer_method = QComboBox()
        self.customer_method.addItems(["Nakit", "Havale/EFT", "Kredi Kartı"])
        customer_layout.addRow("Yöntem:", self.customer_method)

        self.customer_notes = QLineEdit()
        self.customer_notes.setPlaceholderText("Not")
        customer_layout.addRow("Not:", self.customer_notes)

        customer_btn = QPushButton("Tahsilat Al")
        customer_btn.setObjectName("btnSuccess")
        customer_btn.clicked.connect(self.add_customer_payment)
        customer_layout.addRow(customer_btn)

        top_layout.addWidget(customer_group)

        # Tedarikçi ödemesi
        supplier_group = QGroupBox("Tedarikçi Ödemesi")
        supplier_layout = QFormLayout(supplier_group)

        self.supplier_combo = QComboBox()
        self.load_suppliers()
        supplier_layout.addRow("Tedarikçi:", self.supplier_combo)

        self.supplier_amount = QDoubleSpinBox()
        self.supplier_amount.setRange(0, 9999999)
        self.supplier_amount.setDecimals(2)
        self.supplier_amount.setSuffix(" TL")
        supplier_layout.addRow("Tutar:", self.supplier_amount)

        self.supplier_method = QComboBox()
        self.supplier_method.addItems(["Nakit", "Havale/EFT", "Kredi Kartı"])
        supplier_layout.addRow("Yöntem:", self.supplier_method)

        self.supplier_notes = QLineEdit()
        self.supplier_notes.setPlaceholderText("Not")
        supplier_layout.addRow("Not:", self.supplier_notes)

        supplier_btn = QPushButton("Ödeme Yap")
        supplier_btn.setObjectName("btnWarning")
        supplier_btn.clicked.connect(self.add_supplier_payment)
        supplier_layout.addRow(supplier_btn)

        top_layout.addWidget(supplier_group)

        layout.addLayout(top_layout)

        # Ödeme listesi
        list_group = QGroupBox("Ödeme Geçmişi")
        list_layout = QVBoxLayout(list_group)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tarih:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("-"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)

        filter_btn = QPushButton("Filtrele")
        filter_btn.clicked.connect(self.load_payments)
        filter_layout.addWidget(filter_btn)
        filter_layout.addStretch()

        list_layout.addLayout(filter_layout)

        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels([
            "Tarih", "Tip", "Müşteri/Tedarikçi", "Yöntem", "Tutar", "Not"
        ])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_layout.addWidget(self.payments_table)

        layout.addWidget(list_group)

        self.load_payments()

    def load_customers(self):
        """Müşterileri yükle"""
        self.customer_combo.clear()
        for customer in db.get_customers_with_debt():
            self.customer_combo.addItem(
                f"{customer['name']} ({customer['balance']:,.2f} TL)",
                customer['id']
            )

    def load_suppliers(self):
        """Tedarikçileri yükle"""
        self.supplier_combo.clear()
        for supplier in db.get_all_suppliers():
            if supplier['balance'] > 0:
                self.supplier_combo.addItem(
                    f"{supplier['name']} ({supplier['balance']:,.2f} TL)",
                    supplier['id']
                )

    def load_payments(self):
        """Ödemeleri yükle"""
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        payments = db.get_all_payments(start_date=start, end_date=end)

        self.payments_table.setRowCount(len(payments))
        for i, payment in enumerate(payments):
            self.payments_table.setItem(i, 0, QTableWidgetItem(str(payment['payment_date'])[:10]))

            payment_type = "Tahsilat" if payment['payment_type'] == 'tahsilat' else "Ödeme"
            type_item = QTableWidgetItem(payment_type)
            if payment_type == "Tahsilat":
                type_item.setForeground(QColor('#27ae60'))
            else:
                type_item.setForeground(QColor('#e74c3c'))
            self.payments_table.setItem(i, 1, type_item)

            name = payment['customer_name'] or payment['supplier_name'] or '-'
            self.payments_table.setItem(i, 2, QTableWidgetItem(name))
            self.payments_table.setItem(i, 3, QTableWidgetItem(payment['payment_method']))
            self.payments_table.setItem(i, 4, QTableWidgetItem(f"{payment['amount']:,.2f} TL"))
            self.payments_table.setItem(i, 5, QTableWidgetItem(payment['notes'] or '-'))

    def add_customer_payment(self):
        """Müşteri tahsilatı ekle"""
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            QMessageBox.warning(self, "Hata", "Müşteri seçin!")
            return

        amount = self.customer_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Hata", "Tutar girmelisiniz!")
            return

        db.add_payment(
            customer_id=customer_id,
            payment_type='tahsilat',
            amount=amount,
            payment_method=self.customer_method.currentText().lower(),
            notes=self.customer_notes.text().strip()
        )

        QMessageBox.information(self, "Başarılı", "Tahsilat kaydedildi!")
        self.customer_amount.setValue(0)
        self.customer_notes.clear()
        self.load_customers()
        self.load_payments()

    def add_supplier_payment(self):
        """Tedarikçi ödemesi ekle"""
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            QMessageBox.warning(self, "Hata", "Tedarikçi seçin!")
            return

        amount = self.supplier_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Hata", "Tutar girmelisiniz!")
            return

        db.add_payment(
            supplier_id=supplier_id,
            payment_type='odeme',
            amount=amount,
            payment_method=self.supplier_method.currentText().lower(),
            notes=self.supplier_notes.text().strip()
        )

        QMessageBox.information(self, "Başarılı", "Ödeme kaydedildi!")
        self.supplier_amount.setValue(0)
        self.supplier_notes.clear()
        self.load_suppliers()
        self.load_payments()

    def refresh(self):
        self.load_customers()
        self.load_suppliers()
        self.load_payments()


class CashWidget(QWidget):
    """Kasa modülü"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Başlık ve bakiye
        header = QHBoxLayout()

        title = QLabel("Kasa")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header.addWidget(title)

        header.addStretch()

        balance = db.get_cash_balance()
        self.balance_label = QLabel(f"Bakiye: {balance:,.2f} TL")
        self.balance_label.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        self.balance_label.setStyleSheet("color: #27ae60;")
        header.addWidget(self.balance_label)

        layout.addLayout(header)

        # İşlem ekleme
        add_group = QGroupBox("Yeni İşlem")
        add_layout = QHBoxLayout(add_group)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Giriş", "Çıkış"])
        add_layout.addWidget(QLabel("Tip:"))
        add_layout.addWidget(self.type_combo)

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Kategori")
        add_layout.addWidget(QLabel("Kategori:"))
        add_layout.addWidget(self.category_edit)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 9999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(" TL")
        add_layout.addWidget(QLabel("Tutar:"))
        add_layout.addWidget(self.amount_spin)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Açıklama")
        add_layout.addWidget(QLabel("Açıklama:"))
        add_layout.addWidget(self.desc_edit)

        add_btn = QPushButton("Ekle")
        add_btn.setObjectName("btnSuccess")
        add_btn.clicked.connect(self.add_transaction)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_group)

        # Filtre
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tarih:"))

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("-"))

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)

        self.filter_type = QComboBox()
        self.filter_type.addItems(["Tümü", "Giriş", "Çıkış"])
        filter_layout.addWidget(self.filter_type)

        filter_btn = QPushButton("Filtrele")
        filter_btn.clicked.connect(self.load_transactions)
        filter_layout.addWidget(filter_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # İşlem listesi
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Tarih", "Tip", "Kategori", "Açıklama", "Tutar"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.load_transactions()

    def load_transactions(self):
        """İşlemleri yükle"""
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        type_filter = ""
        if self.filter_type.currentText() == "Giriş":
            type_filter = "giris"
        elif self.filter_type.currentText() == "Çıkış":
            type_filter = "cikis"

        transactions = db.get_cash_transactions(start, end, type_filter)

        self.table.setRowCount(len(transactions))
        for i, trans in enumerate(transactions):
            self.table.setItem(i, 0, QTableWidgetItem(str(trans['transaction_date'])[:10]))

            type_text = "Giriş" if trans['transaction_type'] == 'giris' else "Çıkış"
            type_item = QTableWidgetItem(type_text)
            if type_text == "Giriş":
                type_item.setForeground(QColor('#27ae60'))
            else:
                type_item.setForeground(QColor('#e74c3c'))
            self.table.setItem(i, 1, type_item)

            self.table.setItem(i, 2, QTableWidgetItem(trans['category'] or '-'))
            self.table.setItem(i, 3, QTableWidgetItem(trans['description'] or '-'))

            amount_item = QTableWidgetItem(f"{trans['amount']:,.2f} TL")
            if trans['transaction_type'] == 'giris':
                amount_item.setForeground(QColor('#27ae60'))
            else:
                amount_item.setForeground(QColor('#e74c3c'))
            self.table.setItem(i, 4, amount_item)

        # Bakiyeyi güncelle
        balance = db.get_cash_balance()
        self.balance_label.setText(f"Bakiye: {balance:,.2f} TL")

    def add_transaction(self):
        """İşlem ekle"""
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Hata", "Tutar girmelisiniz!")
            return

        trans_type = "giris" if self.type_combo.currentText() == "Giriş" else "cikis"

        db.add_cash_transaction(
            trans_type,
            self.category_edit.text().strip(),
            amount,
            self.desc_edit.text().strip()
        )

        QMessageBox.information(self, "Başarılı", "İşlem kaydedildi!")
        self.amount_spin.setValue(0)
        self.category_edit.clear()
        self.desc_edit.clear()
        self.load_transactions()

    def refresh(self):
        self.load_transactions()


class ReportsWidget(QWidget):
    """Raporlar ve Analiz modülü"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Raporlar ve Analiz")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Tarih filtresi
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tarih Aralığı:"))

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("-"))

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)

        filter_btn = QPushButton("Raporu Güncelle")
        filter_btn.clicked.connect(self.load_reports)
        filter_layout.addWidget(filter_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Özet kartlar
        cards_layout = QHBoxLayout()

        self.sales_card = self.create_summary_card("Satışlar", "0 TL", "#3498db")
        cards_layout.addWidget(self.sales_card)

        self.purchases_card = self.create_summary_card("Alımlar", "0 TL", "#e74c3c")
        cards_layout.addWidget(self.purchases_card)

        self.profit_card = self.create_summary_card("Kar", "0 TL", "#27ae60")
        cards_layout.addWidget(self.profit_card)

        self.debt_card = self.create_summary_card("Alacaklar", "0 TL", "#f39c12")
        cards_layout.addWidget(self.debt_card)

        layout.addLayout(cards_layout)

        # Detaylı raporlar
        tabs = QTabWidget()

        # En çok satan ürünler
        top_products_widget = QWidget()
        top_layout = QVBoxLayout(top_products_widget)
        self.top_products_table = QTableWidget()
        self.top_products_table.setColumnCount(4)
        self.top_products_table.setHorizontalHeaderLabels(["Ürün", "Kod", "Satış Adedi", "Toplam Tutar"])
        self.top_products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        top_layout.addWidget(self.top_products_table)
        tabs.addTab(top_products_widget, "En Çok Satan Ürünler")

        # Borçlu müşteriler
        debtors_widget = QWidget()
        debtors_layout = QVBoxLayout(debtors_widget)

        debtors_header = QHBoxLayout()
        self.only_debtors_check = QCheckBox("Sadece Borçlu Müşteriler")
        self.only_debtors_check.setChecked(True)
        self.only_debtors_check.stateChanged.connect(self.load_debtors)
        debtors_header.addWidget(self.only_debtors_check)
        debtors_header.addStretch()
        debtors_layout.addLayout(debtors_header)

        self.debtors_table = QTableWidget()
        self.debtors_table.setColumnCount(4)
        self.debtors_table.setHorizontalHeaderLabels(["Müşteri", "Telefon", "Adres", "Borç"])
        self.debtors_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        debtors_layout.addWidget(self.debtors_table)
        tabs.addTab(debtors_widget, "Müşteri Borçları")

        # Satış listesi
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels([
            "Fatura No", "Tarih", "Müşteri", "Toplam", "Ödenen", "Kalan"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        sales_layout.addWidget(self.sales_table)
        tabs.addTab(sales_widget, "Satış Listesi")

        layout.addWidget(tabs)

        self.load_reports()

    def create_summary_card(self, title: str, value: str, color: str) -> QFrame:
        """Özet kartı oluştur"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid {color};
            }}
        """)
        card.setMinimumHeight(100)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(value_label)

        return card

    def load_reports(self):
        """Raporları yükle"""
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        # Satış özeti
        sales_summary = db.get_sales_summary(start, end)
        self.sales_card.findChild(QLabel, "value").setText(f"{sales_summary['total_amount']:,.2f} TL")

        # Alım özeti
        purchases_summary = db.get_purchases_summary(start, end)
        self.purchases_card.findChild(QLabel, "value").setText(f"{purchases_summary['total_amount']:,.2f} TL")

        # Kar
        profit = sales_summary['total_amount'] - purchases_summary['total_amount']
        profit_label = self.profit_card.findChild(QLabel, "value")
        profit_label.setText(f"{profit:,.2f} TL")
        if profit < 0:
            profit_label.setStyleSheet("color: #e74c3c; font-size: 20px; font-weight: bold;")
        else:
            profit_label.setStyleSheet("color: #27ae60; font-size: 20px; font-weight: bold;")

        # Toplam alacak
        debtors = db.get_customers_with_debt()
        total_debt = sum(c['balance'] for c in debtors)
        self.debt_card.findChild(QLabel, "value").setText(f"{total_debt:,.2f} TL")

        # En çok satan ürünler
        top_products = db.get_top_products(10, start, end)
        self.top_products_table.setRowCount(len(top_products))
        for i, product in enumerate(top_products):
            self.top_products_table.setItem(i, 0, QTableWidgetItem(product['name']))
            self.top_products_table.setItem(i, 1, QTableWidgetItem(product['code'] or '-'))
            self.top_products_table.setItem(i, 2, QTableWidgetItem(f"{product['total_quantity']:.2f}"))
            self.top_products_table.setItem(i, 3, QTableWidgetItem(f"{product['total_amount']:,.2f} TL"))

        # Borçlu müşteriler
        self.load_debtors()

        # Satış listesi
        sales = db.get_all_sales(start, end)
        self.sales_table.setRowCount(len(sales))
        for i, sale in enumerate(sales):
            self.sales_table.setItem(i, 0, QTableWidgetItem(sale['invoice_no']))
            self.sales_table.setItem(i, 1, QTableWidgetItem(str(sale['sale_date'])[:10]))
            self.sales_table.setItem(i, 2, QTableWidgetItem(sale['customer_name'] or 'Perakende'))
            self.sales_table.setItem(i, 3, QTableWidgetItem(f"{sale['total']:,.2f} TL"))
            self.sales_table.setItem(i, 4, QTableWidgetItem(f"{sale['paid_amount']:,.2f} TL"))
            remaining = sale['total'] - sale['paid_amount']
            remaining_item = QTableWidgetItem(f"{remaining:,.2f} TL")
            if remaining > 0:
                remaining_item.setForeground(QColor('#e74c3c'))
            self.sales_table.setItem(i, 5, remaining_item)

    def load_debtors(self):
        """Borçlu müşterileri yükle"""
        if self.only_debtors_check.isChecked():
            customers = db.get_customers_with_debt()
        else:
            customers = db.get_all_customers()

        self.debtors_table.setRowCount(len(customers))
        for i, customer in enumerate(customers):
            self.debtors_table.setItem(i, 0, QTableWidgetItem(customer['name']))
            self.debtors_table.setItem(i, 1, QTableWidgetItem(customer['phone'] or '-'))
            self.debtors_table.setItem(i, 2, QTableWidgetItem(customer['address'] or '-'))

            balance_item = QTableWidgetItem(f"{customer['balance']:,.2f} TL")
            if customer['balance'] > 0:
                balance_item.setForeground(QColor('#e74c3c'))
            self.debtors_table.setItem(i, 3, balance_item)

    def refresh(self):
        self.load_reports()


class SettingsWidget(QWidget):
    """Ayarlar modülü"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Ayarlar")
        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Şirket bilgileri
        company_group = QGroupBox("Şirket Bilgileri")
        company_layout = QFormLayout(company_group)

        self.company_name = QLineEdit()
        self.company_name.setText(db.get_setting('company_name') or '')
        company_layout.addRow("Şirket Adı:", self.company_name)

        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(60)
        self.company_address.setText(db.get_setting('company_address') or '')
        company_layout.addRow("Adres:", self.company_address)

        self.company_phone = QLineEdit()
        self.company_phone.setText(db.get_setting('company_phone') or '')
        company_layout.addRow("Telefon:", self.company_phone)

        self.company_email = QLineEdit()
        self.company_email.setText(db.get_setting('company_email') or '')
        company_layout.addRow("E-posta:", self.company_email)

        self.company_tax = QLineEdit()
        self.company_tax.setText(db.get_setting('company_tax_number') or '')
        company_layout.addRow("Vergi No:", self.company_tax)

        self.company_tax_office = QLineEdit()
        self.company_tax_office.setText(db.get_setting('company_tax_office') or '')
        company_layout.addRow("Vergi Dairesi:", self.company_tax_office)

        layout.addWidget(company_group)

        # Genel ayarlar
        general_group = QGroupBox("Genel Ayarlar")
        general_layout = QFormLayout(general_group)

        self.currency = QLineEdit()
        self.currency.setText(db.get_setting('currency') or 'TL')
        general_layout.addRow("Para Birimi:", self.currency)

        self.tax_rate = QSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setSuffix(" %")
        self.tax_rate.setValue(int(db.get_setting('tax_rate') or 18))
        general_layout.addRow("KDV Oranı:", self.tax_rate)

        self.invoice_prefix = QLineEdit()
        self.invoice_prefix.setText(db.get_setting('invoice_prefix') or 'INV')
        general_layout.addRow("Fatura Ön Eki:", self.invoice_prefix)

        layout.addWidget(general_group)

        # Yedekleme
        backup_group = QGroupBox("Yedekleme")
        backup_layout = QVBoxLayout(backup_group)

        self.auto_backup = QCheckBox("Otomatik Yedekleme (Açılışta)")
        self.auto_backup.setChecked(db.get_setting('auto_backup') == '1')
        backup_layout.addWidget(self.auto_backup)

        backup_btn_layout = QHBoxLayout()

        backup_now_btn = QPushButton("Şimdi Yedekle")
        backup_now_btn.setObjectName("btnSuccess")
        backup_now_btn.clicked.connect(self.backup_now)
        backup_btn_layout.addWidget(backup_now_btn)

        restore_btn = QPushButton("Yedeği Geri Yükle")
        restore_btn.setObjectName("btnWarning")
        restore_btn.clicked.connect(self.restore_backup)
        backup_btn_layout.addWidget(restore_btn)

        backup_btn_layout.addStretch()
        backup_layout.addLayout(backup_btn_layout)

        layout.addWidget(backup_group)

        # Kaydet butonu
        save_btn = QPushButton("Ayarları Kaydet")
        save_btn.setObjectName("btnSuccess")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

    def save_settings(self):
        """Ayarları kaydet"""
        db.update_setting('company_name', self.company_name.text().strip())
        db.update_setting('company_address', self.company_address.toPlainText().strip())
        db.update_setting('company_phone', self.company_phone.text().strip())
        db.update_setting('company_email', self.company_email.text().strip())
        db.update_setting('company_tax_number', self.company_tax.text().strip())
        db.update_setting('company_tax_office', self.company_tax_office.text().strip())
        db.update_setting('currency', self.currency.text().strip())
        db.update_setting('tax_rate', str(self.tax_rate.value()))
        db.update_setting('invoice_prefix', self.invoice_prefix.text().strip())
        db.update_setting('auto_backup', '1' if self.auto_backup.isChecked() else '0')

        QMessageBox.information(self, "Başarılı", "Ayarlar kaydedildi!")

    def backup_now(self):
        """Veritabanını yedekle"""
        backup_dir = db.get_setting('backup_path') or 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f"muhasebe_backup_{timestamp}.db")

        try:
            shutil.copy2(db.DATABASE_PATH, backup_file)
            QMessageBox.information(self, "Başarılı", f"Yedek oluşturuldu:\n{backup_file}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yedekleme hatası: {str(e)}")

    def restore_backup(self):
        """Yedeği geri yükle"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Yedek Dosyası Seç", "backups", "Database Files (*.db)"
        )

        if file_path:
            reply = QMessageBox.warning(
                self, "Uyarı",
                "Mevcut veriler silinecek ve yedek geri yüklenecek. Devam etmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    shutil.copy2(file_path, db.DATABASE_PATH)
                    QMessageBox.information(self, "Başarılı", "Yedek geri yüklendi! Uygulama yeniden başlatılacak.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Geri yükleme hatası: {str(e)}")

    def refresh(self):
        pass


class MainWindow(QMainWindow):
    """Ana pencere"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Muhasebe Sistemi")
        self.setMinimumSize(1200, 700)

        # Ana widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo/Başlık
        logo = QLabel("MUHASEBE")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo)

        # Menü butonları
        self.menu_buttons = []
        menu_items = [
            ("Dashboard", 0),
            ("Müşteriler", 1),
            ("Tedarikçiler", 2),
            ("Ürünler", 3),
            ("Satış", 4),
            ("Alım", 5),
            ("Ödemeler", 6),
            ("Kasa", 7),
            ("Raporlar", 8),
            ("Ayarlar", 9),
        ]

        for name, index in menu_items:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        sidebar_layout.addStretch()

        # PDF Çıktı butonu
        pdf_btn = QPushButton("PDF Çıktı Al")
        pdf_btn.setObjectName("btnWarning")
        pdf_btn.clicked.connect(self.export_pdf)
        sidebar_layout.addWidget(pdf_btn)

        layout.addWidget(sidebar)

        # İçerik alanı
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content")

        # Sayfa widget'ları
        self.dashboard = DashboardWidget()
        self.customers = CustomersWidget()
        self.suppliers = SuppliersWidget()
        self.products = ProductsWidget()
        self.sales = SalesWidget()
        self.purchases = PurchasesWidget()
        self.payments = PaymentsWidget()
        self.cash = CashWidget()
        self.reports = ReportsWidget()
        self.settings = SettingsWidget()

        self.content_stack.addWidget(self.dashboard)
        self.content_stack.addWidget(self.customers)
        self.content_stack.addWidget(self.suppliers)
        self.content_stack.addWidget(self.products)
        self.content_stack.addWidget(self.sales)
        self.content_stack.addWidget(self.purchases)
        self.content_stack.addWidget(self.payments)
        self.content_stack.addWidget(self.cash)
        self.content_stack.addWidget(self.reports)
        self.content_stack.addWidget(self.settings)

        layout.addWidget(self.content_stack)

        # İlk sayfa
        self.switch_page(0)

        # Otomatik yedekleme
        if db.get_setting('auto_backup') == '1':
            self.settings.backup_now()

    def switch_page(self, index: int):
        """Sayfa değiştir"""
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)

        self.content_stack.setCurrentIndex(index)

        # Sayfayı yenile
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()

    def export_pdf(self):
        """PDF çıktı al"""
        from pdf_generator import PDFExportDialog
        dialog = PDFExportDialog(self)
        dialog.exec()


def main():
    # Veritabanını başlat
    db.init_database()

    # Uygulamayı başlat
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
