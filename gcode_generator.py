#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNC Torna G-Kod Üretici Modülü
DXF profilinden kaba talaş ve finiş G-Kod üretir

Koordinat Sistemi:
- DXF X -> Torna Z (uzunluk/eksenel yön)
- DXF Y -> Torna X (çap/radyal yön)
- X: Uzun eksen (Z torna)
- Y: Kısa eksen (X torna - çap)
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

from dxf_reader import DXFData, Point2D


@dataclass
class ProfilePoint:
    """Profil noktası (torna koordinatlarında)"""
    z: float  # Eksenel pozisyon (DXF X)
    x: float  # Radyal pozisyon/çap (DXF Y)

    def __repr__(self):
        return f"ProfilePoint(Z={self.z:.3f}, X={self.x:.3f})"


@dataclass
class TurningParams:
    """Torna parametreleri"""
    # Kaba parça
    stock_diameter: float = 50.0
    stock_length: float = 100.0
    # Takım
    tool_radius: float = 0.4
    tool_number: int = 1
    tool_orientation: int = 3  # 1,2,3,4
    # Tornalama
    rough_depth: float = 1.0  # Radyal paso derinliği
    finish_allowance: float = 0.2  # Finiş payı
    operation_type: str = "Kaba + Finiş"
    # Hareket
    rough_feed: int = 150
    finish_feed: int = 80
    spindle_speed: int = 1200
    safe_x: float = 5.0  # Güvenli X (çapın üstünde)
    clearance_z: float = 2.0  # Z boşluk
    # Diğer
    unit: str = "G21"
    home_after: bool = True
    coolant: bool = False


