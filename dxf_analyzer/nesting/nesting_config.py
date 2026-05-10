"""
Конфигурационные параметры для всех алгоритмов раскроя.
"""
from dataclasses import dataclass


@dataclass
class NestingConfig:
    sheet_width: float = 2000.0
    sheet_height: float = 1500.0
    part_spacing: float = 3.0          # зазор между деталями
    edge_margin: float = 5.0           # отступ от края листа
    clipper_scale: int = 1_000_000     # масштаб для целочисленных операций pyclipper
    rotation_step_default: float = 15.0 # шаг поворота в градусах для универсального алгоритма
    ga_population_size: int = 50
    ga_mutation_rate: float = 0.1
    ga_iterations: int = 100