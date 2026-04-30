"""
Генератор эталонных DXF файлов для тестирования расчёта длины реза
10 самых частых фигур в плазменной резке металла
"""

import ezdxf
import math
from pathlib import Path


class TestFixturesGenerator:
    """Генератор тестовых DXF файлов для проверки расчёта длины реза"""

    def __init__(self, output_dir="tests/fixtures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_all_fixtures(self):
        """Создать все тестовые фигуры"""
        print("Генерация тестовых DXF файлов...\n")

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

        print(f"\n✓ Все тестовые файлы успешно созданы в папке:\n   {self.output_dir.resolve()}")

    def create_circle(self):
        """1. Круг Ø200 мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        radius = 100.0
        msp.add_circle((0, 0), radius=radius)

        expected_length = 2 * math.pi * radius

        doc.saveas(self.output_dir / "01_circle_d200.dxf")
        print(f"✓ 01 Круг Ø200          → {expected_length:.3f} мм")
        return expected_length

    def create_rectangle(self):
        """2. Прямоугольник 300×200 мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        width, height = 300.0, 200.0
        points = [(0, 0), (width, 0), (width, height), (0, height)]
        msp.add_lwpolyline(points, close=True)

        expected_length = 2 * (width + height)

        doc.saveas(self.output_dir / "02_rectangle_300x200.dxf")
        print(f"✓ 02 Прямоугольник 300×200 → {expected_length:.3f} мм")
        return expected_length

    def create_square(self):
        """3. Квадрат 250×250 мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        side = 250.0
        points = [(0, 0), (side, 0), (side, side), (0, side)]
        msp.add_lwpolyline(points, close=True)

        expected_length = 4 * side

        doc.saveas(self.output_dir / "03_square_250.dxf")
        print(f"✓ 03 Квадрат 250×250     → {expected_length:.3f} мм")
        return expected_length

    def create_triangle(self):
        """4. Равносторонний треугольник со стороной 150 мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        side = 150.0
        height = side * math.sqrt(3) / 2

        points = [(0, 0), (side, 0), (side / 2, height)]
        msp.add_lwpolyline(points, close=True)

        expected_length = 3 * side

        doc.saveas(self.output_dir / "04_triangle_s150.dxf")
        print(f"✓ 04 Треугольник 150     → {expected_length:.3f} мм")
        return expected_length

    def create_hexagon(self):
        """5. Шестигранник (размер под ключ 100 мм)"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        size_across_flats = 100.0
        # Радиус описанной окружности для шестигранника "под ключ"
        radius = size_across_flats / math.sqrt(3)

        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append((x, y))

        msp.add_lwpolyline(points, close=True)

        # Правильная длина одной стороны шестигранника
        side_length = size_across_flats / 2 * math.sqrt(3)   # или 2 * radius * sin(π/6)
        expected_length = 6 * side_length

        doc.saveas(self.output_dir / "05_hexagon_s100.dxf")
        print(f"✓ 05 Шестигранник 100    → {expected_length:.3f} мм")
        return expected_length

    def create_flange(self):
        """6. Фланец Ø300 мм с центральным отверстием Ø100 и 4 отверстиями Ø20"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        outer_radius = 150.0
        center_hole_radius = 50.0
        hole_radius = 10.0
        pcd = 110.0

        msp.add_circle((0, 0), radius=outer_radius)
        msp.add_circle((0, 0), radius=center_hole_radius)

        for i in range(4):
            angle = math.pi / 2 * i
            x = pcd * math.cos(angle)
            y = pcd * math.sin(angle)
            msp.add_circle((x, y), radius=hole_radius)

        expected_length = (
            2 * math.pi * outer_radius +
            2 * math.pi * center_hole_radius +
            4 * 2 * math.pi * hole_radius
        )

        doc.saveas(self.output_dir / "06_flange_d300_4holes.dxf")
        print(f"✓ 06 Фланец Ø300         → {expected_length:.3f} мм")
        return expected_length

    def create_bracket(self):
        """7. Кронштейн (L-образный) 200×150 мм с двумя отверстиями Ø16"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        points = [
            (0, 0), (200, 0), (200, 50), (50, 50),
            (50, 150), (0, 150)
        ]
        msp.add_lwpolyline(points, close=True)

        msp.add_circle((25, 25), radius=8)
        msp.add_circle((25, 125), radius=8)

        # Расчёт периметра внешнего контура
        outer_length = 0.0
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            outer_length += math.hypot(x2 - x1, y2 - y1)

        holes_length = 4 * math.pi * 8  # 2 отверстия

        expected_length = outer_length + holes_length

        doc.saveas(self.output_dir / "07_bracket_200x150.dxf")
        print(f"✓ 07 Кронштейн 200×150   → {expected_length:.3f} мм")
        return expected_length

    def create_ring(self):
        """8. Кольцо (шайба) Ø200 / Ø100"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        outer_radius = 100.0
        inner_radius = 50.0

        msp.add_circle((0, 0), radius=outer_radius)
        msp.add_circle((0, 0), radius=inner_radius)

        expected_length = 2 * math.pi * (outer_radius + inner_radius)

        doc.saveas(self.output_dir / "08_ring_d200_d100.dxf")
        print(f"✓ 08 Кольцо Ø200/100     → {expected_length:.3f} мм")
        return expected_length

    def create_slot(self):
        """9. Продолговатое отверстие (овал) 200×50 мм"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        length = 200.0
        width = 50.0
        r = width / 2

        # Левый полукруг
        msp.add_arc(center=(r, r), radius=r, start_angle=90, end_angle=270)
        # Правый полукруг
        msp.add_arc(center=(length - r, r), radius=r, start_angle=270, end_angle=90)
        # Верхняя прямая
        msp.add_line((r, width), (length - r, width))
        # Нижняя прямая
        msp.add_line((r, 0), (length - r, 0))

        straight = length - width
        arcs = 2 * math.pi * r          # два полукруга = одна полная окружность

        expected_length = 2 * straight + arcs

        doc.saveas(self.output_dir / "09_slot_200x50.dxf")
        print(f"✓ 09 Овал 200×50         → {expected_length:.3f} мм")
        return expected_length

    def create_complex_part(self):
        """10. Сложная деталь — прямоугольник 300×200 с вырезом, отверстиями"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # Основная пластина
        base_points = [(0, 0), (300, 0), (300, 200), (0, 200)]
        msp.add_lwpolyline(base_points, close=True)

        # Вырез 50×50 в правом верхнем углу
        cutout_points = [(250, 150), (300, 150), (300, 200), (250, 200)]
        msp.add_lwpolyline(cutout_points, close=True)

        # Центральное отверстие Ø60
        msp.add_circle((150, 100), radius=30)

        # Два монтажных отверстия Ø10
        msp.add_circle((50, 50), radius=5)
        msp.add_circle((250, 50), radius=5)

        # === Правильный расчёт длины реза ===
        outer_perimeter = 2 * (300 + 200)      # 1000 мм
        cutout_perimeter = 4 * 50              # 200 мм — важно! полный периметр выреза
        center_hole = 2 * math.pi * 30
        mounting_holes = 4 * math.pi * 5       # 2 отверстия

        expected_length = outer_perimeter + cutout_perimeter + center_hole + mounting_holes

        doc.saveas(self.output_dir / "10_complex_part.dxf")
        print(f"✓ 10 Сложная деталь      → {expected_length:.3f} мм")
        return expected_length


def main():
    generator = TestFixturesGenerator()
    generator.create_all_fixtures()

    print("\n" + "=" * 70)
    print("ГЕНЕРАЦИЯ ТЕСТОВЫХ DXF ФАЙЛОВ ЗАВЕРШЕНА УСПЕШНО")
    print("=" * 70)


if __name__ == "__main__":
    main()
