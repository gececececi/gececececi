#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Kod Üretici Modülü
DXF geometrilerinden CNC G-Kod üretir
CNC Torna için - X: Uzun Eksen, Y: Kısa Eksen
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from dxf_reader import DXFData, Point2D, EntityType


@dataclass
class GCodeParams:
    """G-Kod üretim parametreleri"""
    machine_type: str = "CNC Torna"
    unit: str = "G21"  # G21: mm, G20: inch
    feed_rate: int = 100  # mm/dak
    plunge_rate: int = 50  # mm/dak
    spindle_speed: int = 1000  # RPM
    cut_depth: float = 1.0  # mm
    pass_depth: float = 0.5  # mm
    safe_height: float = 5.0  # mm
    start_x: float = 0.0
    start_y: float = 0.0
    home_after: bool = True

    # Ek ayarlar
    coolant: bool = False  # Soğutma
    tool_number: int = 1
    work_offset: str = "G54"  # İş koordinat sistemi


class GCodeGenerator:
    """G-Kod üretici"""

    def __init__(self):
        self.gcode_lines: List[str] = []
        self.current_x: float = 0.0
        self.current_y: float = 0.0
        self.current_z: float = 0.0

    def generate(self, dxf_data: DXFData, params: GCodeParams) -> str:
        """DXF verisinden G-Kod üret"""
        self.gcode_lines = []
        self.params = params

        # Başlık ve açıklamalar
        self._add_header(dxf_data, params)

        # Başlangıç kodları
        self._add_startup_codes(params)

        # Entity'leri G-Kod'a dönüştür
        self._process_entities(dxf_data.entities, params)

        # Bitiş kodları
        self._add_end_codes(params)

        return '\n'.join(self.gcode_lines)

    def _add_header(self, dxf_data: DXFData, params: GCodeParams):
        """Başlık ve açıklama satırları ekle"""
        self.gcode_lines.extend([
            "; =============================================",
            "; DXF to G-Code - CNC Torna",
            f"; Oluşturma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "; =============================================",
            f"; Kaynak Dosya: {dxf_data.file_path}",
            f"; Makine Tipi: {params.machine_type}",
            f"; X Ekseni: Uzun Eksen",
            f"; Y Ekseni: Kısa Eksen",
            "; ---------------------------------------------",
            f"; Parça Boyutları:",
            f";   Genişlik (X): {dxf_data.width:.3f} mm",
            f";   Yükseklik (Y): {dxf_data.height:.3f} mm",
            f";   Min X: {dxf_data.bounds[0]:.3f}, Max X: {dxf_data.bounds[2]:.3f}",
            f";   Min Y: {dxf_data.bounds[1]:.3f}, Max Y: {dxf_data.bounds[3]:.3f}",
            "; ---------------------------------------------",
            f"; İşlem Parametreleri:",
            f";   İlerleme Hızı: {params.feed_rate} mm/dak",
            f";   Dalma Hızı: {params.plunge_rate} mm/dak",
            f";   Devir: {params.spindle_speed} RPM",
            f";   Kesme Derinliği: {params.cut_depth} mm",
            f";   Paso Derinliği: {params.pass_depth} mm",
            f";   Güvenli Yükseklik: {params.safe_height} mm",
            f"; Entity Sayısı: {dxf_data.entity_count}",
            "; =============================================",
            "",
        ])

    def _add_startup_codes(self, params: GCodeParams):
        """Başlangıç G-Kod'larını ekle"""
        self.gcode_lines.append("; === BAŞLANGIÇ KODLARI ===")

        # Birim seçimi
        if params.unit == "G21":
            self.gcode_lines.append("G21 ; Metrik birim (mm)")
        else:
            self.gcode_lines.append("G20 ; İnç birimi")

        # Temel ayarlar
        self.gcode_lines.extend([
            "G90 ; Mutlak koordinat sistemi",
            "G17 ; XY düzlemi seçimi",
            f"{params.work_offset} ; İş koordinat sistemi",
        ])

        # Takım seçimi
        if params.tool_number > 0:
            self.gcode_lines.append(f"T{params.tool_number} M6 ; Takım seçimi")

        # Güvenli yüksekliğe git
        self.gcode_lines.append(f"G0 Z{params.safe_height:.3f} ; Güvenli yükseklik")

        # Mil başlat
        self.gcode_lines.append(f"S{params.spindle_speed} M3 ; Mil başlat (CW)")

        # Soğutma
        if params.coolant:
            self.gcode_lines.append("M8 ; Soğutma aç")

        # Başlangıç noktasına git
        self.gcode_lines.extend([
            "",
            "; Başlangıç noktasına git",
            f"G0 X{params.start_x:.3f} Y{params.start_y:.3f}",
            "",
        ])

        self.current_x = params.start_x
        self.current_y = params.start_y
        self.current_z = params.safe_height

    def _process_entities(self, entities: List, params: GCodeParams):
        """Entity'leri G-Kod'a dönüştür"""
        self.gcode_lines.append("; === İŞLEM KODLARI ===")

        # Paso sayısını hesapla
        num_passes = max(1, int(params.cut_depth / params.pass_depth))
        actual_pass_depth = params.cut_depth / num_passes

        self.gcode_lines.append(f"; Toplam {num_passes} paso, her paso {actual_pass_depth:.3f} mm")
        self.gcode_lines.append("")

        # Her paso için
        for pass_num in range(num_passes):
            current_depth = -((pass_num + 1) * actual_pass_depth)
            self.gcode_lines.append(f"; --- Paso {pass_num + 1}/{num_passes}, Derinlik: {current_depth:.3f} mm ---")

            # Her entity için
            for idx, entity in enumerate(entities):
                self._process_single_entity(entity, idx, current_depth, params)

            self.gcode_lines.append("")

    def _process_single_entity(self, entity, idx: int, depth: float, params: GCodeParams):
        """Tek bir entity'yi G-Kod'a dönüştür"""
        points = entity.get_points()
        if len(points) < 2:
            return

        entity_type = entity.entity_type.value
        self.gcode_lines.append(f"; Entity {idx + 1}: {entity_type}")

        # İlk noktaya hızlı git
        first_point = points[0]
        self.gcode_lines.append(f"G0 X{first_point.x:.3f} Y{first_point.y:.3f} ; Konumlan")

        # Derinliğe in (dalma hızıyla)
        self.gcode_lines.append(f"G1 Z{depth:.3f} F{params.plunge_rate} ; Dalma")

        # İşleme hızını ayarla
        self.gcode_lines.append(f"F{params.feed_rate}")

        # Noktalar boyunca ilerle
        for point in points[1:]:
            self.gcode_lines.append(f"G1 X{point.x:.3f} Y{point.y:.3f}")

        # Güvenli yüksekliğe çık
        self.gcode_lines.append(f"G0 Z{params.safe_height:.3f} ; Güvenli yükseklik")

        self.current_x = points[-1].x
        self.current_y = points[-1].y
        self.current_z = params.safe_height

    def _add_end_codes(self, params: GCodeParams):
        """Bitiş G-Kod'larını ekle"""
        self.gcode_lines.extend([
            "",
            "; === BİTİŞ KODLARI ===",
            f"G0 Z{params.safe_height:.3f} ; Güvenli yükseklik",
        ])

        # Soğutma kapat
        if params.coolant:
            self.gcode_lines.append("M9 ; Soğutma kapat")

        # Mil durdur
        self.gcode_lines.append("M5 ; Mil durdur")

        # Home'a git
        if params.home_after:
            self.gcode_lines.extend([
                "G28 G91 Z0 ; Z Home",
                "G28 G91 X0 Y0 ; XY Home",
                "G90 ; Mutlak koordinata dön",
            ])

        # Program sonu
        self.gcode_lines.extend([
            "M30 ; Program sonu",
            "",
            "; === PROGRAM SONU ===",
        ])


