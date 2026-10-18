import numpy as np
from rangefinder.calib import fit_calibration, px_to_mm
from rangefinder.detect import find_spots, spot_distance_px


def synth(p, w=640, h=480, sigma=2.0):
    img = np.zeros((h, w, 3), np.uint8)
    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    for x in (cx - p / 2, cx + p / 2):
        g = 255 * np.exp(-((xs - x) ** 2 + (ys - cy) ** 2) / (2 * sigma ** 2))
        img[..., 2] = np.maximum(img[..., 2], g.astype(np.uint8))
    return img


def test_detect_subpixel():
    pts = find_spots(synth(123.4))
    assert pts is not None
    assert abs(spot_distance_px(pts) - 123.4) < 0.5


def test_no_spots():
    assert find_spots(np.zeros((100, 100, 3), np.uint8)) is None


def test_calibration_roundtrip():
    a, b = 95_000.0, 25.0
    pts = [(d, a / d + b) for d in (300, 600, 1000, 1500)]
    fa, fb = fit_calibration(pts)
    assert abs(fa - a) < 1e-6 and abs(fb - b) < 1e-6
    assert abs(px_to_mm(a / 800 + b, fa, fb) - 800) < 1e-6


def test_out_of_range():
    assert px_to_mm(10, 95000, 25) is None
