"""Калибровка: p = a/D + b  ->  D = a / (p - b). Формат calib.json совместим с версией 0.1."""
import json
from pathlib import Path

import numpy as np

BASE_MM = 95.0                     # расстояние между лазерами у источника
K_NOM = (120.0 - 95.0) / 1000.0    # прирост расстояния между пятнами на 1 мм дальности


def fit_calibration(points):
    """points = [(D_mm, p_px), ...] -> (a, b)."""
    if not points:
        raise ValueError("нет точек калибровки")
    if len(points) == 1:                         # одна точка: номинальная геометрия
        D, p = points[0]
        f_px = p / ((BASE_MM + K_NOM * D) / D)
        return BASE_MM * f_px, K_NOM * f_px
    x = np.array([1.0 / d for d, _ in points])
    y = np.array([p for _, p in points])
    a, b = np.polyfit(x, y, 1)
    return float(a), float(b)


def load_calib(path):
    path = Path(path)
    if path.exists():
        c = json.loads(path.read_text())
        return [tuple(p) for p in c["points"]], c["a"], c["b"]
    return [], None, None


def save_calib(path, points):
    a, b = fit_calibration(points)
    Path(path).write_text(json.dumps({"points": points, "a": a, "b": b}, indent=2))
    return a, b


def px_to_mm(p, a, b):
    if a is None or p <= b:
        return None                              # вне диапазона / нет калибровки
    return a / (p - b)
