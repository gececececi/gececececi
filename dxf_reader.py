#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF Dosya Okuyucu Modülü
ezdxf kütüphanesi ile DXF dosyalarını okur ve geometri verilerini çıkarır
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

import ezdxf
from ezdxf.entities import Line, Arc, Circle, LWPolyline, Polyline, Spline, Ellipse


class EntityType(Enum):
    """DXF entity tipleri"""
    LINE = "LINE"
    ARC = "ARC"
    CIRCLE = "CIRCLE"
    POLYLINE = "POLYLINE"
    SPLINE = "SPLINE"
    ELLIPSE = "ELLIPSE"
    POINT = "POINT"


@dataclass
class Point2D:
    """2D nokta"""
    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class LineEntity:
    """Çizgi entity'si"""
    entity_type: EntityType = EntityType.LINE
    start: Point2D = None
    end: Point2D = None
    layer: str = "0"

    def get_points(self) -> List[Point2D]:
        """Başlangıç ve bitiş noktalarını döndür"""
        return [self.start, self.end]


@dataclass
class ArcEntity:
    """Yay entity'si"""
    entity_type: EntityType = EntityType.ARC
    center: Point2D = None
    radius: float = 0.0
    start_angle: float = 0.0  # Derece cinsinden
    end_angle: float = 360.0  # Derece cinsinden
    layer: str = "0"

    def get_points(self, segments: int = 32) -> List[Point2D]:
        """Yayı noktalara dönüştür"""
        points = []
        start_rad = math.radians(self.start_angle)
        end_rad = math.radians(self.end_angle)

        # Açı farkını hesapla (CCW yönünde)
        if end_rad < start_rad:
            end_rad += 2 * math.pi

        angle_diff = end_rad - start_rad
        step = angle_diff / segments

        for i in range(segments + 1):
            angle = start_rad + (i * step)
            x = self.center.x + self.radius * math.cos(angle)
            y = self.center.y + self.radius * math.sin(angle)
            points.append(Point2D(x, y))

        return points


@dataclass
class CircleEntity:
    """Daire entity'si"""
    entity_type: EntityType = EntityType.CIRCLE
    center: Point2D = None
    radius: float = 0.0
    layer: str = "0"

    def get_points(self, segments: int = 64) -> List[Point2D]:
        """Daireyi noktalara dönüştür"""
        points = []
        for i in range(segments + 1):
            angle = (2 * math.pi * i) / segments
            x = self.center.x + self.radius * math.cos(angle)
            y = self.center.y + self.radius * math.sin(angle)
            points.append(Point2D(x, y))
        return points


@dataclass
class PolylineEntity:
    """Polyline entity'si"""
    entity_type: EntityType = EntityType.POLYLINE
    points: List[Point2D] = field(default_factory=list)
    is_closed: bool = False
    bulges: List[float] = field(default_factory=list)  # Yay bilgisi
    layer: str = "0"

    def get_points(self, arc_segments: int = 16) -> List[Point2D]:
        """Polyline noktalarını döndür (bulge'ları yaylara çevirerek)"""
        if not self.bulges or all(b == 0 for b in self.bulges):
            result = self.points.copy()
            if self.is_closed and len(result) > 0:
                result.append(result[0])
            return result

        # Bulge'ları işle
        result = []
        for i in range(len(self.points)):
            p1 = self.points[i]
            result.append(p1)

            if i < len(self.bulges) and self.bulges[i] != 0:
                # Sonraki nokta
                if i + 1 < len(self.points):
                    p2 = self.points[i + 1]
                elif self.is_closed:
                    p2 = self.points[0]
                else:
                    continue

                bulge = self.bulges[i]
                arc_points = self._bulge_to_arc(p1, p2, bulge, arc_segments)
                result.extend(arc_points[1:-1])  # İlk ve son nokta zaten eklendi

        if self.is_closed and len(result) > 0:
            result.append(result[0])

        return result

    def _bulge_to_arc(self, p1: Point2D, p2: Point2D, bulge: float, segments: int) -> List[Point2D]:
        """Bulge değerinden yay noktaları oluştur"""
        # Bulge = tan(açı/4)
        # Pozitif bulge: CCW, Negatif bulge: CW

        dx = p2.x - p1.x
        dy = p2.y - p1.y
        chord_length = math.sqrt(dx * dx + dy * dy)

        if chord_length == 0:
            return [p1, p2]

        # Yay açısı ve yarıçap hesapla
        s = bulge * chord_length / 2  # Sagitta (yay yüksekliği)
        radius = (chord_length / 2) / math.sin(2 * math.atan(abs(bulge)))

        # Merkez noktayı bul
        mid_x = (p1.x + p2.x) / 2
        mid_y = (p1.y + p2.y) / 2

        # Chord'a dik birim vektör
        if bulge > 0:
            nx = -dy / chord_length
            ny = dx / chord_length
        else:
            nx = dy / chord_length
            ny = -dx / chord_length

        # Merkez mesafesi
        h = radius - abs(s)

        center_x = mid_x + nx * h * (1 if bulge > 0 else -1)
        center_y = mid_y + ny * h * (1 if bulge > 0 else -1)

        # Açıları hesapla
        start_angle = math.atan2(p1.y - center_y, p1.x - center_x)
        end_angle = math.atan2(p2.y - center_y, p2.x - center_x)

        # Yay noktalarını oluştur
        if bulge > 0:  # CCW
            if end_angle < start_angle:
                end_angle += 2 * math.pi
        else:  # CW
            if start_angle < end_angle:
                start_angle += 2 * math.pi

        points = []
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + t * (end_angle - start_angle)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append(Point2D(x, y))

        return points


