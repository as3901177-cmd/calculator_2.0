"""
Генератор эталонных DXF файлов для тестирования расчёта длины реза
10 самых частых фигур в плазменной резке металла + эллипс
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
        self.create_ellipse()

        print(f"\n✓ Все тестовые файлы успешно созданы в папке:\n   {self.output_dir.resolve()}")

    def create_circle(self):
        """1. Круг Ø200 мм"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_circle((0, 0), radius=100)
        doc.saveas(self.output_dir / "01_circle_d200.dxf")
        print(f"✓ 1 Круг Ø200 мм → {2 * math.pi * 100:.3f} мм")

    def create_rectangle(self):
        """2. Прямоугольник 300×200 мм"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        points = [(0, 0), (300, 0), (300, 200), (0, 200)]
        msp.add_lwpolyline(points, close=True)
        doc.saveas(self.output_dir / "02_rectangle_300x200.dxf")
        print(f"✓ 2 Прямоугольник 300×200 мм → {2 * (300 + 200):.3f} мм")

    def create_square(self):
        """3. Квадрат 250×250 мм"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        points = [(0, 0), (250, 0), (250, 250), (0, 250)]
        msp.add_lwpolyline(points, close=True)
        doc.saveas(self.output_dir / "03_square_250.dxf")
        print(f"✓ 3 Квадрат 250×250 мм → {4 * 250:.3f} мм")

    def create_triangle(self):
        """4. Равносторонний треугольник со стороной 150 мм"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        h = 150 * math.sqrt(3) / 2
        points = [(0, 0), (150, 0), (75, h)]
        msp.add_lwpolyline(points, close=True)
        doc.saveas(self.output_dir / "04_triangle_s150.dxf")
        print(f"✓ 4 Треугольник 150 мм → {3 * 150:.3f} мм")

    def create_hexagon(self):
        """5. Шестигранник под ключ 100 мм"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        R = 100 / math.sqrt(3)  # радиус описанной окружности
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            points.append((R * math.cos(angle), R * math.sin(angle)))
        msp.add_lwpolyline(points, close=True)
        doc.saveas(self.output_dir / "05_hexagon_s100.dxf")
        expected = 200 * math.sqrt(3)
        print(f"✓ 5 Шестигранник 100 мм → {expected:.3f} мм")

    def create_flange(self):
        """6. Фланец Ø300 с центральным отверстием Ø100 и 4 отверстиями Ø20"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_circle((0, 0), radius=150)  # внешний
        msp.add_circle((0, 0), radius=50)   # центральное отверстие
        for angle in (45, 135, 225, 315):
            rad = math.radians(angle)
            x = 100 * math.cos(rad)
            y = 100 * math.sin(rad)
            msp.add_circle((x, y), radius=10)
        doc.saveas(self.output_dir / "06_flange_d300_4holes.dxf")
        expected = 2*math.pi*150 + 2*math.pi*50 + 4*2*math.pi*10
        print(f"✓ 6 Фланец с отверстиями → {expected:.3f} мм")

    def create_bracket(self):
        """7. L-образный кронштейн 200×150 мм с двумя отверстиями Ø16"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        points = [(0, 0), (200, 0), (200, 30), (30, 30), (30, 150), (0, 150)]
        msp.add_lwpolyline(points, close=True)
        msp.add_circle((100, 15), radius=8)
        msp.add_circle((15, 90), radius=8)
        doc.saveas(self.output_dir / "07_bracket_200x150.dxf")
        expected = 700 + 2 * 2 * math.pi * 8
        print(f"✓ 7 Кронштейн → {expected:.3f} мм")

    def create_ring(self):
        """8. Кольцо внешний Ø200, внутренний Ø100"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_circle((0, 0), radius=100)
        msp.add_circle((0, 0), radius=50)
        doc.saveas(self.output_dir / "08_ring_d200_d100.dxf")
        expected = 2*math.pi*100 + 2*math.pi*50
        print(f"✓ 8 Кольцо → {expected:.3f} мм")

    def create_slot(self):
        """9. Продолговатое отверстие 200×50 мм (овал)"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        w, h = 200.0, 50.0
        r = h / 2.0                     # радиус полуокружностей = 25 мм

        # Вершины с bulge: (x, y, bulge)
        # bulge=0 → прямолинейный сегмент, bulge=1 → полуокружность
        vertices = [
            (r, 0, 0),          # 0 → 1: нижняя прямая (150 мм)
            (w - r, 0, 1),      # 1 → 2: верхняя полуокружность (выпуклая вверх)
            (w - r, h, 0),      # 2 → 3: верхняя прямая (150 мм)
            (r, h, 1)           # 3 → 0: нижняя полуокружность (замыкание)
        ]

        # ВАЖНО: указываем format='xyb', чтобы ezdxf правильно сохранил bulge
        msp.add_lwpolyline(vertices, format='xyb', close=True)

        doc.saveas(self.output_dir / "09_slot_200x50.dxf")

        # Ожидаемая длина: две прямых + две полуокружности
        expected = 2 * (w - 2 * r) + 2 * math.pi * r
        print(f"✓ 9 Продолговатое отверстие → {expected:.3f} мм")

    def create_complex_part(self):
        """10. Сложная деталь: пластина 300×200 с вырезом, центральным отверстием и крепежом"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Единый внешний контур с выемкой 50×50 мм справа по центру
        points = [
            (0, 0),           # 0
            (300, 0),         # 1
            (300, 75),        # 2
            (250, 75),        # 3
            (250, 125),       # 4
            (300, 125),       # 5
            (300, 200),       # 6
            (0, 200)          # 7
        ]
        msp.add_lwpolyline(points, close=True)

        # Центральное отверстие Ø60 мм
        msp.add_circle((150, 100), radius=30)

        # Крепёжные отверстия Ø10 мм
        msp.add_circle((20, 20), radius=5)
        msp.add_circle((280, 180), radius=5)

        doc.saveas(self.output_dir / "10_complex_part.dxf")

        # Ожидаемая длина:
        #   периметр внешнего контура = 2*(300+200) - 50 + 3*50 = 1100 мм
        #   окружность Ø60 = 2π·30 ≈ 188.50 мм
        #   2 окружности Ø10 = 2 * 2π·5 ≈ 62.83 мм
        expected = 1100 + 2 * math.pi * 30 + 2 * 2 * math.pi * 5
        print(f"✓ 10 Сложная деталь → {expected:.3f} мм")

    def create_ellipse(self):
        """11. Эллипс с полуосями 100 и 50 мм (замкнутый)"""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        a = 100.0
        b = 50.0
        msp.add_ellipse(
            center=(0, 0),
            major_axis=(a, 0),
            ratio=b/a,
            start_param=0,
            end_param=2 * math.pi
        )
        # Численное интегрирование периметра
        num_segments = 200
        dt = 2 * math.pi / num_segments
        t = 0.0
        total_length = 0.0
        x_prev = a * math.cos(t)
        y_prev = b * math.sin(t)
        for _ in range(num_segments):
            t += dt
            x_curr = a * math.cos(t)
            y_curr = b * math.sin(t)
            total_length += math.hypot(x_curr - x_prev, y_curr - y_prev)
            x_prev, y_prev = x_curr, y_curr
        doc.saveas(self.output_dir / "11_ellipse_100x50.dxf")
        print(f"✓ 11 Эллипс 100×50 → {total_length:.3f} мм")


def main():
    generator = TestFixturesGenerator()
    generator.create_all_fixtures()
    print("\n" + "=" * 70)
    print("ГЕНЕРАЦИЯ ТЕСТОВЫХ DXF ФАЙЛОВ ЗАВЕРШЕНА УСПЕШНО")
    print("=" * 70)


if __name__ == "__main__":
    main()
