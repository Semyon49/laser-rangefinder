# laser-rangefinder

Дальномер по двум лазерным пятнам и камере. Лазеры стоят на базе 95 мм и слегка расходятся
(на 1 м между пятнами 120 мм). Расстояние между пятнами в пикселях `p` связано с дальностью `D`:

```
p = a/D + b      ->      D = a / (p − b)
```

Параметры `a` и `b` находятся калибровкой по нескольким известным расстояниям (`calib.json`).
Точность падает как `ΔD ≈ D²·Δp / a`, поэтому пятна ищутся с субпиксельной точностью.

## Установка

**Windows / ПК**
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[gui]"
```

**Raspberry Pi 4** (Raspberry Pi OS 64-bit)
```bash
git clone <URL репозитория> && cd laser-rangefinder
bash scripts/setup_rpi.sh
```

## Использование

```bash
# окно с видео, 'c' - добавить точку калибровки, 'q' - выход
python -m rangefinder live

# по фото
python -m rangefinder photo img1.jpg img2.jpg

# без монитора (SSH, служба): вывод в консоль или JSON-строками
python -m rangefinder live --headless --json

# калибровка по SSH: поставьте мишень на известное расстояние и запустите
python -m rangefinder calibrate --distance 500
python -m rangefinder calibrate --distance 1000
python -m rangefinder calibrate --distance 1500
```

Камера выбирается автоматически: `picamera2` (CSI на RPi), иначе OpenCV (USB/веб-камера).
Принудительно: `--camera opencv|picamera2`.

## Важно при переезде на Raspberry Pi

- **Калибровку нужно повторить.** Другая камера/объектив/разрешение дают другое `f_px`, значит другие `a` и `b`.
  Файл `calib.json` с Windows переносить нельзя, если сменилась камера или разрешение.
- **Фиксируйте экспозицию** (`--exposure`, для picamera2 в микросекундах; подберите так, чтобы фон был тёмным,
  а пятна яркими, но не пересвеченными). Автоэкспозиция и автобаланс белого сдвигают центроиды.
- Разрешение при калибровке и при измерении должно совпадать.
- Для автозапуска используйте `deploy/rangefinder.service` (systemd).

## Структура

```
rangefinder/   detect.py (пятна), calib.py (калибровка), camera.py (OpenCV/Picamera2), cli.py
tests/         синтетические тесты детектора и калибровки
scripts/       setup_rpi.sh
deploy/        systemd-служба
```

## Тесты

```bash
pip install -e ".[headless,dev]" && pytest
```