@dataclass
class SplineEntity:
    """Spline entity'si"""
    entity_type: EntityType = EntityType.SPLINE
    control_points: List[Point2D] = field(default_factory=list)
    fit_points: List[Point2D] = field(default_factory=list)
    layer: str = "0"

    def get_points(self, segments: int = 50) -> List[Point2D]:
        """Spline'ı noktalara dönüştür (basit interpolasyon)"""
        source_points = self.fit_points if self.fit_points else self.control_points
        if len(source_points) < 2:
            return source_points

        # Basit lineer interpolasyon (daha iyi için B-spline kullanılabilir)
        return source_points


@dataclass
class DXFData:
    """DXF dosyası verileri"""
    file_path: str = ""
    entities: List = field(default_factory=list)
    layers: List[str] = field(default_factory=list)
    bounds: Tuple[float, float, float, float] = (0, 0, 0, 0)  # min_x, min_y, max_x, max_y
    units: str = "mm"

    @property
    def width(self) -> float:
        return self.bounds[2] - self.bounds[0]

    @property
    def height(self) -> float:
        return self.bounds[3] - self.bounds[1]

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    def get_info_text(self) -> str:
        """DXF bilgi metni oluştur"""
        info = [
            f"Dosya: {self.file_path}",
            f"",
            f"Boyutlar:",
            f"  Genişlik (X): {self.width:.2f} {self.units}",
            f"  Yükseklik (Y): {self.height:.2f} {self.units}",
            f"  Min X: {self.bounds[0]:.2f}",
            f"  Max X: {self.bounds[2]:.2f}",
            f"  Min Y: {self.bounds[1]:.2f}",
            f"  Max Y: {self.bounds[3]:.2f}",
            f"",
            f"Entity Sayısı: {self.entity_count}",
            f"",
            f"Entity Tipleri:"
        ]

        # Entity tiplerini say
        type_counts = {}
        for entity in self.entities:
            type_name = entity.entity_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        for type_name, count in sorted(type_counts.items()):
            info.append(f"  {type_name}: {count}")

        info.extend([
            f"",
            f"Katmanlar: {len(self.layers)}",
        ])
        for layer in self.layers[:10]:  # İlk 10 katman
            info.append(f"  - {layer}")
        if len(self.layers) > 10:
            info.append(f"  ... ve {len(self.layers) - 10} katman daha")

        return "\n".join(info)


