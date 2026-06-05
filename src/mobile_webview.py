"""Белпомощник — нативное мобильное приложение на Flet.

Показывает интерфейс программы (React-приложение из reactvitemaket) на телефоне
через нативный WebView. WebView работает на Android/iOS/desktop (но НЕ в web —
Flutter Web не умеет встраивать WebView).

Как запустить НА ТЕЛЕФОНЕ (dev, по Wi-Fi):
    1. Поднять React в сети:   cd reactvitemaket && pnpm dev:lan
       (vite --host → доступен по http://<IP-машины>:8560)
    2. На телефоне установить приложение «Flet» (Google Play / App Store),
       телефон и компьютер — в одной Wi-Fi сети.
    3. Запустить:   .venv/bin/flet run --android src/mobile_webview.py
       (для iPhone: --ios). На телефоне откроется интерфейс программы.

URL берётся из LAN-IP компьютера автоматически. Переопределить вручную:
    REACT_APP_URL=http://192.168.0.10:8560 .venv/bin/flet run --android src/mobile_webview.py

Отдельный установочный APK (нужен Flutter + Android SDK):
    .venv/bin/flet build apk

Локальная проверка на компьютере (окно с WebView):
    .venv/bin/flet run src/mobile_webview.py
"""

from __future__ import annotations

import os
import socket

import flet as ft
from flet_webview import WebView


def _lan_ip() -> str:
    """LAN-адрес компьютера, чтобы телефон достучался до dev-сервера React."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        sock.close()


REACT_URL = os.getenv("REACT_APP_URL", f"http://{_lan_ip()}:8560")


def main(page: ft.Page) -> None:
    page.title = "Белпомощник"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#F6F7FB"
    # Полноэкранный WebView: на телефоне приложение само является «рамкой».
    page.add(WebView(url=REACT_URL, expand=True))


if __name__ == "__main__":
    ft.run(main)