class LatheGCodeGenerator:
    """CNC Torna G-Kod üretici"""

    def __init__(self):
        self.gcode_lines: List[str] = []
        self.profile_points: List[ProfilePoint] = []
        self.params: Optional[TurningParams] = None

    def generate(self, dxf_data: DXFData, params: TurningParams) -> str:
        """DXF profilinden G-Kod üret"""
        self.gcode_lines = []
        self.params = params

        # DXF'den profil noktalarını çıkar
        self.profile_points = self._extract_profile(dxf_data)

        if not self.profile_points:
            raise ValueError("DXF'den profil noktası çıkarılamadı!")

        # Profili Z'ye göre sırala (soldan sağa)
        self.profile_points.sort(key=lambda p: p.z)

        # Başlık
        self._add_header(dxf_data)

        # Başlangıç kodları
        self._add_startup()

        # İşlem tipine göre G-kod üret
        if params.operation_type in ["Kaba + Finiş", "Sadece Kaba"]:
            self._generate_roughing()

        if params.operation_type in ["Kaba + Finiş", "Sadece Finiş"]:
            self._generate_finishing()

        # Bitiş kodları
        self._add_ending()

        return '\n'.join(self.gcode_lines)

    def _extract_profile(self, dxf_data: DXFData) -> List[ProfilePoint]:
        """DXF entity'lerinden profil noktalarını çıkar"""
        all_points = []

        for entity in dxf_data.entities:
            points = entity.get_points()
            for pt in points:
                # DXF X -> Z (uzunluk), DXF Y -> X (çap/yarıçap)
                # Y pozitif ise üst profil (dış torna için kullanılır)
                profile_pt = ProfilePoint(z=pt.x, x=pt.y)
                all_points.append(profile_pt)

        # Tekrarlayan noktaları kaldır ve sırala
        unique_points = self._remove_duplicates(all_points)

        return unique_points

    def _remove_duplicates(self, points: List[ProfilePoint], tolerance: float = 0.001) -> List[ProfilePoint]:
        """Tekrarlayan noktaları kaldır"""
        if not points:
            return []

        unique = [points[0]]
        for pt in points[1:]:
            is_duplicate = False
            for u in unique:
                if abs(pt.z - u.z) < tolerance and abs(pt.x - u.x) < tolerance:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(pt)

        return unique

    def _add_header(self, dxf_data: DXFData):
        """Başlık ekle"""
        self.gcode_lines.extend([
            "; =============================================",
            "; CNC TORNA - DXF'den G-Kod",
            f"; Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "; =============================================",
            f"; Kaynak: {dxf_data.file_path}",
            f"; Profil: {len(self.profile_points)} nokta",
            "; ---------------------------------------------",
            "; KOORDİNAT SİSTEMİ:",
            ";   X = Çap yönü (radyal)",
            ";   Z = Uzunluk yönü (eksenel)",
            "; ---------------------------------------------",
            f"; KABA PARÇA:",
            f";   Çap: {self.params.stock_diameter:.2f} mm",
            f";   Uzunluk: {self.params.stock_length:.2f} mm",
            f";   Yarıçap: {self.params.stock_diameter/2:.2f} mm",
            "; ---------------------------------------------",
            f"; TAKIM:",
            f";   Takım No: T{self.params.tool_number:02d}",
            f";   Bıçak Yarıçapı: {self.params.tool_radius:.2f} mm",
            f";   Yön: {self.params.tool_orientation}",
            "; ---------------------------------------------",
            f"; İŞLEM: {self.params.operation_type}",
            f";   Kaba Paso: {self.params.rough_depth:.2f} mm",
            f";   Finiş Payı: {self.params.finish_allowance:.2f} mm",
            f";   Kaba F: {self.params.rough_feed} mm/dak",
            f";   Finiş F: {self.params.finish_feed} mm/dak",
            f";   Devir: {self.params.spindle_speed} RPM",
            "; =============================================",
            "",
        ])

    def _add_startup(self):
        """Başlangıç kodları"""
        p = self.params
        self.gcode_lines.extend([
            "; === BAŞLANGIÇ ===",
            p.unit,  # G21 veya G20
            "G90 ; Mutlak koordinat",
            "G18 ; ZX düzlemi",
            "G40 ; Takım çapı kompanzasyonu iptal",
            "G54 ; İş koordinat sistemi",
            "",
            f"T{p.tool_number:02d}00 ; Takım seç",
            "M6 ; Takım değiştir",
            "",
            f"G97 S{p.spindle_speed} M3 ; Sabit devir, mil CW",
        ])

        if p.coolant:
            self.gcode_lines.append("M8 ; Soğutma aç")

        # Güvenli pozisyona git
        safe_x = p.stock_diameter / 2 + p.safe_x
        self.gcode_lines.extend([
            "",
            f"G0 X{safe_x:.3f} ; Güvenli X",
            f"G0 Z{p.clearance_z:.3f} ; Başlangıç Z",
            "",
        ])

    def _generate_roughing(self):
        """Kaba talaş döngüsü üret"""
        p = self.params

        self.gcode_lines.extend([
            "; =============================================",
            "; KABA TALAŞ DÖNGÜSÜ",
            "; =============================================",
            "",
        ])

        # Profil sınırlarını bul
        min_z = min(pt.z for pt in self.profile_points)
        max_z = max(pt.z for pt in self.profile_points)
        min_x = min(pt.x for pt in self.profile_points)  # En küçük çap/yarıçap

        # Kaba parça yarıçapı
        stock_radius = p.stock_diameter / 2

        # Finiş payı dahil hedef yarıçap
        target_with_allowance = min_x + p.finish_allowance + p.tool_radius

        # Paso sayısını hesapla
        material_to_remove = stock_radius - target_with_allowance
        if material_to_remove <= 0:
            self.gcode_lines.append("; Kaba talaş gerekmiyor - profil kaba parçanın dışında")
            return

        num_passes = math.ceil(material_to_remove / p.rough_depth)
        actual_depth = material_to_remove / num_passes

        self.gcode_lines.extend([
            f"; Kaldırılacak malzeme: {material_to_remove:.3f} mm (radyal)",
            f"; Paso sayısı: {num_passes}",
            f"; Gerçek paso derinliği: {actual_depth:.3f} mm",
            "",
        ])

        # Her paso için
        current_x = stock_radius
        for pass_num in range(num_passes):
            current_x -= actual_depth
            self.gcode_lines.append(f"; --- Kaba Paso {pass_num + 1}/{num_passes}, X={current_x:.3f} ---")

            # Kesim noktalarını hesapla (profil + offset)
            cut_points = self._calculate_roughing_path(current_x, min_z, max_z)

            # G-kod üret
            self._output_roughing_pass(cut_points, pass_num + 1)

        self.gcode_lines.append("")

    def _calculate_roughing_path(self, target_x: float, min_z: float, max_z: float) -> List[ProfilePoint]:
        """Kaba talaş kesim yolu hesapla"""
        p = self.params
        cut_points = []

        # Z boyunca ilerle ve profille kesişimi kontrol et
        z_start = p.clearance_z
        z_end = min_z - p.clearance_z

        # Profil noktalarını Z'ye göre sırala
        sorted_profile = sorted(self.profile_points, key=lambda pt: pt.z)

        # Başlangıç noktası (parça dışı)
        cut_points.append(ProfilePoint(z=z_start, x=target_x))

        # Profil boyunca ilerle
        for i, pt in enumerate(sorted_profile):
            # Profil noktası hedef X'in altındaysa (içerideyse)
            profile_x_with_offset = pt.x + p.finish_allowance + p.tool_radius

            if profile_x_with_offset > target_x:
                # Profil bu noktada hedefin dışında, profili takip et
                cut_points.append(ProfilePoint(z=pt.z, x=profile_x_with_offset))
            else:
                # Hedef X'te düz git
                cut_points.append(ProfilePoint(z=pt.z, x=target_x))

        # Bitiş (geri çekilme noktası)
        cut_points.append(ProfilePoint(z=z_end, x=target_x))

        return cut_points

    def _output_roughing_pass(self, points: List[ProfilePoint], pass_num: int):
        """Kaba talaş pasosu G-kod çıktısı"""
        p = self.params

        if not points:
            return

        safe_x = p.stock_diameter / 2 + p.safe_x

        # Başlangıç noktasına hızlı git
        first = points[0]
        self.gcode_lines.append(f"G0 Z{first.z:.3f}")
        self.gcode_lines.append(f"G0 X{first.x:.3f}")

        # İlerleme hızını ayarla
        self.gcode_lines.append(f"G1 F{p.rough_feed}")

        # Kesim noktaları boyunca ilerle
        for pt in points[1:]:
            self.gcode_lines.append(f"G1 X{pt.x:.3f} Z{pt.z:.3f}")

        # Geri çekil
        self.gcode_lines.append(f"G0 X{safe_x:.3f} ; Geri çekil")
        self.gcode_lines.append("")

    def _generate_finishing(self):
        """Finiş pasosu üret"""
        p = self.params

        self.gcode_lines.extend([
            "; =============================================",
            "; FİNİŞ PASOSU",
            "; =============================================",
            "",
        ])

        # Profil noktalarını bıçak yarıçapı ile offset'le
        finish_points = self._calculate_finish_path()

        if not finish_points:
            self.gcode_lines.append("; Finiş noktası bulunamadı")
            return

        safe_x = p.stock_diameter / 2 + p.safe_x

        # Başlangıç noktasına git
        first = finish_points[0]
        self.gcode_lines.extend([
            f"; Bıçak yarıçapı offset: {p.tool_radius:.3f} mm",
            f"; Profil noktası sayısı: {len(finish_points)}",
            "",
            f"G0 X{safe_x:.3f}",
            f"G0 Z{first.z + p.clearance_z:.3f}",
            f"G0 X{first.x + 1:.3f} ; Profil başına yaklaş",
            "",
            "; Takım yarıçapı kompanzasyonu",
            f"G42 ; Sağ kompanzasyon (G41: Sol)",
            "",
            f"G1 F{p.finish_feed}",
            f"G1 X{first.x:.3f} Z{first.z:.3f}",
        ])

        # Profil boyunca ilerle
        for pt in finish_points[1:]:
            self.gcode_lines.append(f"G1 X{pt.x:.3f} Z{pt.z:.3f}")

        # Kompanzasyonu kapat ve geri çekil
        last = finish_points[-1]
        self.gcode_lines.extend([
            "",
            "G40 ; Kompanzasyon iptal",
            f"G0 X{safe_x:.3f} ; Geri çekil",
            "",
        ])

    def _calculate_finish_path(self) -> List[ProfilePoint]:
        """Finiş yolu hesapla (bıçak yarıçapı offset'li)"""
        p = self.params
        finish_points = []

        # Profili Z'ye göre sırala
        sorted_profile = sorted(self.profile_points, key=lambda pt: pt.z)

        for pt in sorted_profile:
            # Bıçak yarıçapı offset'i ekle (dış torna için)
            offset_x = pt.x + p.tool_radius
            finish_points.append(ProfilePoint(z=pt.z, x=offset_x))

        return finish_points

    def _add_ending(self):
        """Bitiş kodları"""
        p = self.params
        safe_x = p.stock_diameter / 2 + p.safe_x

        self.gcode_lines.extend([
            "; =============================================",
            "; BİTİŞ",
            "; =============================================",
            "",
            f"G0 X{safe_x:.3f} ; Güvenli X",
            f"G0 Z{p.clearance_z:.3f} ; Başlangıç Z",
            "",
        ])

        if p.coolant:
            self.gcode_lines.append("M9 ; Soğutma kapat")

        self.gcode_lines.append("M5 ; Mil durdur")

        if p.home_after:
            self.gcode_lines.extend([
                "G28 U0 ; X Home",
                "G28 W0 ; Z Home",
            ])

        self.gcode_lines.extend([
            "M30 ; Program sonu",
            "",
            "; === PROGRAM SONU ===",
        ])


def generate_gcode_from_params(dxf_data: DXFData, params_dict: Dict) -> str:
    """Parametre sözlüğünden G-Kod üret"""
    params = TurningParams(
        stock_diameter=params_dict.get('stock_diameter', 50.0),
        stock_length=params_dict.get('stock_length', 100.0),
        tool_radius=params_dict.get('tool_radius', 0.4),
        tool_number=params_dict.get('tool_number', 1),
        tool_orientation=params_dict.get('tool_orientation', 3),
        rough_depth=params_dict.get('rough_depth', 1.0),
        finish_allowance=params_dict.get('finish_allowance', 0.2),
        operation_type=params_dict.get('operation_type', 'Kaba + Finiş'),
        rough_feed=params_dict.get('rough_feed', 150),
        finish_feed=params_dict.get('finish_feed', 80),
        spindle_speed=params_dict.get('spindle_speed', 1200),
        safe_x=params_dict.get('safe_x', 5.0),
        clearance_z=params_dict.get('clearance_z', 2.0),
        unit=params_dict.get('unit', 'G21'),
        home_after=params_dict.get('home_after', True),
        coolant=params_dict.get('coolant', False),
    )

    generator = LatheGCodeGenerator()
    return generator.generate(dxf_data, params)
