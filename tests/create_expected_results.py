"""
Создание файла с эталонными результатами расчётов длины реза
"""

import json
import math
from pathlib import Path


def create_expected_results():
    """Генерация эталонных данных для тестов"""
   
    test_cases = [
        {
            "id": 1,
            "name": "Круг (заготовка под фланец)",
            "file": "01_circle_d200.dxf",
            "description": "Круг Ø200мм",
            "expected_length": 2 * math.pi * 100,
            "tolerance": 0.01,
            "category": "basic"
        },
        {
            "id": 2,
            "name": "Прямоугольник (пластина)",
            "file": "02_rectangle_300x200.dxf",
            "description": "Прямоугольник 300x200мм",
            "expected_length": 2 * (300 + 200),
            "tolerance": 0.01,
            "category": "basic"
        },
        {
            "id": 3,
            "name": "Квадрат (базовая пластина)",
            "file": "03_square_250.dxf",
            "description": "Квадрат 250x250мм",
            "expected_length": 4 * 250,
            "tolerance": 0.01,
            "category": "basic"
        },
        {
            "id": 4,
            "name": "Треугольник (косынка)",
            "file": "04_triangle_s150.dxf",
            "description": "Равносторонний треугольник со стороной 150мм",
            "expected_length": 3 * 150,
            "tolerance": 0.01,
            "category": "basic"
        },
        {
            "id": 5,
            "name": "Шестигранник (гайка)",
            "file": "05_hexagon_s100.dxf",
            "description": "Шестигранник под ключ 100мм",
            "expected_length": 100 * math.sqrt(3),        # 6 * (100 / √3 * √3/2) = 100√3
            "tolerance": 0.1,
            "category": "basic"
        },
        {
            "id": 6,
            "name": "Фланец с отверстиями",
            "file": "06_flange_d300_4holes.dxf",
            "description": "Фланец Ø300 с центральным отверстием Ø100 и 4 отв. Ø20",
            "expected_length": (
                2 * math.pi * 150 +
                2 * math.pi * 50 +
                8 * math.pi * 10
            ),
            "tolerance": 0.5,
            "category": "complex"
        },
        {
            "id": 7,
            "name": "Кронштейн (уголок)",
            "file": "07_bracket_200x150.dxf",
            "description": "L-образный кронштейн 200x150мм с двумя отверстиями Ø16",
            "expected_length": 700.0 + 4 * math.pi * 8,   # Периметр внешнего контура ≈700 + отверстия
            "tolerance": 1.0,
            "category": "complex"
        },
        {
            "id": 8,
            "name": "Кольцо (шайба)",
            "file": "08_ring_d200_d100.dxf",
            "description": "Кольцо внешний Ø200, внутренний Ø100",
            "expected_length": 2 * math.pi * (100 + 50),
            "tolerance": 0.1,
            "category": "basic"
        },
        {
            "id": 9,
            "name": "Продолговатое отверстие",
            "file": "09_slot_200x50.dxf",
            "description": "Овальное отверстие 200x50мм",
            "expected_length": 2 * (200 - 50) + 2 * math.pi * 25,
            "tolerance": 0.5,
            "category": "medium"
        },
        {
            "id": 10,
            "name": "Сложная деталь",
            "file": "10_complex_part.dxf",
            "description": "Пластина 300x200 с вырезом 50x50 в углу, Ø60 и 2×Ø10",
            "expected_length": (
                2 * (300 + 200) +      # Внешний периметр = 1000
                4 * 50 +               # ← ИСПРАВЛЕНО: полный периметр выреза = 200 мм
                2 * math.pi * 30 +     # Центральное отверстие Ø60
                4 * math.pi * 5        # Два отверстия Ø10
            ),
            "tolerance": 1.0,
            "category": "complex"
        }
    ]
   
    # Сохранение в JSON
    output_dir = Path("tests/fixtures")
    output_dir.mkdir(parents=True, exist_ok=True)
   
    output_file = output_dir / "expected_results.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"test_cases": test_cases}, f, indent=2, ensure_ascii=False)
   
    print(f"✓ Эталонные данные сохранены в {output_file}\n")

    # Красивая таблица
    print("="*110)
    print(f"{'ID':<3} {'Название':<38} {'Ожидаемая длина (мм)':<22} {'Допуск'}")
    print("="*110)
    for tc in test_cases:
        print(f"{tc['id']:<3} {tc['name']:<38} {tc['expected_length']:>18.2f} {'±' + str(tc['tolerance']):>8}")
    print("="*110)

    return test_cases


if __name__ == "__main__":
    create_expected_results()
