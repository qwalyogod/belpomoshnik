"""
Выпадающее меню пользователя в header.

В header: круглый аватар + имя пользователя (без подписи «Профиль»).
По клику открывается dropdown:
  1. Профиль
  2. Настройки
  ─────────────────────
  3. Список тестовых аккаунтов для переключения (с email и галкой у текущего)
  4. Добавить пользователя
  ─────────────────────
  5. Email текущего пользователя
  6. Выйти

Гость в header не получает аватара — у него отдельная кнопка «Войти».
"""
from __future__ import annotations

import flet as ft

from theme.app_theme import APP_COLORS, ANIM_FAST, CENTER, border_all, padding_symmetric, ts


_ROLE_LABELS: dict[str, str] = {
    "citizen": "Гражданин",
    "content_editor": "Редактор",
    "platform_admin": "Администратор",
}


def _initials(name: str) -> str:
    if not name:
        return "•"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _role_label(role_id: str) -> str:
    return _ROLE_LABELS.get(role_id, role_id)


def build_user_menu(
    page: ft.Page,
    user: dict | None,
    role: str,
    on_profile,
    on_settings,
    on_logout,
    avatar_url: str | None = None,
    size: int = 40,
    *,
    test_accounts: list[dict] | None = None,
    on_switch_account=None,
    on_add_account=None,
    show_name: bool = True,
) -> ft.Control:
    """
    Аватар + имя в header + popup-меню.

    show_name=True показывает имя справа от аватара (desktop).
    show_name=False — только аватар (mobile).
    """
    user = user or {}
    test_accounts = test_accounts or []
    user_email = user.get("email", "")
    user_name = user.get("name", "Пользователь")
    initials = _initials(user_name)

    # ── Avatar (круг с инициалами или картинкой) ──────────────────────────
    if avatar_url:
        avatar_ctrl: ft.Control = ft.Container(
            width=size, height=size, border_radius=size // 2,
            content=ft.Image(src=avatar_url, width=size, height=size, fit=ft.ImageFit.COVER, border_radius=size // 2),
            border=border_all(APP_COLORS["stroke2"]),
        )
    else:
        avatar_ctrl = ft.Container(
            width=size, height=size, border_radius=size // 2,
            bgcolor=APP_COLORS["surface2"],
            alignment=CENTER,
            content=ft.Text(initials or "•", size=ts(15), weight=ft.FontWeight.W_900, color=APP_COLORS["blue"]),
            border=border_all(APP_COLORS["stroke2"]),
        )

    # ── Trigger: avatar + name (без подписи «Профиль») ────────────────────
    trigger_controls: list[ft.Control] = [avatar_ctrl]
    if show_name:
        trigger_controls.insert(
            0,
            ft.Text(
                user_name,
                size=ts(14),
                weight=ft.FontWeight.W_800,
                color=APP_COLORS["text"],
                max_lines=1,
                no_wrap=True,
            ),
        )

    # ── Pop-up menu rows ──────────────────────────────────────────────────
    def _menu_item(icon, label, on_click, danger: bool = False, trailing: ft.Control | None = None) -> ft.Container:
        text_color = APP_COLORS["red"] if danger else APP_COLORS["text"]
        icon_color = APP_COLORS["red"] if danger else APP_COLORS["muted"]
        row_controls: list[ft.Control] = [
            ft.Icon(icon, size=ts(18), color=icon_color),
            ft.Text(label, size=ts(13), weight=ft.FontWeight.W_700, color=text_color, expand=True),
        ]
        if trailing is not None:
            row_controls.append(trailing)
        row = ft.Container(
            ink=True,
            on_click=lambda _e: (_close_menu(), on_click() if on_click else None),
            padding=padding_symmetric(horizontal=14, vertical=11),
            border_radius=10,
            content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=row_controls),
        )

        def _hover(e: ft.HoverEvent) -> None:
            row.bgcolor = APP_COLORS["surface2"] if e.data == "true" else None
            try:
                row.update()
            except Exception:
                pass

        row.on_hover = _hover
        return row

    def _account_row(account: dict) -> ft.Container:
        acc_email = account.get("email", "")
        acc_role = account.get("role", "")
        acc_name = account.get("name", "") or _role_label(acc_role)
        active = acc_email == user_email
        check = ft.Icon(ft.Icons.CHECK_CIRCLE, size=ts(16), color=APP_COLORS["blue"]) if active else ft.Container(width=16, height=16)
        body = ft.Column(
            spacing=1,
            expand=True,
            controls=[
                ft.Text(acc_name, size=ts(13), weight=ft.FontWeight.W_700, color=APP_COLORS["text"], max_lines=1, no_wrap=True),
                ft.Text(acc_email, size=ts(11), color=APP_COLORS["muted"], max_lines=1, no_wrap=True),
            ],
        )

        def _click(_=None) -> None:
            _close_menu()
            if not active and on_switch_account:
                on_switch_account(acc_email, acc_name, acc_role)

        row = ft.Container(
            ink=True,
            on_click=_click,
            padding=padding_symmetric(horizontal=14, vertical=9),
            border_radius=10,
            bgcolor=APP_COLORS["active"] if active else None,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=28, height=28, border_radius=14,
                        bgcolor=APP_COLORS["surface2"],
                        alignment=CENTER,
                        content=ft.Text(_initials(acc_name), size=ts(11), weight=ft.FontWeight.W_900, color=APP_COLORS["blue"]),
                    ),
                    body,
                    check,
                ],
            ),
        )

        def _hover(e: ft.HoverEvent) -> None:
            if not active:
                row.bgcolor = APP_COLORS["surface2"] if e.data == "true" else None
                try:
                    row.update()
                except Exception:
                    pass

        row.on_hover = _hover
        return row

    # ── Header card в попапе: имя + роль ───────────────────────────────────
    header_block = ft.Container(
        padding=padding_symmetric(horizontal=14, vertical=12),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=36, height=36, border_radius=18,
                    bgcolor=APP_COLORS["active"],
                    alignment=CENTER,
                    content=ft.Text(initials or "•", size=ts(14), weight=ft.FontWeight.W_900, color=APP_COLORS["blue"]),
                ),
                ft.Column(
                    spacing=1,
                    expand=True,
                    controls=[
                        ft.Text(user_name, size=ts(13), weight=ft.FontWeight.W_900, color=APP_COLORS["text"], max_lines=1, no_wrap=True),
                        ft.Text(_role_label(role), size=ts(11), color=APP_COLORS["muted"], max_lines=1, no_wrap=True),
                    ],
                ),
            ],
        ),
    )

    # ── Сборка списка контролов в menu_card ────────────────────────────────
    items: list[ft.Control] = [
        header_block,
        ft.Divider(height=1, color=APP_COLORS["stroke2"]),
        _menu_item(ft.Icons.PERSON_OUTLINE, "Профиль", on_profile),
        _menu_item(ft.Icons.SETTINGS_OUTLINED, "Настройки", on_settings),
    ]

    if test_accounts:
        items.extend([
            ft.Divider(height=1, color=APP_COLORS["stroke2"]),
            ft.Container(
                padding=ft.Padding(left=14, top=8, right=14, bottom=4),
                content=ft.Text("Сменить пользователя", size=ts(11), weight=ft.FontWeight.W_700, color=APP_COLORS["muted2"]),
            ),
        ])
        items.extend([_account_row(acc) for acc in test_accounts])

    if on_add_account is not None:
        items.append(_menu_item(ft.Icons.PERSON_ADD_OUTLINED, "Добавить пользователя", on_add_account))

    # Footer block: email + выйти
    items.extend([
        ft.Divider(height=1, color=APP_COLORS["stroke2"]),
        ft.Container(
            padding=padding_symmetric(horizontal=14, vertical=8),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.MAIL_OUTLINE, size=ts(14), color=APP_COLORS["muted2"]),
                    ft.Text(user_email or "—", size=ts(11), color=APP_COLORS["muted"], expand=True, max_lines=1, no_wrap=True),
                ],
            ),
        ),
        _menu_item(ft.Icons.LOGOUT, "Выйти", on_logout, danger=True),
    ])

    menu_card = ft.Container(
        bgcolor=APP_COLORS["panel"],
        border_radius=14,
        border=border_all(APP_COLORS["stroke"]),
        shadow=ft.BoxShadow(blur_radius=28, color=ft.Colors.with_opacity(0.22, ft.Colors.BLACK)),
        width=300,
        padding=padding_symmetric(horizontal=6, vertical=6),
        content=ft.Column(spacing=2, tight=True, controls=items),
        # Лёгкая анимация появления
        animate_opacity=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
    )

    # Anchored dropdown: backdrop (закрытие по клику вне) + карточка справа-сверху.
    state = {"open": False, "layer": None}

    def _close_menu(_=None) -> None:
        layer = state.get("layer")
        if layer is not None and layer in page.overlay:
            page.overlay.remove(layer)
        state["open"] = False
        state["layer"] = None
        try:
            page.update()
        except Exception:
            pass

    def _open_menu(_=None) -> None:
        if state["open"]:
            _close_menu()
            return
        backdrop = ft.GestureDetector(
            on_tap=_close_menu,
            content=ft.Container(expand=True, bgcolor=ft.Colors.TRANSPARENT),
        )
        positioned = ft.Container(
            content=menu_card,
            right=18,
            top=70,
        )
        layer = ft.Stack(controls=[backdrop, positioned], expand=True)
        state["layer"] = layer
        state["open"] = True
        page.overlay.append(layer)
        page.update()

    trigger = ft.Container(
        ink=True,
        on_click=_open_menu,
        border_radius=22,
        padding=padding_symmetric(horizontal=8, vertical=4),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=trigger_controls,
        ),
        tooltip="Меню пользователя",
        animate=ft.Animation(ANIM_FAST, ft.AnimationCurve.EASE_OUT),
    )

    return trigger
