#!/usr/bin/env bash
# Установка на Raspberry Pi OS (Bookworm, 64-bit). Запуск: bash scripts/setup_rpi.sh
set -euo pipefail

sudo apt update
sudo apt install -y python3-opencv python3-numpy python3-picamera2 python3-venv git

# --system-site-packages, чтобы venv видел apt-версии opencv и picamera2
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e . --no-deps

echo
echo "Готово. Проверка камеры:  rpicam-hello -t 2000"
echo "Калибровка:               .venv/bin/python -m rangefinder calibrate --distance 1000 --exposure 2000"
echo "Измерение:                .venv/bin/python -m rangefinder live --headless --exposure 2000"
