"""Белпомощник — нативное мобильное приложение на Flet.

Показывает интерфейс программы (React-приложение из reactvitemaket) на телефоне
через нативный WebView. WebView работает на Android/iOS/desktop (но НЕ в web —
Flutter Web не умеет встраивать WebView).

ВАЖНО про сеть: при `flet run --android/--ios` Python-код выполняется на КОМПЬЮТЕРЕ,
а сам WebView рендерится на ТЕЛЕФОНЕ и грузит URL уже из сети телефона. Значит
телефон должен достучаться до dev-сервера React на компьютере по Wi-Fi.

ВРЕМЕННЫЙ dev-режим: перед загрузкой вручную вводим URL, который печатает терминал
vite в строке `Network: http://192.168.x.x:8560`. После заливки на сервер заменить
на постоянный URL (env REACT_APP_URL или захардкодить).

Как запустить НА ТЕЛЕФОНЕ (dev, по Wi-Fi):
    1. Поднять React в сети:   cd reactvitemaket && pnpm dev:lan
    2. На телефоне установить приложение «Flet» (Google Play / App Store),
       телефон и компьютер — в одной Wi-Fi сети.
    3. Запустить из КОРНЯ проекта:
           .venv/bin/flet run --android src/mobile_webview.py   (iPhone: --ios)

Локальная проверка на компьютере (окно с WebView):
    .venv/bin/flet run src/mobile_webview.py
"""

from __future__ import annotations

import asyncio
import os
import socket
from urllib.parse import urlparse

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

# Тёмный фон самого Flet — чтобы на телефоне отличить «пустой Flet» (тёмный) от
# реально загруженного React (светлый #F6F7FB). Диагностика «серого экрана».
_FLET_BG = "#15171C"

_CHECKLIST = (
    "Проверь:\n"
    "• запущен ли  cd reactvitemaket && pnpm dev:lan  (именно dev:lan, не dev)\n"
    "• телефон и компьютер в ОДНОЙ сети Wi-Fi\n"
    "• firewall macOS не блокирует порт 8560\n"
    "• URL открывается в браузере телефона"
)


def _vite_reachable(url: str) -> tuple[bool, str]:
    """Со стороны компьютера: поднят ли dev-сервер React (ловит 'vite не запущен')."""
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    last_error = "unknown"
    for candidate in ("127.0.0.1", host):
        try:
            with socket.create_connection((candidate, port), timeout=1.5):
                return True, candidate
        except OSError as exc:
            last_error = str(exc)
    return False, last_error


# iOS WKWebView в flet НЕ возвращает значение из run_javascript и не пробрасывает
# console.* — поэтому зонд рисует диагноз ПРЯМО на странице (div поверх всего).
_PROBE_JS = """
(function(){
  function panel(bg,txt){
    var d=document.createElement('div');
    d.style.cssText='position:fixed;top:0;left:0;right:0;z-index:2147483647;'
      +'background:'+bg+';color:#000;font:12px/1.4 monospace;padding:10px;'
      +'white-space:pre-wrap;border-bottom:3px solid red';
    d.textContent=txt; document.body.appendChild(d);
  }
  try{
    var r=document.getElementById('root');
    var fc=r&&r.firstElementChild;
    var p=document.createElement('div');p.style.height='100dvh';
    document.body.appendChild(p);var dvh=p.offsetHeight;p.remove();
    panel('#fff',
      'PROBE ok\\n'
      +'ready='+document.readyState+'\\n'
      +'path='+location.pathname+'\\n'
      +'inner='+window.innerWidth+'x'+window.innerHeight+'\\n'
      +'dvh100='+dvh+'\\n'
      +'rootKids='+(r?r.childElementCount:-1)+'\\n'
      +'first='+(fc?fc.offsetWidth+'x'+fc.offsetHeight:'-')+'\\n'
      +'body='+(document.body.innerText||'').replace(/\\s+/g,' ').slice(0,60));
  }catch(err){ panel('#f88','PROBE_FAIL '+err); }
})();
"""


