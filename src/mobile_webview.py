"""Мобильный просмотр (НАТИВНЫЙ): Flet-обёртка с WebView, показывающая
React-приложение (reactvitemaket, http://localhost:8560) внутри телефонной рамки.

ВАЖНО: WebView рендерится только в desktop/mobile-режиме Flet. В web-режиме
(`flet run -w`) Flutter Web не умеет встраивать WebView — экран будет пустым.
Для просмотра В БРАУЗЕРЕ используйте страницу-обёртку:
    cd reactvitemaket && pnpm mobile   →  откроет http://localhost:8560/mobile.html

Нативный запуск (откроет окно-телефон через WebView):
    .venv/bin/flet run src/mobile_webview.py

Требует запущенный React dev-сервер на :8560.
"""

from __future__ import annotations

import os

import flet as ft
from flet_webview import WebView

REACT_URL = os.getenv("REACT_APP_URL", "http://localhost:8560")


def main(page: ft.Page) -> None:
    page.title = "Белпомощник — мобильный просмотр"
    page.padding = 0
    page.bgcolor = "#0B0D13"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    webview = WebView(url=REACT_URL, expand=True)

    # Телефонная рамка вокруг web-view.
    phone = ft.Container(
        width=390,
        height=844,
        bgcolor="#000000",
        border_radius=44,
        padding=10,
        content=ft.Container(
            content=webview,
            border_radius=34,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor="#F6F7FB",
            expand=True,
        ),
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Белпомощник · мобильный просмотр", size=13, color="#9AA3B2"),
                    phone,
                    ft.Text(REACT_URL, size=11, color="#5A6473"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
            padding=20,
        )
    )


if __name__ == "__main__":
    ft.run(main)
