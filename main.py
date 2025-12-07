#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF Önizleme ve CNC G-Kod Çıkartma Uygulaması
CNC Torna için - X: Uzun Eksen, Y: Kısa Eksen
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QGroupBox, QLabel, QPushButton, QLineEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QFileDialog, QMessageBox, QComboBox,
    QCheckBox, QStatusBar, QMenuBar, QMenu, QToolBar, QGraphicsView,
    QGraphicsScene, QFrame, QFormLayout, QTabWidget, QGraphicsPathItem
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QAction, QPen, QBrush, QColor, QPainter, QFont, QWheelEvent,
    QMouseEvent, QPainterPath
)

from dxf_reader import DXFReader, DXFData, EntityType
from gcode_generator import generate_gcode_from_params


class DXFPreviewWidget(QGraphicsView):
    """DXF dosyası önizleme widget'ı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Görünüm ayarları
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Arka plan
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        # Zoom seviyesi
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # Grid çizimi için
        self.show_grid = True
        self.grid_size = 10

        # Başlangıç görünümü
        self._draw_initial_view()

    def _draw_initial_view(self):
        """Başlangıç görünümü çiz"""
        self.scene.clear()

        # Grid çiz
        if self.show_grid:
            self._draw_grid()

        # Eksen çiz
        self._draw_axes()

        # Bilgi metni
        text = self.scene.addText("DXF dosyası yükleyin", QFont("Arial", 12))
        text.setDefaultTextColor(QColor(150, 150, 150))
        text.setPos(-60, -30)

    def _draw_grid(self):
        """Grid çiz"""
        pen = QPen(QColor(50, 50, 50))
        pen.setWidth(1)

        grid_range = 200
        for i in range(-grid_range, grid_range + 1, self.grid_size):
            # Dikey çizgiler
            self.scene.addLine(i, -grid_range, i, grid_range, pen)
            # Yatay çizgiler
            self.scene.addLine(-grid_range, i, grid_range, i, pen)

    def _draw_axes(self):
        """Koordinat eksenleri çiz"""
        # X ekseni (kırmızı) - Uzun eksen
        pen_x = QPen(QColor(255, 80, 80))
        pen_x.setWidth(2)
        self.scene.addLine(-200, 0, 200, 0, pen_x)

        # Y ekseni (yeşil) - Kısa eksen
        pen_y = QPen(QColor(80, 255, 80))
        pen_y.setWidth(2)
        self.scene.addLine(0, -200, 0, 200, pen_y)

        # Eksen etiketleri
        label_x = self.scene.addText("X (Uzun)", QFont("Arial", 8))
        label_x.setDefaultTextColor(QColor(255, 80, 80))
        label_x.setPos(180, 5)

        label_y = self.scene.addText("Y (Kısa)", QFont("Arial", 8))
        label_y.setDefaultTextColor(QColor(80, 255, 80))
        label_y.setPos(5, -200)

    def wheelEvent(self, event: QWheelEvent):
        """Mouse tekerleği ile zoom"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        new_zoom = self.zoom_factor * zoom_factor

        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.zoom_factor = new_zoom
            self.scale(zoom_factor, zoom_factor)

    def fit_to_view(self):
        """İçeriği görünüme sığdır"""
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_factor = 1.0

    def zoom_in(self):
        """Yakınlaştır"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor *= 1.2
            self.scale(1.2, 1.2)

    def zoom_out(self):
        """Uzaklaştır"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor /= 1.2
            self.scale(1/1.2, 1/1.2)

    def reset_view(self):
        """Görünümü sıfırla"""
        self.resetTransform()
        self.zoom_factor = 1.0
        self.fit_to_view()

    def draw_dxf(self, dxf_data: DXFData):
        """DXF verilerini çiz"""
        self.scene.clear()

        # Sınırları al
        min_x, min_y, max_x, max_y = dxf_data.bounds
        width = max_x - min_x
        height = max_y - min_y

        # Grid çiz (DXF boyutlarına göre)
        if self.show_grid:
            self._draw_dynamic_grid(min_x, min_y, max_x, max_y)

        # Eksenleri çiz
        self._draw_axes_at_origin(min_x, min_y, max_x, max_y)

        # Entity renkler
        entity_pen = QPen(QColor(0, 200, 255))  # Cyan
        entity_pen.setWidth(0)  # Cosmetic pen (zoom'dan etkilenmez)
        entity_pen.setCosmetic(True)

        # Her entity'yi çiz
        for entity in dxf_data.entities:
            points = entity.get_points()
            if len(points) < 2:
                continue

            # QPainterPath oluştur
            path = QPainterPath()
            # Y eksenini ters çevir (ekran koordinatları için)
            path.moveTo(points[0].x, -points[0].y)

            for point in points[1:]:
                path.lineTo(point.x, -point.y)

            # Path'i sahneye ekle
            path_item = self.scene.addPath(path, entity_pen)

        # Görünümü sığdır
        self.fit_to_view()

    def _draw_dynamic_grid(self, min_x: float, min_y: float, max_x: float, max_y: float):
        """Dinamik grid çiz"""
        pen = QPen(QColor(50, 50, 50))
        pen.setWidth(0)
        pen.setCosmetic(True)

        # Grid aralığını hesapla
        width = max_x - min_x
        height = max_y - min_y
        max_dim = max(width, height)

        # Uygun grid aralığı bul
        if max_dim <= 10:
            grid_step = 1
        elif max_dim <= 50:
            grid_step = 5
        elif max_dim <= 100:
            grid_step = 10
        elif max_dim <= 500:
            grid_step = 50
        else:
            grid_step = 100

        # Grid sınırlarını genişlet
        margin = grid_step * 2
        grid_min_x = (int(min_x / grid_step) - 1) * grid_step
        grid_max_x = (int(max_x / grid_step) + 2) * grid_step
        grid_min_y = (int(min_y / grid_step) - 1) * grid_step
        grid_max_y = (int(max_y / grid_step) + 2) * grid_step

        # Dikey çizgiler
        x = grid_min_x
        while x <= grid_max_x:
            self.scene.addLine(x, -grid_min_y, x, -grid_max_y, pen)
            x += grid_step

        # Yatay çizgiler
        y = grid_min_y
        while y <= grid_max_y:
            self.scene.addLine(grid_min_x, -y, grid_max_x, -y, pen)
            y += grid_step

    def _draw_axes_at_origin(self, min_x: float, min_y: float, max_x: float, max_y: float):
        """Orijinde eksenleri çiz"""
        # Eksen uzunlukları
        margin = max(max_x - min_x, max_y - min_y) * 0.1

        # X ekseni (kırmızı)
        pen_x = QPen(QColor(255, 80, 80))
        pen_x.setWidth(2)
        pen_x.setCosmetic(True)
        self.scene.addLine(min_x - margin, 0, max_x + margin, 0, pen_x)

        # Y ekseni (yeşil) - ters çevrilmiş
        pen_y = QPen(QColor(80, 255, 80))
        pen_y.setWidth(2)
        pen_y.setCosmetic(True)
        self.scene.addLine(0, -(min_y - margin), 0, -(max_y + margin), pen_y)

        # Eksen etiketleri
        label_x = self.scene.addText("X", QFont("Arial", 8))
        label_x.setDefaultTextColor(QColor(255, 80, 80))
        label_x.setPos(max_x + margin, 5)

        label_y = self.scene.addText("Y", QFont("Arial", 8))
        label_y.setDefaultTextColor(QColor(80, 255, 80))
        label_y.setPos(5, -(max_y + margin))


