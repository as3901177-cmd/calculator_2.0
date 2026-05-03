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
        self.create_ellipse()          # <-- добавлен вызов

        print(f"\n✓ Все тестовые файлы успешно созданы в папке:\n   {self.output_dir.resolve()}")

    # ... все предыдущие методы create_circle, create_rectangle и т.д. без изменений ...

    def create_ellipse(self):
        """11. Эллипс с полуосями 100 и 50 мм (замкнутый)"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        a = 100.0  # большая полуось
        b = 50.0   # малая полуось
        msp.add_ellipse(
            center=(0, 0),
            major_axis=(a, 0),
            ratio=b/a,
            start_param=0,
            end_param=2 * math.pi
        )

        # Численное интегрирование периметра (как в калькуляторе)
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

        expected_length = total_length

        doc.saveas(self.output_dir / "11_ellipse_100x50.dxf")
        print(f"✓ 11 Эллипс 100×50       → {expected_length:.3f} мм")
        return expected_length


def main():
    generator = TestFixturesGenerator()
    generator.create_all_fixtures()

    print("\n" + "=" * 70)
    print("ГЕНЕРАЦИЯ ТЕСТОВЫХ DXF ФАЙЛОВ ЗАВЕРШЕНА УСПЕШНО")
    print("=" * 70)


if __name__ == "__main__":
    main()
