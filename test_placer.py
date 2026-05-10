from shapely.geometry import Polygon, box
from dxf_analyzer.nesting.algorithms.placer import place_parts_in_order
from dxf_analyzer.nesting.nesting_config import NestingConfig

# Прямоугольный лист 1000x800 мм
sheet = box(0, 0, 1000, 800)

# Две детали: квадрат 100x100 и прямоугольник 200x100
part1 = box(0, 0, 100, 100)
part2 = box(0, 0, 200, 100)

parts = [part1, part2]
rotations = [0, 45]  # вторую повернём на 45°

config = NestingConfig(part_spacing=5, edge_margin=10)
placements, unplaced = place_parts_in_order(sheet, parts, rotations, config)

print("Размещённые:")
for p in placements:
    print(f"  Деталь {p.part_index}: ({p.x:.2f}, {p.y:.2f}), угол {p.rotation}°")
print("Неразмещённые:", unplaced)