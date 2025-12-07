; =============================================
; CNC TORNA - DXF'den G-Kod
; Tarih: 2025-12-07 11:33:26
; =============================================
; Kaynak: test_lathe_profile.dxf
; Profil: 6 nokta
; ---------------------------------------------
; KOORDİNAT SİSTEMİ:
;   X = Çap yönü (radyal)
;   Z = Uzunluk yönü (eksenel)
; ---------------------------------------------
; KABA PARÇA:
;   Çap: 50.00 mm
;   Uzunluk: 100.00 mm
;   Yarıçap: 25.00 mm
; ---------------------------------------------
; TAKIM:
;   Takım No: T01
;   Bıçak Yarıçapı: 0.40 mm
;   Yön: 3
; ---------------------------------------------
; İŞLEM: Kaba + Finiş
;   Kaba Paso: 2.00 mm
;   Finiş Payı: 0.20 mm
;   Kaba F: 150 mm/dak
;   Finiş F: 80 mm/dak
;   Devir: 1200 RPM
; =============================================

; === BAŞLANGIÇ ===
G21
G90 ; Mutlak koordinat
G18 ; ZX düzlemi
G40 ; Takım çapı kompanzasyonu iptal
G54 ; İş koordinat sistemi

T0100 ; Takım seç
M6 ; Takım değiştir

G97 S1200 M3 ; Sabit devir, mil CW

G0 X30.000 ; Güvenli X
G0 Z2.000 ; Başlangıç Z

; =============================================
; KABA TALAŞ DÖNGÜSÜ
; =============================================

; Kaldırılacak malzeme: 14.400 mm (radyal)
; Paso sayısı: 8
; Gerçek paso derinliği: 1.800 mm

; --- Kaba Paso 1/8, X=23.200 ---
G0 Z2.000
G0 X23.200
G1 F150
G1 X23.200 Z0.000
G1 X23.200 Z20.000
G1 X23.200 Z20.000
G1 X23.200 Z50.000
G1 X23.200 Z50.000
G1 X23.200 Z80.000
G1 X23.200 Z-2.000
G0 X30.000 ; Geri çekil

; --- Kaba Paso 2/8, X=21.400 ---
G0 Z2.000
G0 X21.400
G1 F150
G1 X21.400 Z0.000
G1 X21.400 Z20.000
G1 X21.400 Z20.000
G1 X21.400 Z50.000
G1 X21.400 Z50.000
G1 X21.400 Z80.000
G1 X21.400 Z-2.000
G0 X30.000 ; Geri çekil

; --- Kaba Paso 3/8, X=19.600 ---
G0 Z2.000
G0 X19.600
G1 F150
G1 X20.600 Z0.000
G1 X20.600 Z20.000
G1 X19.600 Z20.000
G1 X19.600 Z50.000
G1 X19.600 Z50.000
G1 X19.600 Z80.000
G1 X19.600 Z-2.000
G0 X30.000 ; Geri çekil

; --- Kaba Paso 4/8, X=17.800 ---
G0 Z2.000
G0 X17.800
G1 F150
G1 X20.600 Z0.000
G1 X20.600 Z20.000
G1 X17.800 Z20.000
G1 X17.800 Z50.000
G1 X17.800 Z50.000
G1 X17.800 Z80.000
G1 X17.800 Z-2.000
G0 X30.000 ; Geri çekil

; --- Kaba Paso 5/8, X=16.000 ---
G0 Z2.000
G0 X16.000
G1 F150
G1 X20.600 Z0.000
G1 X20.600 Z20.000
G1 X16.000 Z20.000
G1 X16.000 Z50.000
G1 X16.000 Z50.000
G1 X16.000 Z80.000
G1 X16.000 Z-2.000
G0 X30.000 ; Geri çekil

; --- Kaba Paso 6/8, X=14.200 ---
G0 Z2.000
G0 X14.200
G1 F150
G1 X20.600 Z0.000
G1 X20.600 Z20.000
G1 X15.600 Z20.000
G1 X15.600 Z50.000
G1 X14.200 Z50.000
G1 X14.200 Z80.000
G1 X14.200 Z-2.000
G0 X30.000 ; Geri çekil

; --- Kaba Paso 7/8, X=12.400 ---
G0 Z2.000
G0 X12.400
G1 F150
G1 X20.600 Z0.000
G1 X20.600 Z20.000
G1 X15.600 Z20.000
G1 X15.600 Z50.000
G1 X12.400 Z50.000
G1 X12.400 Z80.000
G1 X12.400 Z-2.000
G0 X30.000 ; Geri çekil

; --- Kaba Paso 8/8, X=10.600 ---
G0 Z2.000
G0 X10.600
G1 F150
G1 X20.600 Z0.000
G1 X20.600 Z20.000
G1 X15.600 Z20.000
G1 X15.600 Z50.000
G1 X10.600 Z50.000
G1 X10.600 Z80.000
G1 X10.600 Z-2.000
G0 X30.000 ; Geri çekil


; =============================================
; FİNİŞ PASOSU
; =============================================

; Bıçak yarıçapı offset: 0.400 mm
; Profil noktası sayısı: 6

G0 X30.000
G0 Z2.000
G0 X21.400 ; Profil başına yaklaş

; Takım yarıçapı kompanzasyonu
G42 ; Sağ kompanzasyon (G41: Sol)

G1 F80
G1 X20.400 Z0.000
G1 X20.400 Z20.000
G1 X15.400 Z20.000
G1 X15.400 Z50.000
G1 X10.400 Z50.000
G1 X10.400 Z80.000

G40 ; Kompanzasyon iptal
G0 X30.000 ; Geri çekil

; =============================================
; BİTİŞ
; =============================================

G0 X30.000 ; Güvenli X
G0 Z2.000 ; Başlangıç Z

M5 ; Mil durdur
G28 U0 ; X Home
G28 W0 ; Z Home
M30 ; Program sonu

; === PROGRAM SONU ===