class GCodeGeneratorLathe(GCodeGenerator):
    """CNC Torna için özelleştirilmiş G-Kod üretici"""

    def _add_startup_codes(self, params: GCodeParams):
        """Torna için başlangıç G-Kod'larını ekle"""
        self.gcode_lines.append("; === BAŞLANGIÇ KODLARI (TORNA) ===")

        # Birim seçimi
        if params.unit == "G21":
            self.gcode_lines.append("G21 ; Metrik birim (mm)")
        else:
            self.gcode_lines.append("G20 ; İnç birimi")

        # Torna temel ayarları
        self.gcode_lines.extend([
            "G90 ; Mutlak koordinat sistemi",
            "G18 ; ZX düzlemi (torna için)",
            f"{params.work_offset} ; İş koordinat sistemi",
        ])

        # Takım seçimi
        if params.tool_number > 0:
            self.gcode_lines.append(f"T{params.tool_number:02d}00 M6 ; Takım seçimi")

        # Güvenli pozisyona git
        self.gcode_lines.append(f"G0 X{params.safe_height:.3f} Z{params.start_x:.3f} ; Güvenli pozisyon")

        # Mil başlat
        self.gcode_lines.append(f"G97 S{params.spindle_speed} M3 ; Sabit devir, mil başlat")

        # Soğutma
        if params.coolant:
            self.gcode_lines.append("M8 ; Soğutma aç")

        self.gcode_lines.append("")

    def _process_single_entity(self, entity, idx: int, depth: float, params: GCodeParams):
        """Torna için entity işleme - X ve Z koordinatları"""
        points = entity.get_points()
        if len(points) < 2:
            return

        entity_type = entity.entity_type.value
        self.gcode_lines.append(f"; Entity {idx + 1}: {entity_type}")

        # Torna için: DXF X -> G-kod Z (uzun eksen), DXF Y -> G-kod X (çap/yarıçap)
        first_point = points[0]

        # Hızlı konumlanma
        self.gcode_lines.append(f"G0 X{first_point.y:.3f} Z{first_point.x:.3f} ; Konumlan")

        # İşleme hızını ayarla
        self.gcode_lines.append(f"G1 F{params.feed_rate}")

        # Noktalar boyunca ilerle
        for point in points[1:]:
            # DXF X -> Z, DXF Y -> X (torna koordinatları)
            self.gcode_lines.append(f"G1 X{point.y:.3f} Z{point.x:.3f}")

        # Güvenli pozisyona çık
        self.gcode_lines.append(f"G0 X{params.safe_height:.3f} ; Güvenli X")

    def _add_end_codes(self, params: GCodeParams):
        """Torna için bitiş G-Kod'larını ekle"""
        self.gcode_lines.extend([
            "",
            "; === BİTİŞ KODLARI (TORNA) ===",
            f"G0 X{params.safe_height:.3f} ; Güvenli X pozisyonu",
        ])

        # Soğutma kapat
        if params.coolant:
            self.gcode_lines.append("M9 ; Soğutma kapat")

        # Mil durdur
        self.gcode_lines.append("M5 ; Mil durdur")

        # Home'a git
        if params.home_after:
            self.gcode_lines.extend([
                "G28 U0 W0 ; Home (torna)",
            ])

        # Program sonu
        self.gcode_lines.extend([
            "M30 ; Program sonu",
            "",
            "; === PROGRAM SONU ===",
        ])


def create_generator(machine_type: str) -> GCodeGenerator:
    """Makine tipine göre G-Kod üretici oluştur"""
    if machine_type == "CNC Torna":
        return GCodeGeneratorLathe()
    else:
        return GCodeGenerator()


def generate_gcode_from_params(dxf_data: DXFData, params_dict: Dict) -> str:
    """Parametre sözlüğünden G-Kod üret"""
    params = GCodeParams(
        machine_type=params_dict.get('machine_type', 'CNC Torna'),
        unit=params_dict.get('unit', 'G21'),
        feed_rate=params_dict.get('feed_rate', 100),
        plunge_rate=params_dict.get('plunge_rate', 50),
        spindle_speed=params_dict.get('spindle_speed', 1000),
        cut_depth=params_dict.get('cut_depth', 1.0),
        pass_depth=params_dict.get('pass_depth', 0.5),
        safe_height=params_dict.get('safe_height', 5.0),
        start_x=params_dict.get('start_x', 0.0),
        start_y=params_dict.get('start_y', 0.0),
        home_after=params_dict.get('home_after', True),
    )

    generator = create_generator(params.machine_type)
    return generator.generate(dxf_data, params)
