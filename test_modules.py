#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNC Torna Modül Test Script'i
DXF okuma ve G-Kod üretimi test eder
"""

from dxf_reader import DXFReader
from gcode_generator import generate_gcode_from_params

def test_lathe_profile():
    """Torna profili testi"""
    print("=" * 60)
    print("CNC TORNA - DXF Profil ve G-Kod Testi")
    print("=" * 60)

    # DXF oku
    reader = DXFReader()
    dxf_data = reader.read_file("test_lathe_profile.dxf")

    print("\n--- DXF BİLGİLERİ ---")
    print(dxf_data.get_info_text())

    # Torna parametreleri
    params = {
        # Kaba parça - çap 50mm, uzunluk 100mm
        'stock_diameter': 50.0,
        'stock_length': 100.0,
        # Takım
        'tool_radius': 0.4,  # 0.4mm bıçak yarıçapı
        'tool_number': 1,
        'tool_orientation': 3,
        # Tornalama
        'rough_depth': 2.0,  # 2mm paso
        'finish_allowance': 0.2,  # 0.2mm finiş payı
        'operation_type': 'Kaba + Finiş',
        # Hareket
        'rough_feed': 150,
        'finish_feed': 80,
        'spindle_speed': 1200,
        'safe_x': 5.0,
        'clearance_z': 2.0,
        # Diğer
        'unit': 'G21',
        'home_after': True,
        'coolant': False,
    }

    print("\n--- PARAMETRELER ---")
    print(f"Kaba Parça: Ø{params['stock_diameter']} x {params['stock_length']} mm")
    print(f"Bıçak Yarıçapı: {params['tool_radius']} mm")
    print(f"Kaba Paso: {params['rough_depth']} mm")
    print(f"Finiş Payı: {params['finish_allowance']} mm")
    print(f"İşlem: {params['operation_type']}")

    # G-Kod üret
    print("\n--- G-KOD ÜRETİLİYOR ---")
    gcode = generate_gcode_from_params(dxf_data, params)

    print("\n" + "=" * 60)
    print("ÜRETİLEN G-KOD:")
    print("=" * 60)
    print(gcode)
    print("=" * 60)
    print(f"Toplam satır: {len(gcode.strip().split(chr(10)))}")

    # G-Kodu dosyaya kaydet
    with open("output_lathe.nc", "w") as f:
        f.write(gcode)
    print(f"\nG-Kod kaydedildi: output_lathe.nc")

    return True


if __name__ == "__main__":
    try:
        test_lathe_profile()
        print("\n✓ Test başarılı!")
    except Exception as e:
        print(f"\n✗ HATA: {e}")
        import traceback
        traceback.print_exc()