def main(page: ft.Page) -> None:
    page.title = "Белпомощник"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = _FLET_BG

    title = ft.Text("Введите адрес React", size=18, weight=ft.FontWeight.W_600, color="#FFFFFF")
    hint = ft.Text(
        "Скопируй из терминала строку  Network: http://…:8560",
        size=13,
        color="#9AA4B2",
    )
    url_field = ft.TextField(
        value=REACT_URL,
        label="URL React-сервера",
        hint_text="http://192.168.0.10:8560",
        text_size=14,
        autofocus=True,
        keyboard_type=ft.KeyboardType.URL,
        # open_url объявлен ниже — lambda откладывает обращение и планирует корутину.
        on_submit=lambda e: page.run_task(open_url),
    )

    input_view = ft.Container(
        expand=True,
        bgcolor=_FLET_BG,
        padding=24,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                title,
                hint,
                url_field,
                ft.FilledButton("Открыть", icon=ft.Icons.PLAY_ARROW, on_click=lambda e: page.run_task(open_url)),
                ft.OutlinedButton("🔴 Тест WebView (без React)", on_click=lambda e: page.run_task(test_webview)),
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
            width=360,
        ),
    )

    probed = {"done": False}

    def show_input(text: str | None = None, detail: str | None = None, color: str = "#FFFFFF") -> None:
        if text is not None:
            title.value = text
            title.color = color
        if detail is not None:
            hint.value = detail
        page.clean()
        page.add(input_view)
        page.update()

    # --- WebView (создаётся один раз, монтируется как ЕДИНСТВЕННЫЙ контрол страницы) ---
    def on_started(e: ft.ControlEvent) -> None:
        print(f"[webview] start  -> {e.data}")

    def on_progress(e: ft.ControlEvent) -> None:
        print(f"[webview] {e.data}%")

    async def _probe() -> None:
        if probed["done"]:
            return
        probed["done"] = True
        # Ждём выхода из диспатча событий flet (иначе "Concurrent modification").
        await asyncio.sleep(0.8)
        try:
            await webview.run_javascript(_PROBE_JS)
            print("[probe] инъекция отправлена (смотри панель на телефоне)")
        except Exception as ex:  # noqa: BLE001
            print(f"[probe] run_javascript failed: {ex}")

    def on_ended(e: ft.ControlEvent) -> None:
        print(f"[webview] loaded -> {e.data}")
        page.run_task(_probe)

    def on_error(e: ft.ControlEvent) -> None:
        print(f"[webview] ERROR  -> {e.data}")
        show_input("Не удалось загрузить", f"Ошибка: {e.data}\n\n{_CHECKLIST}", "#F87171")

    def on_console(e) -> None:
        print(f"[react:{getattr(e, 'severity_level', '?')}] {getattr(e, 'message', e)}")

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
        url = (url_field.value or "").strip()
        if not url:
            show_input("Введите адрес React", "Поле пустое — вставь URL из терминала.", "#F87171")
            return
        print(f"[webview] открываю -> {url}")
        probed["done"] = False
        # WebView становится единственным контролом страницы → full-size, без Stack.
        page.clean()
        page.add(webview)
        page.update()
        await asyncio.sleep(0.3)  # дать контролу смонтироваться
        await webview.load_request(url)

    async def test_webview(_=None) -> None:
        # Решающий тест: красим WebView напрямую, минуя React и сеть.
        # Красный экран "WEBVIEW OK" => контрол рендерит, виноват React/сеть.
        # Остался тёмный/серый => сам WebView не красит на этом устройстве.
        print("[webview] ТЕСТ load_html")
        page.clean()
        page.add(webview)
        page.update()
        await asyncio.sleep(0.3)
        await webview.load_html(
            "<!doctype html><html><body style='margin:0;background:#e11d48;"
            "color:#fff;font:bold 40px sans-serif;display:flex;align-items:center;"
            "justify-content:center;height:100vh'>WEBVIEW OK</body></html>"
        )

    page.add(input_view)

    ok, info = _vite_reachable(REACT_URL)
    port = urlparse(REACT_URL).port
    if ok:
        print(f"[preflight] vite доступен локально на {info}:{port}")
    else:
        print(f"[preflight] vite НЕ отвечает локально: {info}")
        hint.value = "vite не отвечает на этой машине — запусти  pnpm dev:lan"
        page.update()


if __name__ == "__main__":
    ft.run(main)
