"""
Muhasebe Sistemi - PDF Oluşturucu
Rapor ve fatura PDF çıktıları
"""

import os
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QDateEdit, QCheckBox, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import QDate

import database as db

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFExportDialog(QDialog):
    """PDF çıktı alma dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PDF Çıktı Al")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Rapor tipi seçimi
        type_group = QGroupBox("Rapor Tipi")
        type_layout = QFormLayout(type_group)

        self.report_type = QComboBox()
        self.report_type.addItems([
            "Satış Listesi",
            "Müşteri Borçları",
            "Sadece Borçlu Müşteriler",
            "Ürün Stok Listesi",
            "Kasa Hareketleri",
            "Tedarikçi Listesi",
            "Satış Faturası"
        ])
        self.report_type.currentTextChanged.connect(self.on_type_changed)
        type_layout.addRow("Rapor:", self.report_type)

        layout.addWidget(type_group)

        # Tarih filtresi
        self.date_group = QGroupBox("Tarih Aralığı")
        date_layout = QHBoxLayout(self.date_group)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Başlangıç:"))
        date_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Bitiş:"))
        date_layout.addWidget(self.end_date)

        layout.addWidget(self.date_group)

        # Müşteri seçimi (satış faturası için)
        self.customer_group = QGroupBox("Müşteri Seçimi")
        customer_layout = QFormLayout(self.customer_group)

        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Tüm Müşteriler", None)
        for customer in db.get_all_customers():
            self.customer_combo.addItem(customer['name'], customer['id'])
        customer_layout.addRow("Müşteri:", self.customer_combo)

        self.customer_group.hide()
        layout.addWidget(self.customer_group)

        # Fatura seçimi
        self.invoice_group = QGroupBox("Fatura Seçimi")
        invoice_layout = QFormLayout(self.invoice_group)

        self.invoice_combo = QComboBox()
        for sale in db.get_all_sales()[:50]:
            self.invoice_combo.addItem(
                f"{sale['invoice_no']} - {sale['customer_name'] or 'Perakende'} ({sale['total']:.2f} TL)",
                sale['id']
            )
        invoice_layout.addRow("Fatura:", self.invoice_combo)

        self.invoice_group.hide()
        layout.addWidget(self.invoice_group)

        # İlerleme çubuğu
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)

        # Butonlar
        btn_layout = QHBoxLayout()

        export_btn = QPushButton("PDF Oluştur")
        export_btn.setObjectName("btnSuccess")
        export_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(export_btn)

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def on_type_changed(self, text: str):
        """Rapor tipi değiştiğinde"""
        self.date_group.show()
        self.customer_group.hide()
        self.invoice_group.hide()

        if text == "Satış Listesi":
            self.customer_group.show()
        elif text == "Satış Faturası":
            self.date_group.hide()
            self.invoice_group.show()
        elif text in ["Ürün Stok Listesi", "Tedarikçi Listesi", "Müşteri Borçları", "Sadece Borçlu Müşteriler"]:
            self.date_group.hide()

    def export_pdf(self):
        """PDF oluştur"""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.warning(
                self, "Uyarı",
                "PDF oluşturmak için 'reportlab' kütüphanesi gerekli.\n"
                "Kurulum: pip install reportlab"
            )
            return

        report_type = self.report_type.currentText()

        # Dosya kaydetme dialogu
        default_name = f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF Kaydet", default_name, "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        self.progress.show()
        self.progress.setValue(10)

        try:
            if report_type == "Satış Listesi":
                self.export_sales_list(file_path)
            elif report_type == "Müşteri Borçları":
                self.export_customer_debts(file_path, only_debtors=False)
            elif report_type == "Sadece Borçlu Müşteriler":
                self.export_customer_debts(file_path, only_debtors=True)
            elif report_type == "Ürün Stok Listesi":
                self.export_product_list(file_path)
            elif report_type == "Kasa Hareketleri":
                self.export_cash_transactions(file_path)
            elif report_type == "Tedarikçi Listesi":
                self.export_supplier_list(file_path)
            elif report_type == "Satış Faturası":
                self.export_invoice(file_path)

            self.progress.setValue(100)
            QMessageBox.information(self, "Başarılı", f"PDF oluşturuldu:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası:\n{str(e)}")

        self.progress.hide()

    def get_styles(self):
        """PDF stilleri"""
        styles = getSampleStyleSheet()

        # Türkçe karakterler için
        styles.add(ParagraphStyle(
            name='TurkishNormal',
            fontName='Helvetica',
            fontSize=10,
            leading=14
        ))

        styles.add(ParagraphStyle(
            name='TurkishTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            spaceAfter=20
        ))

        styles.add(ParagraphStyle(
            name='TurkishSubtitle',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            spaceAfter=10
        ))

        return styles

    def get_company_info(self):
        """Şirket bilgilerini al"""
        return {
            'name': db.get_setting('company_name') or 'Şirket Adı',
            'address': db.get_setting('company_address') or '',
            'phone': db.get_setting('company_phone') or '',
            'email': db.get_setting('company_email') or '',
            'tax_number': db.get_setting('company_tax_number') or '',
            'tax_office': db.get_setting('company_tax_office') or ''
        }

    def export_sales_list(self, file_path: str):
        """Satış listesi PDF"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = self.get_styles()
        company = self.get_company_info()

        # Başlık
        elements.append(Paragraph(company['name'], styles['TurkishTitle']))
        elements.append(Paragraph("Satis Listesi", styles['TurkishSubtitle']))

        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        customer_id = self.customer_combo.currentData()

        elements.append(Paragraph(f"Tarih: {start} - {end}", styles['TurkishNormal']))
        elements.append(Spacer(1, 20))

        self.progress.setValue(30)

        # Tablo verileri
        sales = db.get_all_sales(start, end, customer_id)

        data = [["Fatura No", "Tarih", "Musteri", "Toplam", "Odenen", "Kalan"]]

        for sale in sales:
            remaining = sale['total'] - sale['paid_amount']
            data.append([
                sale['invoice_no'],
                str(sale['sale_date'])[:10],
                sale['customer_name'] or 'Perakende',
                f"{sale['total']:.2f} TL",
                f"{sale['paid_amount']:.2f} TL",
                f"{remaining:.2f} TL"
            ])

        self.progress.setValue(60)

        # Toplam satır
        total_amount = sum(s['total'] for s in sales)
        total_paid = sum(s['paid_amount'] for s in sales)
        total_remaining = total_amount - total_paid

        data.append([
            "TOPLAM", "", "",
            f"{total_amount:.2f} TL",
            f"{total_paid:.2f} TL",
            f"{total_remaining:.2f} TL"
        ])

        # Tablo oluştur
        table = Table(data, colWidths=[3*cm, 2.5*cm, 4*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))

        elements.append(table)
        self.progress.setValue(80)

        doc.build(elements)

    def export_customer_debts(self, file_path: str, only_debtors: bool = True):
        """Müşteri borçları PDF"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = self.get_styles()
        company = self.get_company_info()

        # Başlık
        elements.append(Paragraph(company['name'], styles['TurkishTitle']))
        title = "Borclu Musteriler" if only_debtors else "Musteri Listesi"
        elements.append(Paragraph(title, styles['TurkishSubtitle']))
        elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d.%m.%Y')}", styles['TurkishNormal']))
        elements.append(Spacer(1, 20))

        self.progress.setValue(30)

        # Verileri al
        if only_debtors:
            customers = db.get_customers_with_debt()
        else:
            customers = db.get_all_customers()

        data = [["Musteri", "Telefon", "Adres", "Borc"]]

        for customer in customers:
            data.append([
                customer['name'],
                customer['phone'] or '-',
                (customer['address'] or '-')[:30],
                f"{customer['balance']:.2f} TL"
            ])

        self.progress.setValue(60)

        # Toplam
        total_debt = sum(c['balance'] for c in customers)
        data.append(["TOPLAM", "", "", f"{total_debt:.2f} TL"])

        # Tablo
        table = Table(data, colWidths=[5*cm, 3*cm, 5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))

        elements.append(table)
        self.progress.setValue(80)

        doc.build(elements)

    def export_product_list(self, file_path: str):
        """Ürün stok listesi PDF"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = self.get_styles()
        company = self.get_company_info()

        elements.append(Paragraph(company['name'], styles['TurkishTitle']))
        elements.append(Paragraph("Urun Stok Listesi", styles['TurkishSubtitle']))
        elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d.%m.%Y')}", styles['TurkishNormal']))
        elements.append(Spacer(1, 20))

        self.progress.setValue(30)

        products = db.get_all_products()

        data = [["Kod", "Urun Adi", "Birim", "Stok", "Alis", "Satis"]]

        for product in products:
            data.append([
                product['code'] or '-',
                product['name'][:25],
                product['unit'] or 'Adet',
                f"{product['stock_quantity']:.2f}",
                f"{product['buy_price']:.2f} TL",
                f"{product['sell_price']:.2f} TL"
            ])

        self.progress.setValue(60)

        table = Table(data, colWidths=[2.5*cm, 5*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))

        elements.append(table)
        self.progress.setValue(80)

        doc.build(elements)

    def export_cash_transactions(self, file_path: str):
        """Kasa hareketleri PDF"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = self.get_styles()
        company = self.get_company_info()

        elements.append(Paragraph(company['name'], styles['TurkishTitle']))
        elements.append(Paragraph("Kasa Hareketleri", styles['TurkishSubtitle']))

        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        elements.append(Paragraph(f"Tarih: {start} - {end}", styles['TurkishNormal']))
        elements.append(Spacer(1, 20))

        self.progress.setValue(30)

        transactions = db.get_cash_transactions(start, end)

        data = [["Tarih", "Tip", "Kategori", "Aciklama", "Tutar"]]

        total_in = 0
        total_out = 0

        for trans in transactions:
            tip = "Giris" if trans['transaction_type'] == 'giris' else "Cikis"
            if trans['transaction_type'] == 'giris':
                total_in += trans['amount']
            else:
                total_out += trans['amount']

            data.append([
                str(trans['transaction_date'])[:10],
                tip,
                trans['category'] or '-',
                (trans['description'] or '-')[:25],
                f"{trans['amount']:.2f} TL"
            ])

        self.progress.setValue(60)

        # Özet satırları
        data.append(["", "TOPLAM GIRIS", "", "", f"{total_in:.2f} TL"])
        data.append(["", "TOPLAM CIKIS", "", "", f"{total_out:.2f} TL"])
        data.append(["", "BAKIYE", "", "", f"{total_in - total_out:.2f} TL"])

        table = Table(data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))

        elements.append(table)
        self.progress.setValue(80)

        doc.build(elements)

    def export_supplier_list(self, file_path: str):
        """Tedarikçi listesi PDF"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = self.get_styles()
        company = self.get_company_info()

        elements.append(Paragraph(company['name'], styles['TurkishTitle']))
        elements.append(Paragraph("Tedarikci Listesi", styles['TurkishSubtitle']))
        elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d.%m.%Y')}", styles['TurkishNormal']))
        elements.append(Spacer(1, 20))

        self.progress.setValue(30)

        suppliers = db.get_all_suppliers()

        data = [["Tedarikci", "Telefon", "E-posta", "Bakiye"]]

        for supplier in suppliers:
            data.append([
                supplier['name'],
                supplier['phone'] or '-',
                supplier['email'] or '-',
                f"{supplier['balance']:.2f} TL"
            ])

        self.progress.setValue(60)

        table = Table(data, colWidths=[5*cm, 3*cm, 5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))

        elements.append(table)
        self.progress.setValue(80)

        doc.build(elements)

    def export_invoice(self, file_path: str):
        """Satış faturası PDF"""
        sale_id = self.invoice_combo.currentData()
        if not sale_id:
            QMessageBox.warning(self, "Hata", "Fatura seçin!")
            return

        sale = db.get_sale(sale_id)
        items = db.get_sale_items(sale_id)

        if not sale:
            QMessageBox.warning(self, "Hata", "Fatura bulunamadı!")
            return

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = self.get_styles()
        company = self.get_company_info()

        self.progress.setValue(20)

        # Şirket başlığı
        elements.append(Paragraph(company['name'], styles['TurkishTitle']))
        if company['address']:
            elements.append(Paragraph(company['address'], styles['TurkishNormal']))
        if company['phone']:
            elements.append(Paragraph(f"Tel: {company['phone']}", styles['TurkishNormal']))
        if company['tax_number']:
            elements.append(Paragraph(f"Vergi No: {company['tax_number']} - {company['tax_office']}", styles['TurkishNormal']))

        elements.append(Spacer(1, 20))

        # Fatura bilgileri
        elements.append(Paragraph("SATIS FATURASI", styles['TurkishSubtitle']))
        elements.append(Paragraph(f"Fatura No: {sale['invoice_no']}", styles['TurkishNormal']))
        elements.append(Paragraph(f"Tarih: {str(sale['sale_date'])[:10]}", styles['TurkishNormal']))
        elements.append(Paragraph(f"Musteri: {sale['customer_name'] or 'Perakende'}", styles['TurkishNormal']))

        elements.append(Spacer(1, 20))

        self.progress.setValue(40)

        # Ürün tablosu
        data = [["Urun", "Miktar", "Birim Fiyat", "Toplam"]]

        for item in items:
            data.append([
                item['product_name'],
                f"{item['quantity']:.2f}",
                f"{item['unit_price']:.2f} TL",
                f"{item['total']:.2f} TL"
            ])

        self.progress.setValue(60)

        table = Table(data, colWidths=[7*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

        # Toplam bilgileri
        totals_data = [
            ["Ara Toplam:", f"{sale['subtotal']:.2f} TL"],
            ["Indirim:", f"{sale['discount']:.2f} TL"],
            ["KDV:", f"{sale['tax']:.2f} TL"],
            ["GENEL TOPLAM:", f"{sale['total']:.2f} TL"],
            ["Odenen:", f"{sale['paid_amount']:.2f} TL"],
            ["Kalan:", f"{sale['total'] - sale['paid_amount']:.2f} TL"],
        ]

        totals_table = Table(totals_data, colWidths=[10*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE', (0, 3), (-1, 3), 1, colors.black),
        ]))

        elements.append(totals_table)
        self.progress.setValue(80)

        doc.build(elements)
