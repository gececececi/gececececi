#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modül Test Script'i
DXF okuma ve G-Kod üretimi test eder
"""

from dxf_reader import DXFReader
from gcode_generator import generate_gcode_from_params, GCodeParams

def test_dxf_reader():
    """DXF okuyucu test"""
    print("=" * 50)
    print("DXF Okuyucu Testi")
    print("=" * 50)

    reader = DXFReader()
    dxf_data = reader.read_file("test_sample.dxf")

    print(dxf_data.get_info_text())
    print()

    return dxf_data


def test_gcode_generator(dxf_data):
    """G-Kod üretici test"""
    print("=" * 50)
    print("G-Kod Üretici Testi")
    print("=" * 50)

    params = {
        'machine_type': 'CNC Torna',
        'unit': 'G21',
        'feed_rate': 100,
        'plunge_rate': 50,
        'spindle_speed': 1000,
        'cut_depth': 1.0,
        'pass_depth': 0.5,
        'safe_height': 5.0,
        'start_x': 0.0,
        'start_y': 0.0,
        'home_after': True
    }

    gcode = generate_gcode_from_params(dxf_data, params)

    print("Üretilen G-Kod:")
    print("-" * 50)
    print(gcode)
    print("-" * 50)
    print(f"Toplam satır: {len(gcode.strip().split(chr(10)))}")


if __name__ == "__main__":
    try:
        dxf_data = test_dxf_reader()
        test_gcode_generator(dxf_data)
        print("\nTüm testler başarılı!")
    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        traceback.print_exc()
