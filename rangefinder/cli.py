"""CLI: live / photo / calibrate."""
import argparse
import json
import time
from collections import deque

import cv2
import numpy as np

from .calib import load_calib, px_to_mm, save_calib
from .camera import open_camera
from .detect import find_spots, spot_distance_px


def run_photo(args):
    _, a, b = load_calib(args.calib)
    for f in args.files:
        img = cv2.imread(f)
        if img is None:
            print(f"{f}: не удалось открыть"); continue
        pts = find_spots(img, args.color, args.thr)
        if pts is None:
            print(f"{f}: пятна не найдены"); continue
        p = spot_distance_px(pts)
        d = px_to_mm(p, a, b)
        print(f"{f}: p = {p:.2f} px  ->  " + (f"D = {d:.0f} мм" if d else "нет калибровки / вне диапазона"))


def _open(args):
    return open_camera(args.camera, args.cam, args.width, args.height, args.exposure, args.gain)


def run_live(args):
    points, a, b = load_calib(args.calib)
    cam = _open(args)
    hist = deque(maxlen=15)                      # медианное сглаживание
    last_print = 0.0
    try:
        while True:
            frame = cam.read()
            if frame is None:
                break
            pts = find_spots(frame, args.color, args.thr)
            p = d = None
            if pts:
                hist.append(spot_distance_px(pts))
                p = float(np.median(hist))
                d = px_to_mm(p, a, b)
            else:
                hist.clear()

            if args.headless:
                now = time.time()
                if now - last_print >= args.interval:
                    last_print = now
                    if args.json:
                        print(json.dumps({"t": round(now, 3), "p_px": p, "d_mm": d}), flush=True)
                    elif p is None:
                        print("пятна не найдены", flush=True)
                    else:
                        print(f"p={p:.1f}px  " + (f"D={d:.0f} мм" if d else "нет калибровки"), flush=True)
                continue

            text = "пятна не найдены"
            if pts:
                text = f"p={p:.1f}px  " + (f"D={d / 10:.1f} см" if d else "нет калибровки")
                for (x, y) in pts:
                    cv2.circle(frame, (int(round(x)), int(round(y))), 8, (0, 255, 0), 1)
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.imshow("rangefinder  [c]=calib  [q]=quit", frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                break
            if k == ord("c") and hist:
                try:
                    dist = float(input("Реальное расстояние до объекта, мм: "))
                except ValueError:
                    continue
                points.append((dist, float(np.median(hist))))
                a, b = save_calib(args.calib, points)
                print(f"Точек: {len(points)}, a={a:.1f}, b={b:.2f}")
    except KeyboardInterrupt:
        pass
    finally:
        cam.close()
        if not args.headless:
            cv2.destroyAllWindows()


def run_calibrate(args):
    """Безголовая калибровка по SSH: python -m rangefinder calibrate --distance 1000"""
    points, _, _ = load_calib(args.calib)
    cam = _open(args)
    ps = []
    try:
        time.sleep(0.5)                          # дать камере прогреться
        for _ in range(args.frames * 3):
            frame = cam.read()
            pts = find_spots(frame, args.color, args.thr) if frame is not None else None
            if pts:
                ps.append(spot_distance_px(pts))
            if len(ps) >= args.frames:
                break
    finally:
        cam.close()
    if len(ps) < args.frames // 2:
        raise SystemExit(f"Пятна найдены только в {len(ps)} кадрах, калибровка отменена")
    p = float(np.median(ps))
    points.append((args.distance, p))
    a, b = save_calib(args.calib, points)
    print(f"D={args.distance} мм, p={p:.2f} px (разброс σ={np.std(ps):.2f}); точек: {len(points)}, a={a:.1f}, b={b:.2f}")


def main():
    ap = argparse.ArgumentParser(prog="rangefinder")
    sub = ap.add_subparsers(dest="mode", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--calib", default="calib.json")
    common.add_argument("--color", default="red", choices=["red", "green", "blue"])
    common.add_argument("--thr", type=int, default=200, help="мин. яркость пятна 0..255")

    cam = argparse.ArgumentParser(add_help=False)
    cam.add_argument("--camera", default="auto", choices=["auto", "opencv", "picamera2"])
    cam.add_argument("--cam", type=int, default=0, help="индекс для OpenCV")
    cam.add_argument("--width", type=int, default=1280)
    cam.add_argument("--height", type=int, default=720)
    cam.add_argument("--exposure", type=float, default=None,
                     help="ручная экспозиция (picamera2: мкс; OpenCV: зависит от драйвера)")
    cam.add_argument("--gain", type=float, default=1.0)

    p = sub.add_parser("photo", parents=[common]); p.add_argument("files", nargs="+")
    p.set_defaults(fn=run_photo)

    p = sub.add_parser("live", parents=[common, cam])
    p.add_argument("--headless", action="store_true", help="без окна, вывод в stdout (для RPi/службы)")
    p.add_argument("--json", action="store_true", help="в headless печатать JSON-строки")
    p.add_argument("--interval", type=float, default=0.5, help="период вывода в headless, с")
    p.set_defaults(fn=run_live)

    p = sub.add_parser("calibrate", parents=[common, cam])
    p.add_argument("--distance", type=float, required=True, help="реальное расстояние, мм")
    p.add_argument("--frames", type=int, default=30)
    p.set_defaults(fn=run_calibrate)

    args = ap.parse_args()
    args.fn(args)