class CNCParametersWidget(QWidget):
    """CNC parametreleri widget'ı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Makine Ayarları
        machine_group = QGroupBox("Makine Ayarları")
        machine_layout = QFormLayout()

        self.machine_type = QComboBox()
        self.machine_type.addItems(["CNC Torna", "CNC Freze", "Lazer Kesim"])
        machine_layout.addRow("Makine Tipi:", self.machine_type)

        self.unit_type = QComboBox()
        self.unit_type.addItems(["mm (G21)", "inch (G20)"])
        machine_layout.addRow("Birim:", self.unit_type)

        machine_group.setLayout(machine_layout)
        layout.addWidget(machine_group)

        # Hareket Parametreleri
        movement_group = QGroupBox("Hareket Parametreleri")
        movement_layout = QFormLayout()

        self.feed_rate = QSpinBox()
        self.feed_rate.setRange(1, 10000)
        self.feed_rate.setValue(100)
        self.feed_rate.setSuffix(" mm/dak")
        movement_layout.addRow("İlerleme (F):", self.feed_rate)

        self.plunge_rate = QSpinBox()
        self.plunge_rate.setRange(1, 5000)
        self.plunge_rate.setValue(50)
        self.plunge_rate.setSuffix(" mm/dak")
        movement_layout.addRow("Dalma Hızı:", self.plunge_rate)

        self.spindle_speed = QSpinBox()
        self.spindle_speed.setRange(0, 30000)
        self.spindle_speed.setValue(1000)
        self.spindle_speed.setSuffix(" RPM")
        movement_layout.addRow("Devir (S):", self.spindle_speed)

        movement_group.setLayout(movement_layout)
        layout.addWidget(movement_group)

        # Kesim Parametreleri
        cut_group = QGroupBox("Kesim Parametreleri")
        cut_layout = QFormLayout()

        self.cut_depth = QDoubleSpinBox()
        self.cut_depth.setRange(0.01, 100)
        self.cut_depth.setValue(1.0)
        self.cut_depth.setSuffix(" mm")
        self.cut_depth.setDecimals(2)
        cut_layout.addRow("Kesme Derinliği:", self.cut_depth)

        self.pass_depth = QDoubleSpinBox()
        self.pass_depth.setRange(0.01, 50)
        self.pass_depth.setValue(0.5)
        self.pass_depth.setSuffix(" mm")
        self.pass_depth.setDecimals(2)
        cut_layout.addRow("Paso Derinliği:", self.pass_depth)

        self.safe_height = QDoubleSpinBox()
        self.safe_height.setRange(1, 100)
        self.safe_height.setValue(5.0)
        self.safe_height.setSuffix(" mm")
        self.safe_height.setDecimals(2)
        cut_layout.addRow("Güvenli Yükseklik:", self.safe_height)

        cut_group.setLayout(cut_layout)
        layout.addWidget(cut_group)

        # Başlangıç/Bitiş Ayarları
        start_end_group = QGroupBox("Başlangıç / Bitiş")
        start_end_layout = QFormLayout()

        self.start_x = QDoubleSpinBox()
        self.start_x.setRange(-10000, 10000)
        self.start_x.setValue(0)
        self.start_x.setSuffix(" mm")
        start_end_layout.addRow("Başlangıç X:", self.start_x)

        self.start_y = QDoubleSpinBox()
        self.start_y.setRange(-10000, 10000)
        self.start_y.setValue(0)
        self.start_y.setSuffix(" mm")
        start_end_layout.addRow("Başlangıç Y:", self.start_y)

        self.home_after = QCheckBox("İşlem sonrası Home")
        self.home_after.setChecked(True)
        start_end_layout.addRow("", self.home_after)

        start_end_group.setLayout(start_end_layout)
        layout.addWidget(start_end_group)

        # Boşluk ekle
        layout.addStretch()

    def get_parameters(self):
        """Tüm parametreleri döndür"""
        return {
            'machine_type': self.machine_type.currentText(),
            'unit': 'G21' if self.unit_type.currentIndex() == 0 else 'G20',
            'feed_rate': self.feed_rate.value(),
            'plunge_rate': self.plunge_rate.value(),
            'spindle_speed': self.spindle_speed.value(),
            'cut_depth': self.cut_depth.value(),
            'pass_depth': self.pass_depth.value(),
            'safe_height': self.safe_height.value(),
            'start_x': self.start_x.value(),
            'start_y': self.start_y.value(),
            'home_after': self.home_after.isChecked()
        }


class GCodePreviewWidget(QWidget):
    """G-Kod önizleme widget'ı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Başlık ve satır sayısı
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("G-Kod Önizleme:"))
        self.line_count_label = QLabel("0 satır")
        header_layout.addWidget(self.line_count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # G-Kod metin alanı
        self.gcode_text = QTextEdit()
        self.gcode_text.setFont(QFont("Courier New", 10))
        self.gcode_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
        """)
        self.gcode_text.setPlaceholderText("G-Kod burada görüntülenecek...")
        layout.addWidget(self.gcode_text)

        # Butonlar
        button_layout = QHBoxLayout()

        self.generate_btn = QPushButton("G-Kod Oluştur")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        button_layout.addWidget(self.generate_btn)

        self.save_btn = QPushButton("Kaydet (.nc)")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #388a34;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #46a342;
            }
        """)
        button_layout.addWidget(self.save_btn)

        self.copy_btn = QPushButton("Kopyala")
        button_layout.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("Temizle")
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

    def set_gcode(self, gcode: str):
        """G-Kod metnini ayarla"""
        self.gcode_text.setPlainText(gcode)
        line_count = len(gcode.strip().split('\n')) if gcode.strip() else 0
        self.line_count_label.setText(f"{line_count} satır")

    def get_gcode(self) -> str:
        """G-Kod metnini al"""
        return self.gcode_text.toPlainText()

    def clear(self):
        """G-Kod metnini temizle"""
        self.gcode_text.clear()
        self.line_count_label.setText("0 satır")


