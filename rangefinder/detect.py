"""Детекция двух лазерных пятен и расстояние между ними в пикселях."""
import cv2
import numpy as np


def find_spots(img, color="red", thr=200, min_area=3, max_area=3000):
    """Возвращает [(x, y), (x, y)] субпиксельные центры двух пятен (слева направо) или None."""
    b, g, r = cv2.split(img)
    ch = {"red": r, "green": g, "blue": b}[color].astype(np.float32)
    ch = cv2.GaussianBlur(ch, (0, 0), 1.0)

    t = max(float(thr), 0.7 * float(ch.max()))
    mask = (ch >= t).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    cands = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if not (min_area <= area <= max_area):
            continue
        x0, y0 = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
        w, h = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        if max(w, h) > 3 * min(w, h):           # отсекаем вытянутые блики
            continue
        roi = ch[y0:y0 + h, x0:x0 + w] * (labels[y0:y0 + h, x0:x0 + w] == i)
        wgt = np.clip(roi - t * 0.5, 0, None)   # взвешенный центроид
        s = wgt.sum()
        if s <= 0:
            continue
        ys, xs = np.mgrid[y0:y0 + h, x0:x0 + w]
        cands.append(((xs * wgt).sum() / s, (ys * wgt).sum() / s, s))

    if len(cands) < 2:
        return None
    cands.sort(key=lambda c: -c[2])             # два самых ярких
    pts = sorted(cands[:2], key=lambda c: c[0])
    return [(pts[0][0], pts[0][1]), (pts[1][0], pts[1][1])]


def spot_distance_px(pts):
    (x1, y1), (x2, y2) = pts
    return float(np.hypot(x2 - x1, y2 - y1))
