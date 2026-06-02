import flet as ft

from components.buttons import secondary_button
from components.cards import app_card, badge, info_card
from components.layout import desktop_content
from data.mock_data import LAW_DETAIL, LEGAL_UPDATES
from theme.app_theme import APP_COLORS, ts


_PROCESSING_STATUS_LABELS = {
    "new": ("Новое", "warning"),
    "reviewed": ("Проверено", "blue"),
    "applied": ("Применено", "success"),
}


def _processing_badge(law: dict) -> ft.Control:
    ps = law.get("processing_status", "new")
    label, variant = _PROCESSING_STATUS_LABELS.get(ps, ("Новое", "warning"))
    return badge(label, variant)


def _find_law(law_id: str, laws: list[dict] | None = None) -> dict:
    dataset = laws or LEGAL_UPDATES
    return next((item for item in dataset if item["id"] == law_id), dataset[0] if dataset else {})


def _detail(law_id: str, law_detail: dict | None = None) -> dict:
    dataset = law_detail or LAW_DETAIL
    return dataset.get(law_id, {"summary": "Подробности будут добавлены позже.", "details": []})


def _content(law: dict, detail: dict, go_back, on_save_law=None, on_open_source=None) -> ft.Column:
    if not law:
        return ft.Column(
            spacing=18,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=APP_COLORS["muted"], on_click=go_back),
                        ft.Text("Обновление не найдено", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"], expand=True),
                    ],
                ),
                app_card(ft.Text("Запись могла быть удалена в админ-панели.", size=ts(14), color=APP_COLORS["muted"])),
            ],
        )

    related_scenarios = law.get("related_scenarios") or []
    related_problems = law.get("related_problems") or []
    last_checked = law.get("last_checked", "")

    scenario_chips = ft.Row(
        wrap=True,
        spacing=6,
        run_spacing=6,
        controls=[badge(s, "blue") for s in related_scenarios] or [ft.Text("Связанные сценарии пока не указаны.", size=ts(13), color=APP_COLORS["muted"])],
    )
    problem_chips = ft.Row(
        wrap=True,
        spacing=6,
        run_spacing=6,
        controls=[badge(p, "default") for p in related_problems] or [ft.Text("Связанные проблемы пока не указаны.", size=ts(13), color=APP_COLORS["muted"])],
    )

    meta_rows: list[ft.Control] = [
        ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, color=APP_COLORS["primary"]),
                ft.Text(f"Вступает в силу: {law['date']}", size=ts(14), weight=ft.FontWeight.W_600, color=APP_COLORS["text"]),
            ],
        ),
        ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.GROUP_OUTLINED, color=APP_COLORS["blue"]),
                ft.Text(f"Кого касается: {law['target']}", size=ts(14), weight=ft.FontWeight.W_600, color=APP_COLORS["text"], expand=True),
            ],
        ),
        ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.PLAYLIST_ADD_CHECK_OUTLINED, color=APP_COLORS["muted"], size=ts(18)),
                ft.Text("Статус обработки: ", size=ts(13), color=APP_COLORS["muted"]),
                _processing_badge(law),
            ],
        ),
    ]
    if last_checked:
        meta_rows.append(
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.UPDATE_OUTLINED, color=APP_COLORS["muted"], size=ts(18)),
                    ft.Text(f"Источник проверен: {last_checked}", size=ts(13), color=APP_COLORS["muted"]),
                ],
            )
        )

    return ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                spacing=8,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=APP_COLORS["muted"], on_click=go_back),
                    ft.Text("Подробности", size=ts(20), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"], expand=True),
                    ft.IconButton(
                        icon=ft.Icons.BOOKMARK_BORDER,
                        icon_color=APP_COLORS["muted"],
                        tooltip="Сохранить",
                        on_click=lambda _: on_save_law(law["id"]) if on_save_law else None,
                    ),
                ],
            ),
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(wrap=True, spacing=6, controls=[badge(law["category_name"], "blue"), _processing_badge(law)]),
                    ft.Text(law["title"], size=ts(28), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                    ft.Text(law["short"], size=ts(15), color=APP_COLORS["muted"]),
                    app_card(ft.Column(spacing=10, controls=meta_rows)),
                ],
            ),
            info_card("Что изменилось", [detail["summary"], *detail.get("details", [])], ft.Icons.ERROR_OUTLINE, "blue"),
            info_card(
                "Что сделать пользователю",
                law.get("what_to_do") or "Проверьте актуальность информации по официальному источнику и уточните требования перед подачей документов.",
                ft.Icons.TASK_ALT_OUTLINED,
                "green",
            ),
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, color=APP_COLORS["primary"], size=ts(20)),
                                ft.Text("Затронутые сценарии", size=ts(15), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                            ],
                        ),
                        scenario_chips,
                    ],
                )
            ),
            app_card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.MANAGE_SEARCH_OUTLINED, color=APP_COLORS["primary"], size=ts(20)),
                                ft.Text("Связанные проблемы", size=ts(15), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                            ],
                        ),
                        problem_chips,
                    ],
                )
            ),
            app_card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.VERIFIED_OUTLINED, color=APP_COLORS["primary"], size=ts(20)),
                                ft.Text("Официальный источник", size=ts(16), weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
                            ],
                        ),
                        ft.Text(
                            law.get("source_url") or "Источник будет добавлен редактором.",
                            size=ts(13),
                            color=APP_COLORS["muted"],
                        ),
                        ft.Text(
                            "Информация используется в справочных целях и должна сверяться с официальными ресурсами.",
                            size=ts(12),
                            color=APP_COLORS["muted"],
                        ),
                    ],
                )
            ),
            secondary_button(
                "Открыть первоисточник",
                icon=ft.Icons.LINK,
                expand=True,
                on_click=lambda _: on_open_source(law["id"]) if on_open_source else None,
            ),
        ],
    )


def build_law_detail_page(
    law_id: str,
    go_back,
    is_desktop: bool = False,
    on_save_law=None,
    on_open_source=None,
    laws: list[dict] | None = None,
    law_detail: dict | None = None,
) -> ft.Control:
    law = _find_law(law_id, laws)
    detail = _detail(law_id, law_detail)
    content = _content(law, detail, go_back, on_save_law, on_open_source)
    return desktop_content(content, width=780, top=54) if is_desktop else content