class DXFReader:
    """DXF dosya okuyucu"""

    def __init__(self):
        self.dxf_data: Optional[DXFData] = None

    def read_file(self, file_path: str) -> DXFData:
        """DXF dosyasını oku"""
        try:
            doc = ezdxf.readfile(file_path)
        except Exception as e:
            raise Exception(f"DXF dosyası okunamadı: {str(e)}")

        self.dxf_data = DXFData(file_path=file_path)

        # Modelspace'deki entity'leri oku
        msp = doc.modelspace()

        # Katmanları topla
        layers = set()

        # Sınır değerleri
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for entity in msp:
            parsed_entity = self._parse_entity(entity)
            if parsed_entity:
                self.dxf_data.entities.append(parsed_entity)
                layers.add(parsed_entity.layer)

                # Sınırları güncelle
                points = parsed_entity.get_points()
                for point in points:
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)

        # Sınırları kaydet
        if self.dxf_data.entities:
            self.dxf_data.bounds = (min_x, min_y, max_x, max_y)
        else:
            self.dxf_data.bounds = (0, 0, 0, 0)

        self.dxf_data.layers = sorted(list(layers))

        return self.dxf_data

    def _parse_entity(self, entity):
        """Entity'yi parse et"""
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            return self._parse_line(entity)
        elif entity_type == "ARC":
            return self._parse_arc(entity)
        elif entity_type == "CIRCLE":
            return self._parse_circle(entity)
        elif entity_type == "LWPOLYLINE":
            return self._parse_lwpolyline(entity)
        elif entity_type == "POLYLINE":
            return self._parse_polyline(entity)
        elif entity_type == "SPLINE":
            return self._parse_spline(entity)
        elif entity_type == "ELLIPSE":
            return self._parse_ellipse(entity)

        return None

    def _parse_line(self, entity) -> LineEntity:
        """LINE entity'sini parse et"""
        start = entity.dxf.start
        end = entity.dxf.end
        return LineEntity(
            start=Point2D(start.x, start.y),
            end=Point2D(end.x, end.y),
            layer=entity.dxf.layer
        )

    def _parse_arc(self, entity) -> ArcEntity:
        """ARC entity'sini parse et"""
        center = entity.dxf.center
        return ArcEntity(
            center=Point2D(center.x, center.y),
            radius=entity.dxf.radius,
            start_angle=entity.dxf.start_angle,
            end_angle=entity.dxf.end_angle,
            layer=entity.dxf.layer
        )

    def _parse_circle(self, entity) -> CircleEntity:
        """CIRCLE entity'sini parse et"""
        center = entity.dxf.center
        return CircleEntity(
            center=Point2D(center.x, center.y),
            radius=entity.dxf.radius,
            layer=entity.dxf.layer
        )

    def _parse_lwpolyline(self, entity) -> PolylineEntity:
        """LWPOLYLINE entity'sini parse et"""
        points = []
        bulges = []

        for x, y, start_width, end_width, bulge in entity.get_points(format='xyseb'):
            points.append(Point2D(x, y))
            bulges.append(bulge)

        return PolylineEntity(
            points=points,
            is_closed=entity.closed,
            bulges=bulges,
            layer=entity.dxf.layer
        )

    def _parse_polyline(self, entity) -> PolylineEntity:
        """POLYLINE entity'sini parse et"""
        points = []
        for vertex in entity.vertices:
            loc = vertex.dxf.location
            points.append(Point2D(loc.x, loc.y))

        return PolylineEntity(
            points=points,
            is_closed=entity.is_closed,
            layer=entity.dxf.layer
        )

    def _parse_spline(self, entity) -> SplineEntity:
        """SPLINE entity'sini parse et"""
        control_points = [Point2D(p.x, p.y) for p in entity.control_points]
        fit_points = [Point2D(p.x, p.y) for p in entity.fit_points]

        return SplineEntity(
            control_points=control_points,
            fit_points=fit_points,
            layer=entity.dxf.layer
        )

    def _parse_ellipse(self, entity) -> ArcEntity:
        """ELLIPSE entity'sini yaklaşık olarak parse et (basitleştirilmiş)"""
        # Elipsi çember olarak yaklaşık hesapla
        center = entity.dxf.center
        major_axis = entity.dxf.major_axis
        ratio = entity.dxf.ratio

        # Major axis uzunluğu
        radius = math.sqrt(major_axis.x**2 + major_axis.y**2)

        # Açıları derece cinsine çevir
        start_param = entity.dxf.start_param
        end_param = entity.dxf.end_param

        start_angle = math.degrees(start_param)
        end_angle = math.degrees(end_param)

        return ArcEntity(
            center=Point2D(center.x, center.y),
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle,
            layer=entity.dxf.layer
        )


def test_reader():
    """Test fonksiyonu"""
    reader = DXFReader()
    # Test için örnek DXF dosyası gerekir
    print("DXF Reader modülü yüklendi.")


if __name__ == "__main__":
    test_reader()
