"""
Кросс-версийные хелперы открытия/закрытия диалогов Flet.

Flet 0.85 не имеет page.open/page.close — есть show_dialog/pop_dialog.
Более новые версии имеют page.open/page.close. Эти функции пробуют все
варианты по очереди.
"""
from __future__ import annotations

import flet as ft


def open_dialog(page: ft.Page, dialog: ft.Control) -> None:
    open_method = getattr(page, "open", None)
    if callable(open_method):
        try:
            open_method(dialog)
            return
        except Exception:
            pass
    show = getattr(page, "show_dialog", None)
    if callable(show):
        try:
            show(dialog)
            return
        except Exception:
            pass
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    try:
        dialog.open = True
    except Exception:
        pass
    page.update()


def close_dialog(page: ft.Page, dialog: ft.Control | None = None) -> None:
    pop = getattr(page, "pop_dialog", None)
    if callable(pop):
        try:
            pop()
            return
        except Exception:
            pass
    close = getattr(page, "close", None)
    if callable(close) and dialog is not None:
        try:
            close(dialog)
            return
        except Exception:
            pass
    if dialog is not None:
        try:
            dialog.open = False
        except Exception:
            pass
    page.update()
