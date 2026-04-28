# tests/generate_test_fixtures.py
"""
Генератор эталонных DXF файлов для тестирования расчёта длины реза
10 самых частых фигур в плазменной резке металла
"""

import ezdxf
import math
from pathlib import Path


class TestFixturesGenerator:
    """Генератор тестовых DXF файлов"""
    
    def __init__(self, output_dir="tests/fixtures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_all_fixtures(self):
        """Создать все тестовые фигуры"""
        print("Генерация тестовых DXF файлов...")
        
        self.create_circle()
        self.create_rectangle()
        self.create_square()
        self.create_triangle()
        self.create_hexagon()
        self.create_flange()
        self.create_bracket()
        self.create_ring()
        self.create_slot()
        self.create_complex_part()
        
        print(f"✓ Все тестовые файлы созданы в {self.output_dir}")
    
    def create_circle(self):
        """1. Круг (заготовка под фланец) - Ø200мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        radius = 100  # Ø200
        msp.add_circle((0, 0), radius=radius)
        
        expected_length = 2 * math.pi * radius
        
        doc.saveas(self.output_dir / "01_circle_d200.dxf")
        print(f"✓ Круг Ø200: длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_rectangle(self):
        """2. Прямоугольник (пластина) - 300x200мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        width, height = 300, 200
        points = [
            (0, 0),
            (width, 0),
            (width, height),
            (0, height)
        ]
        msp.add_lwpolyline(points, close=True)
        
        expected_length = 2 * (width + height)
        
        doc.saveas(self.output_dir / "02_rectangle_300x200.dxf")
        print(f"✓ Прямоугольник 300x200: длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_square(self):
        """3. Квадрат (базовая пластина) - 250x250мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        side = 250
        points = [
            (0, 0),
            (side, 0),
            (side, side),
            (0, side)
        ]
        msp.add_lwpolyline(points, close=True)
        
        expected_length = 4 * side
        
        doc.saveas(self.output_dir / "03_square_250.dxf")
        print(f"✓ Квадрат 250x250: длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_triangle(self):
        """4. Равносторонний треугольник (косынка) - сторона 150мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        side = 150
        height = side * math.sqrt(3) / 2
        
        points = [
            (0, 0),
            (side, 0),
            (side/2, height)
        ]
        msp.add_lwpolyline(points, close=True)
        
        expected_length = 3 * side
        
        doc.saveas(self.output_dir / "04_triangle_s150.dxf")
        print(f"✓ Треугольник (сторона 150): длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_hexagon(self):
        """5. Шестигранник (гайка) - размер под ключ 100мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Радиус описанной окружности
        size_across_flats = 100  # Размер под ключ
        radius = size_across_flats / math.sqrt(3)
        
        points = []
        for i in range(6):
            angle = math.pi / 3 * i  # 60 градусов
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append((x, y))
        
        msp.add_lwpolyline(points, close=True)
        
        side_length = radius  # Для правильного шестиугольника
        expected_length = 6 * side_length
        
        doc.saveas(self.output_dir / "05_hexagon_s100.dxf")
        print(f"✓ Шестигранник (под ключ 100): длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_flange(self):
        """6. Фланец (круг с отверстиями) - Ø300 с 4 отв. Ø20"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Внешний контур
        outer_radius = 150  # Ø300
        msp.add_circle((0, 0), radius=outer_radius)
        
        # Центральное отверстие
        center_hole_radius = 50  # Ø100
        msp.add_circle((0, 0), radius=center_hole_radius)
        
        # 4 крепёжных отверстия
        hole_radius = 10  # Ø20
        hole_pcd = 110  # Диаметр расположения отверстий
        
        for i in range(4):
            angle = math.pi / 2 * i  # 90 градусов
            x = hole_pcd * math.cos(angle)
            y = hole_pcd * math.sin(angle)
            msp.add_circle((x, y), radius=hole_radius)
        
        expected_length = (
            2 * math.pi * outer_radius +  # Внешний контур
            2 * math.pi * center_hole_radius +  # Центральное отверстие
            4 * 2 * math.pi * hole_radius  # 4 крепёжных отверстия
        )
        
        doc.saveas(self.output_dir / "06_flange_d300_4holes.dxf")
        print(f"✓ Фланец Ø300 с отверстиями: длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_bracket(self):
        """7. Кронштейн (уголок) - 200x150мм с отверстиями"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Внешний контур L-образной детали
        points = [
            (0, 0),
            (200, 0),
            (200, 50),
            (50, 50),
            (50, 150),
            (0, 150)
        ]
        msp.add_lwpolyline(points, close=True)
        
        # Два крепёжных отверстия
        msp.add_circle((25, 25), radius=8)  # Ø16
        msp.add_circle((25, 125), radius=8)  # Ø16
        
        # Расчёт периметра внешнего контура
        outer_length = 0
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            outer_length += math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        
        holes_length = 2 * 2 * math.pi * 8  # 2 отверстия Ø16
        expected_length = outer_length + holes_length
        
        doc.saveas(self.output_dir / "07_bracket_200x150.dxf")
        print(f"✓ Кронштейн 200x150: длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_ring(self):
        """8. Кольцо (шайба) - Ø200/Ø100"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        outer_radius = 100  # Ø200
        inner_radius = 50   # Ø100
        
        msp.add_circle((0, 0), radius=outer_radius)
        msp.add_circle((0, 0), radius=inner_radius)
        
        expected_length = (
            2 * math.pi * outer_radius +
            2 * math.pi * inner_radius
        )
        
        doc.saveas(self.output_dir / "08_ring_d200_d100.dxf")
        print(f"✓ Кольцо Ø200/Ø100: длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_slot(self):
        """9. Продолговатое отверстие (овал) - 200x50мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        length = 200
        width = 50
        radius = width / 2
        
        # Два полукруга и две линии
        # Левый полукруг
        msp.add_arc(
            center=(radius, width/2),
            radius=radius,
            start_angle=90,
            end_angle=270
        )
        
        # Правый полукруг
        msp.add_arc(
            center=(length - radius, width/2),
            radius=radius,
            start_angle=270,
            end_angle=90
        )
        
        # Верхняя линия
        msp.add_line((radius, width), (length - radius, width))
        
        # Нижняя линия
        msp.add_line((radius, 0), (length - radius, 0))
        
        straight_part = length - 2 * radius
        arc_part = 2 * math.pi * radius  # Два полукруга = полная окружность
        
        expected_length = 2 * straight_part + arc_part
        
        doc.saveas(self.output_dir / "09_slot_200x50.dxf")
        print(f"✓ Овал 200x50: длина реза = {expected_length:.3f} мм")
        
        return expected_length
    
    def create_complex_part(self):
        """10. Сложная деталь (комбинация элементов)"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Основная прямоугольная пластина 300x200
        base_points = [
            (0, 0),
            (300, 0),
            (300, 200),
            (0, 200)
        ]
        msp.add_lwpolyline(base_points, close=True)
        
        # Вырез в углу (прямоугольный) 50x50
        cutout_points = [
            (250, 150),
            (300, 150),
            (300, 200),
            (250, 200)
        ]
        # Для выреза добавляем отдельные линии
        for i in range(len(cutout_points)):
            p1 = cutout_points[i]
            p2 = cutout_points[(i + 1) % len(cutout_points)]
            msp.add_line(p1, p2)
        
        # Центральное круглое отверстие Ø60
        msp.add_circle((150, 100), radius=30)
        
        # Два крепёжных отверстия Ø10
        msp.add_circle((50, 50), radius=5)
        msp.add_circle((250, 50), radius=5)
        
        # Расчёт длины реза
        base_perimeter = 2 * (300 + 200)
        cutout_length = 2 * 50  # Только две стороны выреза (две другие - на границе)
        center_hole = 2 * math.pi * 30
        mounting_holes = 2 * 2 * math.pi * 5
        
        expected_length = base_perimeter + cutout_length + center_hole + mounting_holes
        
        doc.saveas(self.output_dir / "10_complex_part.dxf")
        print(f"✓ Сложная деталь: длина реза = {expected_length:.3f} мм")
        
        return expected_length


def main():
    """Генерация всех тестовых файлов"""
    generator = TestFixturesGenerator()
    generator.create_all_fixtures()
    print("\n" + "="*60)
    print("Тестовые DXF файлы успешно созданы!")
    print("="*60)


if __name__ == "__main__":
    main()