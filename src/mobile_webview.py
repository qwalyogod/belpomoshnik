"""Белпомощник — нативная мобильная оболочка.

Файл оставляет Flet только как тонкую оболочку вокруг основного web-интерфейса.
На текущем dev-этапе первым экраном остается ввод адреса приложения. После
переезда на постоянный сервер этот экран можно заменить статичным URL из env.

Ориентация
----------
На ТЕЛЕФОНАХ (iOS/Android, shortest ≤ 600 AND longest ≤ 1100) ориентация
жёстко фиксируется в PORTRAIT_UP через set_allowed_device_orientations —
это даёт нативный UX и предотвращает «планшетный» поворот на узких экранах,
где UX приложения рассчитан на вертикаль.

На ПЛАНШЕТАХ (iPad / Android tablet) ориентация остаётся СВОБОДНОЙ —
пользователь явно просил так. Ширина 600+/длина 1100+ пропускает их
через _is_phone() и не блокирует.

Дополнительная защита от «ложного WebView»: см. _server_reachable,
_internet_reachable и show_offline / show_server_error. Если React-приложение
присылает событие connection (через postMessage), обёртка переключается на
соответствующий экран.
"""

from __future__ import annotations

import asyncio
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import flet as ft
from flet_webview import WebView


def _lan_ip() -> str:
    """LAN-адрес компьютера для локальной разработки по Wi-Fi."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        sock.close()


APP_URL = os.getenv("BELPOMOSHNIK_APP_URL") or os.getenv("REACT_APP_URL") or f"http://{_lan_ip()}:8560"
DEBUG_WEBVIEW = os.getenv("BELPOMOSHNIK_WEBVIEW_DEBUG", "0") == "1"

PHONE_MAX_SHORTEST_SIDE = 600
PHONE_MAX_LONGEST_SIDE = 1100


def _normalize_url(raw: str) -> str:
    value = raw.strip()
    if value and "://" not in value:
        value = f"http://{value}"
    return value.rstrip("/")


def _app_host_label(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url


def _internet_reachable() -> bool:
    for host in ("1.1.1.1", "8.8.8.8"):
        try:
            with socket.create_connection((host, 53), timeout=1.5):
                return True
        except OSError:
            continue
    return False


def _server_reachable(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return False, "Некорректный адрес"

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=2):
            pass
    except OSError as exc:
        return False, str(exc)

    try:
        request = Request(url, headers={"User-Agent": "BelpomoshnikShell/1.0"})
        with urlopen(request, timeout=3) as response:  # noqa: S310 - dev/local health check.
            if 200 <= response.status < 500:
                return True, f"HTTP {response.status}"
            return False, f"HTTP {response.status}"
    except HTTPError as exc:
        if exc.code < 500:
            return True, f"HTTP {exc.code}"
        return False, f"HTTP {exc.code}"
    except (OSError, URLError) as exc:
        return False, str(exc)


def _looks_like_offline_error(data: object) -> bool:
    text = str(data).lower()
    offline_markers = (
        "internet",
        "notconnectedtointernet",
        "network is unreachable",
        "err_internet_disconnected",
        "err_network_changed",
        "the internet connection appears to be offline",
    )
    return any(marker in text for marker in offline_markers)


def _is_phone(page: ft.Page) -> bool:
    platform = getattr(page, "platform", None)
    if platform not in (ft.PagePlatform.IOS, ft.PagePlatform.ANDROID):
        return False

    width = float(page.width or 0)
    height = float(page.height or 0)
    if not width or not height:
        return False

    shortest = min(width, height)
    longest = max(width, height)
    return shortest <= PHONE_MAX_SHORTEST_SIDE and longest <= PHONE_MAX_LONGEST_SIDE


def _palette(page: ft.Page) -> dict[str, str]:
    is_dark = page.platform_brightness == ft.Brightness.DARK
    if is_dark:
        return {
            "bg": "#070A12",
            "surface": "#111827",
            "surface_2": "#172033",
            "text": "#F8FAFC",
            "muted": "#AAB4C5",
            "border": "#263247",
            "primary": "#3B82F6",
            "primary_text": "#FFFFFF",
            "danger": "#F87171",
            "warning": "#FBBF24",
        }
    return {
        "bg": "#F5F7FB",
        "surface": "#FFFFFF",
        "surface_2": "#EEF4FF",
        "text": "#111827",
        "muted": "#64748B",
        "border": "#DCE5F5",
        "primary": "#2563EB",
        "primary_text": "#FFFFFF",
        "danger": "#EF4444",
        "warning": "#F59E0B",
    }


def main(page: ft.Page) -> None:
    page.title = "Белпомощник"
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.SYSTEM

    last_url = {"value": APP_URL}
    orientation_applied = {"done": False}

    def apply_shell_theme() -> None:
        colors = _palette(page)
        page.bgcolor = colors["bg"]

    def lock_phone_orientation_if_needed() -> None:
        if orientation_applied["done"] or not _is_phone(page):
            return
        try:
            page.set_allowed_device_orientations([ft.DeviceOrientation.PORTRAIT_UP])
            orientation_applied["done"] = True
            print("[shell] portrait orientation locked for phone viewport")
        except Exception as exc:  # noqa: BLE001
            print(f"[shell] orientation lock unavailable: {exc}")

    def root(control: ft.Control) -> ft.SafeArea:
        return ft.SafeArea(
            expand=True,
            minimum_padding=ft.padding.only(left=16, top=12, right=16, bottom=16),
            content=control,
        )

    def brand_mark(size: int = 48) -> ft.Container:
        colors = _palette(page)
        return ft.Container(
            width=size,
            height=size,
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#1D4ED8", colors["primary"]],
            ),
            alignment=ft.alignment.center,
            content=ft.Text("Б", size=size * 0.46, weight=ft.FontWeight.W_700, color="#FFFFFF"),
        )

    def primary_button(label: str, icon: str, on_click) -> ft.FilledButton:
        colors = _palette(page)
        return ft.FilledButton(
            label,
            icon=icon,
            on_click=on_click,
            height=48,
            style=ft.ButtonStyle(
                bgcolor=colors["primary"],
                color=colors["primary_text"],
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

    def secondary_button(label: str, icon: str, on_click) -> ft.OutlinedButton:
        colors = _palette(page)
        return ft.OutlinedButton(
            label,
            icon=icon,
            on_click=on_click,
            height=48,
            style=ft.ButtonStyle(
                color=colors["text"],
                side=ft.BorderSide(1, colors["border"]),
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

    def shell_card(
        icon: str,
        title: str,
        text: str,
        controls: list[ft.Control],
        accent: str | None = None,
    ) -> ft.Container:
        colors = _palette(page)
        accent_color = accent or colors["primary"]
        return ft.Container(
            width=440,
            padding=24,
            border_radius=28,
            bgcolor=colors["surface"],
            border=ft.border.all(1, colors["border"]),
            shadow=ft.BoxShadow(
                blur_radius=24,
                spread_radius=0,
                color="#1E293B1A",
                offset=ft.Offset(0, 12),
            ),
            content=ft.Column(
                [
                    brand_mark(52),
                    ft.Container(
                        width=52,
                        height=52,
                        border_radius=18,
                        bgcolor=colors["surface_2"],
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, color=accent_color, size=28),
                    ),
                    ft.Text(title, size=24, weight=ft.FontWeight.W_700, color=colors["text"]),
                    ft.Text(text, size=15, color=colors["muted"], text_align=ft.TextAlign.CENTER),
                    *controls,
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
        )

    url_field = ft.TextField(
        value=APP_URL,
        label="Адрес приложения",
        hint_text="http://192.168.0.10:8560",
        text_size=15,
        autofocus=True,
        keyboard_type=ft.KeyboardType.URL,
        on_submit=lambda e: page.run_task(open_url),
        border_radius=14,
    )

    def replace(control: ft.Control) -> None:
        apply_shell_theme()
        lock_phone_orientation_if_needed()
        page.clean()
        page.add(root(control))
        page.update()

    def show_connection_form(message: str | None = None, error: bool = False) -> None:
        colors = _palette(page)
        helper: ft.Control
        if message:
            helper = ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                border_radius=14,
                bgcolor="#FEF2F2" if error else colors["surface_2"],
                content=ft.Text(
                    message,
                    size=13,
                    color=colors["danger"] if error else colors["muted"],
                    text_align=ft.TextAlign.CENTER,
                ),
            )
        else:
            helper = ft.Text(
                "Для разработки укажите адрес, который доступен с этого устройства.",
                size=13,
                color=colors["muted"],
                text_align=ft.TextAlign.CENTER,
            )

        controls: list[ft.Control] = [
            helper,
            url_field,
            ft.Row(
                [primary_button("Подключиться", ft.Icons.ARROW_FORWARD, lambda e: page.run_task(open_url))],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ]
        if DEBUG_WEBVIEW:
            controls.append(secondary_button("Проверить оболочку", ft.Icons.BUG_REPORT, lambda e: page.run_task(test_shell)))

        replace(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=shell_card(
                    ft.Icons.LINK,
                    "Подключение к Белпомощнику",
                    "Введите адрес приложения и нажмите «Подключиться».",
                    controls,
                ),
            )
        )

    def show_loading(url: str) -> None:
        colors = _palette(page)
        replace(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Container(
                    width=420,
                    padding=28,
                    border_radius=28,
                    bgcolor=colors["surface"],
                    border=ft.border.all(1, colors["border"]),
                    content=ft.Column(
                        [
                            brand_mark(56),
                            ft.ProgressRing(width=42, height=42, stroke_width=4, color=colors["primary"]),
                            ft.Text("Загрузка приложения", size=24, weight=ft.FontWeight.W_700, color=colors["text"]),
                            ft.Text(
                                f"Открываем Белпомощник: {_app_host_label(url)}",
                                size=14,
                                color=colors["muted"],
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        spacing=16,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                    ),
                ),
            )
        )

    def show_offline() -> None:
        replace(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=shell_card(
                    ft.Icons.WIFI_OFF,
                    "Нет подключения к интернету",
                    "Проверьте сеть на устройстве и попробуйте снова.",
                    [
                        ft.Row(
                            [
                                primary_button("Попробовать снова", ft.Icons.REFRESH, lambda e: page.run_task(retry)),
                                secondary_button("Изменить адрес", ft.Icons.EDIT, lambda e: show_connection_form()),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            wrap=True,
                            spacing=10,
                        )
                    ],
                    accent=_palette(page)["danger"],
                ),
            )
        )

    def show_server_error(detail: str | None = None) -> None:
        console_detail = f" ({detail})" if detail else ""
        print(f"[shell] server/site error{console_detail}")
        replace(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=shell_card(
                    ft.Icons.CLOUD_OFF,
                    "Сервис временно недоступен",
                    "Сервер не ответил или страница не загрузилась. Попробуйте обновить подключение.",
                    [
                        ft.Row(
                            [
                                primary_button("Попробовать снова", ft.Icons.REFRESH, lambda e: page.run_task(retry)),
                                secondary_button("Изменить адрес", ft.Icons.EDIT, lambda e: show_connection_form()),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            wrap=True,
                            spacing=10,
                        )
                    ],
                    accent=_palette(page)["warning"],
                ),
            )
        )

    def on_started(e: ft.ControlEvent) -> None:
        print(f"[webview] start -> {e.data}")

    def on_progress(e: ft.ControlEvent) -> None:
        print(f"[webview] progress -> {e.data}%")

    def on_ended(e: ft.ControlEvent) -> None:
        print(f"[webview] loaded -> {e.data}")

    def on_error(e: ft.ControlEvent) -> None:
        print(f"[webview] resource error -> {e.data}")
        if _looks_like_offline_error(e.data):
            show_offline()
            return
        show_server_error(str(e.data))

    def on_console(e) -> None:
        print(f"[web:{getattr(e, 'severity_level', '?')}] {getattr(e, 'message', e)}")

    webview = WebView(
        url="about:blank",
        expand=True,
        on_page_started=on_started,
        on_page_ended=on_ended,
        on_web_resource_error=on_error,
        on_progress=on_progress,
        on_console_message=on_console,
    )

    async def open_url(_=None) -> None:
        url = _normalize_url(url_field.value or "")
        if not url:
            show_connection_form("Введите адрес приложения.", error=True)
            return

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            show_connection_form("Адрес должен начинаться с http:// или https://.", error=True)
            return

        last_url["value"] = url
        url_field.value = url
        print(f"[shell] open -> {url}")
        show_loading(url)

        server_ok, server_info = await asyncio.to_thread(_server_reachable, url)
        if not server_ok:
            internet_ok = await asyncio.to_thread(_internet_reachable)
            if not internet_ok:
                print(f"[shell] offline detected while opening {url}: {server_info}")
                show_offline()
                return
            show_server_error(server_info)
            return

        print(f"[shell] server reachable: {server_info}")
        page.clean()
        page.add(webview)
        page.update()
        await asyncio.sleep(0.25)
        await webview.load_request(url)

    async def retry(_=None) -> None:
        url_field.value = last_url["value"]
        await open_url()

    async def test_shell(_=None) -> None:
        page.clean()
        page.add(webview)
        page.update()
        await asyncio.sleep(0.25)
        await webview.load_html(
            "<!doctype html><html><body style='margin:0;background:#0f172a;color:#fff;"
            "font:700 36px system-ui;display:flex;align-items:center;justify-content:center;"
            "height:100vh'>Белпомощник</body></html>"
        )

    def on_resize(_=None) -> None:
        lock_phone_orientation_if_needed()

    def on_brightness_change(_=None) -> None:
        # Нативные shell-экраны должны следовать системной теме.
        show_connection_form() if not page.controls else page.update()

    page.on_resize = on_resize
    page.on_platform_brightness_change = on_brightness_change

    apply_shell_theme()
    show_connection_form()


if __name__ == "__main__":
    ft.run(main)