class MainWindow(QMainWindow):
    """Ana pencere"""

    def __init__(self):
        super().__init__()
        self.dxf_file_path: Optional[str] = None
        self.dxf_data: Optional[DXFData] = None
        self.dxf_reader = DXFReader()

        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_ui(self):
        """Ana arayüzü oluştur"""
        self.setWindowTitle("DXF to G-Code - CNC Torna")
        self.setMinimumSize(1200, 800)

        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Ana splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # Sol Panel - DXF Önizleme
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Dosya bilgisi
        file_group = QGroupBox("DXF Dosyası")
        file_layout = QHBoxLayout()

        self.file_path_label = QLabel("Dosya seçilmedi")
        self.file_path_label.setStyleSheet("color: #888;")
        file_layout.addWidget(self.file_path_label, 1)

        self.load_btn = QPushButton("DXF Yükle")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        file_layout.addWidget(self.load_btn)

        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # DXF Önizleme
        preview_group = QGroupBox("Önizleme (X: Uzun Eksen, Y: Kısa Eksen)")
        preview_layout = QVBoxLayout()

        self.dxf_preview = DXFPreviewWidget()
        preview_layout.addWidget(self.dxf_preview)

        # Zoom kontrolleri
        zoom_layout = QHBoxLayout()

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(30, 30)
        zoom_layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(30, 30)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.fit_btn = QPushButton("Sığdır")
        zoom_layout.addWidget(self.fit_btn)

        self.reset_btn = QPushButton("Sıfırla")
        zoom_layout.addWidget(self.reset_btn)

        zoom_layout.addStretch()

        self.grid_checkbox = QCheckBox("Grid Göster")
        self.grid_checkbox.setChecked(True)
        zoom_layout.addWidget(self.grid_checkbox)

        preview_layout.addLayout(zoom_layout)
        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)

        # Sağ Panel - Parametreler ve G-Kod
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Tab widget
        tab_widget = QTabWidget()

        # Parametreler sekmesi
        self.parameters_widget = CNCParametersWidget()
        tab_widget.addTab(self.parameters_widget, "CNC Parametreleri")

        # DXF Bilgileri sekmesi
        dxf_info_widget = QWidget()
        dxf_info_layout = QVBoxLayout(dxf_info_widget)

        self.dxf_info_text = QTextEdit()
        self.dxf_info_text.setReadOnly(True)
        self.dxf_info_text.setPlaceholderText("DXF dosyası bilgileri burada görüntülenecek...")
        dxf_info_layout.addWidget(self.dxf_info_text)

        tab_widget.addTab(dxf_info_widget, "DXF Bilgileri")

        right_layout.addWidget(tab_widget)

        # G-Kod önizleme
        self.gcode_preview = GCodePreviewWidget()
        right_layout.addWidget(self.gcode_preview)

        # Splitter'a ekle
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([600, 600])

    def _setup_menubar(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()

        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")

        open_action = QAction("DXF Aç...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_dxf_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_gcode_action = QAction("G-Kod Kaydet...", self)
        save_gcode_action.setShortcut("Ctrl+S")
        save_gcode_action.triggered.connect(self.save_gcode)
        file_menu.addAction(save_gcode_action)

        file_menu.addSeparator()

        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")

        zoom_in_action = QAction("Yakınlaştır", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.dxf_preview.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Uzaklaştır", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.dxf_preview.zoom_out)
        view_menu.addAction(zoom_out_action)

        fit_action = QAction("Görünüme Sığdır", self)
        fit_action.setShortcut("Ctrl+0")
        fit_action.triggered.connect(self.dxf_preview.fit_to_view)
        view_menu.addAction(fit_action)

        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")

        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Araç çubuğunu oluştur"""
        toolbar = QToolBar("Ana Araç Çubuğu")
        self.addToolBar(toolbar)

        # DXF Yükle
        load_action = QAction("DXF Yükle", self)
        load_action.triggered.connect(self.load_dxf_file)
        toolbar.addAction(load_action)

        toolbar.addSeparator()

        # G-Kod Oluştur
        generate_action = QAction("G-Kod Oluştur", self)
        generate_action.triggered.connect(self.generate_gcode)
        toolbar.addAction(generate_action)

        # G-Kod Kaydet
        save_action = QAction("Kaydet", self)
        save_action.triggered.connect(self.save_gcode)
        toolbar.addAction(save_action)

    def _setup_statusbar(self):
        """Durum çubuğunu oluştur"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Hazır - DXF dosyası yükleyin")

    def _connect_signals(self):
        """Sinyal bağlantılarını yap"""
        self.load_btn.clicked.connect(self.load_dxf_file)
        self.zoom_in_btn.clicked.connect(self.dxf_preview.zoom_in)
        self.zoom_out_btn.clicked.connect(self.dxf_preview.zoom_out)
        self.fit_btn.clicked.connect(self.dxf_preview.fit_to_view)
        self.reset_btn.clicked.connect(self.dxf_preview.reset_view)

        self.gcode_preview.generate_btn.clicked.connect(self.generate_gcode)
        self.gcode_preview.save_btn.clicked.connect(self.save_gcode)
        self.gcode_preview.copy_btn.clicked.connect(self.copy_gcode)
        self.gcode_preview.clear_btn.clicked.connect(self.gcode_preview.clear)

    def load_dxf_file(self):
        """DXF dosyası yükle"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "DXF Dosyası Seç",
            "",
            "DXF Dosyaları (*.dxf);;Tüm Dosyalar (*)"
        )

        if file_path:
            self.dxf_file_path = file_path
            self.file_path_label.setText(file_path.split('/')[-1])
            self.file_path_label.setStyleSheet("color: #4ec9b0;")
            self.statusbar.showMessage(f"DXF yüklendi: {file_path}")

            # DXF dosyasını oku ve önizle
            self._load_and_preview_dxf(file_path)

    def _load_and_preview_dxf(self, file_path: str):
        """DXF dosyasını yükle ve önizle"""
        try:
            # DXF dosyasını oku
            self.dxf_data = self.dxf_reader.read_file(file_path)

            # DXF bilgilerini göster
            self.dxf_info_text.setText(self.dxf_data.get_info_text())

            # Önizlemeyi çiz
            self.dxf_preview.draw_dxf(self.dxf_data)

            # Durum çubuğunu güncelle
            self.statusbar.showMessage(
                f"DXF yüklendi: {self.dxf_data.entity_count} entity, "
                f"Boyut: {self.dxf_data.width:.2f} x {self.dxf_data.height:.2f} mm"
            )

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"DXF dosyası okunamadı:\n{str(e)}")
            self.statusbar.showMessage("DXF okuma hatası")

    def generate_gcode(self):
        """G-Kod oluştur"""
        if not self.dxf_file_path:
            QMessageBox.warning(self, "Uyarı", "Önce bir DXF dosyası yükleyin!")
            return

        if not self.dxf_data:
            QMessageBox.warning(self, "Uyarı", "DXF verisi yüklenememiş!")
            return

        try:
            params = self.parameters_widget.get_parameters()

            # G-Kod üret
            gcode = generate_gcode_from_params(self.dxf_data, params)
            self.gcode_preview.set_gcode(gcode)

            # Durum güncelle
            line_count = len(gcode.strip().split('\n'))
            self.statusbar.showMessage(f"G-Kod oluşturuldu: {line_count} satır")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"G-Kod oluşturma hatası:\n{str(e)}")
            self.statusbar.showMessage("G-Kod oluşturma hatası")

    def save_gcode(self):
        """G-Kod kaydet"""
        gcode = self.gcode_preview.get_gcode()

        if not gcode.strip():
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek G-Kod yok!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "G-Kod Kaydet",
            "",
            "NC Dosyaları (*.nc);;G-Kod Dosyaları (*.gcode);;Tüm Dosyalar (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(gcode)
                self.statusbar.showMessage(f"G-Kod kaydedildi: {file_path}")
                QMessageBox.information(self, "Başarılı", f"G-Kod kaydedildi:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")

    def copy_gcode(self):
        """G-Kod'u panoya kopyala"""
        gcode = self.gcode_preview.get_gcode()
        if gcode.strip():
            QApplication.clipboard().setText(gcode)
            self.statusbar.showMessage("G-Kod panoya kopyalandı")

    def show_about(self):
        """Hakkında penceresi"""
        QMessageBox.about(
            self,
            "Hakkında",
            "DXF to G-Code\n"
            "CNC Torna için G-Kod Üretici\n\n"
            "X: Uzun Eksen\n"
            "Y: Kısa Eksen\n\n"
            "PyQt6 ile geliştirilmiştir."
        )


def main():
    app = QApplication(sys.argv)

    # Uygulama stili
    app.setStyle("Fusion")

    # Koyu tema
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(palette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
