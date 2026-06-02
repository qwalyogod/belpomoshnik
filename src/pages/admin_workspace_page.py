"""
Admin workspace page — рабочее пространство контент-редактора.

Двухпанельный layout: основная область редактирования слева,
правая панель (sidebar) — дерево всего контента в стиле VS Code.

Фаза 1: каркас, sidebar-дерево сценариев (раскрытие до этапов и шагов),
placeholder в основной области. Реальное редактирование появится в Фазе 2.
"""

import flet as ft

from components.cards import app_card
from theme.app_theme import APP_COLORS, padding_only, padding_symmetric, ts

SIDEBAR_WIDTH = 340
MAIN_MIN_WIDTH = 560


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _icon_for_type(item_type: str) -> str:
    return {
        "scenario": ft.Icons.ROUTE_OUTLINED,
        "stage": ft.Icons.STAIRS_OUTLINED,
        "step": ft.Icons.RADIO_BUTTON_UNCHECKED,
        "problem": ft.Icons.HELP_OUTLINE,
        "document": ft.Icons.DESCRIPTION_OUTLINED,
        "authority": ft.Icons.ACCOUNT_BALANCE_OUTLINED,
        "law": ft.Icons.GAVEL_OUTLINED,
        "source": ft.Icons.LINK_OUTLINED,
    }.get(item_type, ft.Icons.CIRCLE_OUTLINED)


def _label_for_type(item_type: str) -> str:
    return {
        "scenario": "Сценарий",
        "stage": "Этап",
        "step": "Шаг",
        "problem": "Проблема",
        "document": "Документ",
        "authority": "Учреждение",
        "law": "Закон-апдейт",
        "source": "Источник",
    }.get(item_type, item_type)


def _tree_row(
    *,
    label: str,
    icon: str,
    indent: int,
    selected: bool,
    expandable: bool,
    expanded: bool,
    on_click,
    on_toggle=None,
    trailing: ft.Control | None = None,
) -> ft.Control:
    """Одна строка дерева в правом sidebar."""
    bg = APP_COLORS["primary_light"] if selected else None
    text_color = APP_COLORS["primary"] if selected else APP_COLORS["text"]
    icon_color = APP_COLORS["primary"] if selected else APP_COLORS["muted"]

    chevron = None
    if expandable:
        chevron = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN if expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
            icon_size=16,
            icon_color=APP_COLORS["muted"],
            on_click=on_toggle,
            tooltip=None,
            style=ft.ButtonStyle(padding=ft.Padding(left=2, top=2, right=2, bottom=2)),
        )
    else:
        chevron = ft.Container(width=24)

    leading_icon = ft.Icon(icon, size=ts(16), color=icon_color)

    label_ctl = ft.Text(
        label,
        size=ts(13),
        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
        color=text_color,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
        expand=True,
    )

    children: list[ft.Control] = [
        ft.Container(width=max(0, indent * 14)),
        chevron,
        leading_icon,
        label_ctl,
    ]
    if trailing is not None:
        children.append(trailing)

    row = ft.Row(controls=children, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    return ft.Container(
        content=row,
        padding=padding_symmetric(horizontal=8, vertical=6),
        border_radius=8,
        bgcolor=bg,
        on_click=on_click,
        ink=True,
        animate=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )


def _dirty_dot() -> ft.Control:
    return ft.Container(
        width=8,
        height=8,
        bgcolor=APP_COLORS["warning"],
        border_radius=4,
        tooltip="Есть несохранённые изменения",
    )


def _section_header(title: str, count: int, expanded: bool, on_toggle) -> ft.Control:
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.KEYBOARD_ARROW_DOWN if expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
                    size=ts(18),
                    color=APP_COLORS["muted"],
                ),
                ft.Text(
                    title,
                    size=ts(11),
                    weight=ft.FontWeight.W_700,
                    color=APP_COLORS["muted"],
                ),
                ft.Container(expand=True),
                ft.Text(
                    str(count),
                    size=ts(11),
                    weight=ft.FontWeight.W_700,
                    color=APP_COLORS["muted"],
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=8, vertical=8),
        border_radius=6,
        on_click=on_toggle,
        ink=True,
    )


def _build_scenario_subtree(
    *,
    scenario: dict,
    state: dict,
    workspace_state: dict,
    on_select,
    on_toggle_scenario,
    on_toggle_stage,
) -> list[ft.Control]:
    """Дерево одного сценария: ─ scenario (с раскрытием) → ─ этапы → шаги."""
    scenario_id = scenario.get("id")
    sel_type = workspace_state.get("selected_type")
    sel_id = workspace_state.get("selected_id")
    expanded_scenarios = workspace_state.setdefault("expanded_scenarios", set())
    expanded_stages = workspace_state.setdefault("expanded_stages", set())

    is_expanded = scenario_id in expanded_scenarios
    is_selected = sel_type == "scenario" and sel_id == scenario_id

    rows: list[ft.Control] = [
        _tree_row(
            label=scenario.get("title") or "(без названия)",
            icon=_icon_for_type("scenario"),
            indent=0,
            selected=is_selected,
            expandable=True,
            expanded=is_expanded,
            on_click=(lambda _e, sid=scenario_id: on_select("scenario", sid)),
            on_toggle=(lambda _e, sid=scenario_id: on_toggle_scenario(sid)),
        )
    ]

    if not is_expanded:
        return rows

    # Если детали этого сценария уже подгружены в admin_state — показываем этапы.
    detail = state.get("scenario_detail") or {}
    detail_id = detail.get("id")
    if detail_id != scenario_id:
        rows.append(
            ft.Container(
                content=ft.Text(
                    "Загрузка этапов…",
                    size=ts(12),
                    color=APP_COLORS["muted"],
                    italic=True,
                ),
                padding=padding_only(left=46, top=4, bottom=4),
            )
        )
        return rows

    stages = detail.get("stages", [])
    if not stages:
        rows.append(
            ft.Container(
                content=ft.Text(
                    "Этапов пока нет",
                    size=ts(12),
                    color=APP_COLORS["muted"],
                    italic=True,
                ),
                padding=padding_only(left=46, top=4, bottom=4),
            )
        )
        return rows

    for stage in stages:
        stage_id = stage.get("id")
        stage_key = (scenario_id, stage_id)
        is_stage_expanded = stage_key in expanded_stages
        is_stage_selected = sel_type == "stage" and sel_id == stage_id
        rows.append(
            _tree_row(
                label=stage.get("title") or "(без названия)",
                icon=_icon_for_type("stage"),
                indent=1,
                selected=is_stage_selected,
                expandable=True,
                expanded=is_stage_expanded,
                on_click=(lambda _e, sid=stage_id: on_select("stage", sid)),
                on_toggle=(lambda _e, sk=stage_key: on_toggle_stage(sk)),
            )
        )
        if not is_stage_expanded:
            continue
        steps = stage.get("steps", []) or []
        if not steps:
            rows.append(
                ft.Container(
                    content=ft.Text(
                        "Шагов нет",
                        size=ts(12),
                        color=APP_COLORS["muted"],
                        italic=True,
                    ),
                    padding=padding_only(left=74, top=4, bottom=4),
                )
            )
            continue
        for step in steps:
            step_id = step.get("id")
            is_step_selected = sel_type == "step" and sel_id == step_id
            rows.append(
                _tree_row(
                    label=step.get("title") or "(без названия)",
                    icon=_icon_for_type("step"),
                    indent=2,
                    selected=is_step_selected,
                    expandable=False,
                    expanded=False,
                    on_click=(lambda _e, sid=step_id: on_select("step", sid)),
                )
            )

    return rows


def _build_flat_section(
    *,
    items: list[dict],
    item_type: str,
    workspace_state: dict,
    on_select,
    label_field: str = "title",
) -> list[ft.Control]:
    sel_type = workspace_state.get("selected_type")
    sel_id = workspace_state.get("selected_id")
    rows: list[ft.Control] = []
    for it in items:
        it_id = it.get("id") or it.get("api_id")
        label = it.get(label_field) or "(без названия)"
        rows.append(
            _tree_row(
                label=label,
                icon=_icon_for_type(item_type),
                indent=0,
                selected=(sel_type == item_type and sel_id == it_id),
                expandable=False,
                expanded=False,
                on_click=(lambda _e, t=item_type, i=it_id: on_select(t, i)),
            )
        )
    if not rows:
        rows.append(
            ft.Container(
                content=ft.Text(
                    "Пока пусто",
                    size=ts(12),
                    color=APP_COLORS["muted"],
                    italic=True,
                ),
                padding=padding_only(left=14, top=4, bottom=4),
            )
        )
    return rows


def _sidebar(
    *,
    state: dict,
    workspace_state: dict,
    search_field: ft.TextField,
    on_select,
    on_toggle_section,
    on_toggle_scenario,
    on_toggle_stage,
    on_open_legacy,
) -> ft.Control:
    expanded_sections: set[str] = workspace_state.setdefault(
        "expanded_sections", {"scenarios"}
    )

    scenarios = state.get("scenarios") or []
    problems = state.get("problems") or []
    documents = state.get("documents") or []
    authorities = state.get("authorities") or []
    law_updates = state.get("law_updates") or []

    blocks: list[ft.Control] = []

    sections = [
        ("scenarios", "СЦЕНАРИИ", scenarios, "scenario"),
        ("problems", "ПРОБЛЕМЫ", problems, "problem"),
        ("documents", "ДОКУМЕНТЫ", documents, "document"),
        ("authorities", "УЧРЕЖДЕНИЯ", authorities, "authority"),
        ("law_updates", "ЗАКОН-АПДЕЙТЫ", law_updates, "law"),
    ]

    for key, title, items, item_type in sections:
        is_expanded = key in expanded_sections
        blocks.append(
            _section_header(
                title=title,
                count=len(items),
                expanded=is_expanded,
                on_toggle=(lambda _e, k=key: on_toggle_section(k)),
            )
        )
        if not is_expanded:
            continue
        if key == "scenarios":
            for sc in scenarios:
                blocks.extend(
                    _build_scenario_subtree(
                        scenario=sc,
                        state=state,
                        workspace_state=workspace_state,
                        on_select=on_select,
                        on_toggle_scenario=on_toggle_scenario,
                        on_toggle_stage=on_toggle_stage,
                    )
                )
        else:
            label_field = (
                "title" if key not in {"law_updates"} else "title"
            )
            blocks.extend(
                _build_flat_section(
                    items=items,
                    item_type=item_type,
                    workspace_state=workspace_state,
                    on_select=on_select,
                    label_field=label_field,
                )
            )

    header = ft.Row(
        controls=[
            ft.Icon(ft.Icons.FOLDER_OPEN, size=ts(18), color=APP_COLORS["primary"]),
            ft.Text(
                "EXPLORER",
                size=ts(12),
                weight=ft.FontWeight.W_800,
                color=APP_COLORS["text"],
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.OPEN_IN_NEW,
                icon_size=16,
                tooltip="Открыть старую админ-панель",
                on_click=on_open_legacy,
            ),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    tree_column = ft.Column(
        controls=blocks,
        spacing=2,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return ft.Container(
        width=SIDEBAR_WIDTH,
        content=ft.Column(
            controls=[
                header,
                ft.Container(height=8),
                search_field,
                ft.Container(height=10),
                tree_column,
            ],
            spacing=0,
            expand=True,
        ),
        padding=padding_symmetric(horizontal=14, vertical=16),
        bgcolor=APP_COLORS["surface"],
        border=ft.Border(left=ft.BorderSide(1, APP_COLORS["border"])),
    )


def _breadcrumb(state: dict, workspace_state: dict) -> ft.Control:
    parts: list[str] = ["Workspace"]
    sel_type = workspace_state.get("selected_type")
    sel_id = workspace_state.get("selected_id")
    detail = state.get("scenario_detail") or {}

    if sel_type == "scenario":
        title = next(
            (s.get("title") for s in (state.get("scenarios") or []) if s.get("id") == sel_id),
            None,
        )
        parts.append("Сценарии")
        if title:
            parts.append(title)
    elif sel_type == "stage":
        parts.append("Сценарии")
        if detail.get("title"):
            parts.append(detail["title"])
        stage = next(
            (s for s in (detail.get("stages") or []) if s.get("id") == sel_id),
            None,
        )
        if stage:
            parts.append(stage.get("title") or "Этап")
    elif sel_type == "step":
        parts.append("Сценарии")
        if detail.get("title"):
            parts.append(detail["title"])
        for stage in detail.get("stages") or []:
            for step in stage.get("steps") or []:
                if step.get("id") == sel_id:
                    parts.append(stage.get("title") or "Этап")
                    parts.append(step.get("title") or "Шаг")
                    break
    elif sel_type in {"problem", "document", "authority", "law"}:
        parts.append(_label_for_type(sel_type) + "ы")
        section_key = {
            "problem": "problems",
            "document": "documents",
            "authority": "authorities",
            "law": "law_updates",
        }[sel_type]
        items = state.get(section_key) or []
        item = next(
            (
                x for x in items
                if (x.get("id") or x.get("api_id")) == sel_id
            ),
            None,
        )
        if item:
            parts.append(item.get("title") or "(без названия)")

    chips: list[ft.Control] = []
    for i, p in enumerate(parts):
        chips.append(
            ft.Text(
                p,
                size=ts(13),
                weight=ft.FontWeight.W_700 if i == len(parts) - 1 else ft.FontWeight.W_500,
                color=APP_COLORS["text"] if i == len(parts) - 1 else APP_COLORS["muted"],
            )
        )
        if i < len(parts) - 1:
            chips.append(
                ft.Icon(
                    ft.Icons.CHEVRON_RIGHT,
                    size=ts(16),
                    color=APP_COLORS["muted"],
                )
            )
    return ft.Row(controls=chips, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _topbar(
    *,
    state: dict,
    workspace_state: dict,
    on_save,
    on_refresh,
) -> ft.Control:
    dirty = workspace_state.get("dirty", False)

    return ft.Container(
        content=ft.Row(
            controls=[
                _breadcrumb(state, workspace_state),
                ft.Container(expand=True),
                _dirty_dot() if dirty else ft.Container(width=0),
                ft.TextButton(
                    "Обновить",
                    icon=ft.Icons.REFRESH,
                    on_click=on_refresh,
                ),
                ft.FilledButton(
                    "Сохранить",
                    icon=ft.Icons.SAVE_OUTLINED,
                    on_click=on_save,
                    disabled=not dirty,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=22, vertical=14),
        bgcolor=APP_COLORS["surface"],
        border=ft.Border(bottom=ft.BorderSide(1, APP_COLORS["border"])),
    )


def _placeholder_main() -> ft.Control:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.EDIT_DOCUMENT,
                    size=ts(64),
                    color=APP_COLORS["muted"],
                ),
                ft.Container(height=10),
                ft.Text(
                    "Выберите элемент в правой панели",
                    size=ts(18),
                    weight=ft.FontWeight.W_700,
                    color=APP_COLORS["text"],
                ),
                ft.Text(
                    "Раскройте дерево и кликните по сценарию, этапу, шагу, "
                    "проблеме, документу или закон-апдейту, чтобы открыть его в редакторе.",
                    size=ts(13),
                    color=APP_COLORS["muted"],
                    text_align=ft.TextAlign.CENTER,
                    width=440,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
    )


def _editor_preview(state: dict, workspace_state: dict) -> ft.Control:
    """
    Фаза 1: рендер выбранного элемента как карточки только для чтения.
    В Фазе 2 здесь появятся реальные inline-формы для каждого типа.
    """
    sel_type = workspace_state.get("selected_type")
    sel_id = workspace_state.get("selected_id")
    if sel_type is None or sel_id is None:
        return _placeholder_main()

    item: dict | None = None
    title = ""
    subtitle = ""
    body_rows: list[ft.Control] = []

    if sel_type == "scenario":
        item = next(
            (s for s in (state.get("scenarios") or []) if s.get("id") == sel_id),
            None,
        )
        if item:
            title = item.get("title") or "(без названия)"
            subtitle = f"Сценарий · slug: {item.get('slug', '—')}"
            body_rows = [
                ("Краткое описание", item.get("short_description") or "—"),
                ("Сложность", item.get("difficulty_level") or "—"),
                ("Статус", item.get("status") or "—"),
                ("ID", str(item.get("id"))),
            ]
    elif sel_type == "stage":
        detail = state.get("scenario_detail") or {}
        for s in detail.get("stages") or []:
            if s.get("id") == sel_id:
                item = s
                break
        if item:
            title = item.get("title") or "(без названия)"
            subtitle = f"Этап · order_index: {item.get('order_index', '—')}"
            body_rows = [
                ("Описание", item.get("description") or "—"),
                ("Обязательный", "Да" if item.get("is_required") else "Нет"),
                ("Шагов внутри", str(len(item.get("steps") or []))),
                ("ID", str(item.get("id"))),
            ]
    elif sel_type == "step":
        detail = state.get("scenario_detail") or {}
        for stage in detail.get("stages") or []:
            for step in stage.get("steps") or []:
                if step.get("id") == sel_id:
                    item = step
                    break
        if item:
            title = item.get("title") or "(без названия)"
            subtitle = (
                f"Шаг · действие: {item.get('action_type', '—')} · "
                f"order_index: {item.get('order_index', '—')}"
            )
            body_rows = [
                ("Описание", item.get("description") or "—"),
                ("Обязательный", "Да" if item.get("is_required") else "Нет"),
                ("ID", str(item.get("id"))),
            ]
    elif sel_type == "problem":
        item = next(
            (p for p in (state.get("problems") or []) if p.get("id") == sel_id),
            None,
        )
        if item:
            title = item.get("title") or "(без названия)"
            subtitle = f"Проблема · категория: {item.get('category', '—')}"
            body_rows = [
                ("Краткое описание", item.get("short_description") or "—"),
                ("Статус", item.get("status") or "—"),
                ("ID", str(item.get("id"))),
            ]
    elif sel_type == "document":
        item = next(
            (d for d in (state.get("documents") or []) if d.get("id") == sel_id),
            None,
        )
        if item:
            title = item.get("title") or "(без названия)"
            subtitle = f"Документ · тип: {item.get('document_type', '—')}"
            body_rows = [
                ("Описание", item.get("description") or "—"),
                ("ID", str(item.get("id"))),
            ]
    elif sel_type == "authority":
        item = next(
            (a for a in (state.get("authorities") or []) if a.get("id") == sel_id),
            None,
        )
        if item:
            title = item.get("title") or "(без названия)"
            subtitle = f"Учреждение · {item.get('region', '—')}"
            body_rows = [
                ("Адрес", item.get("address") or "—"),
                ("Контакты", item.get("contacts") or "—"),
                ("ID", str(item.get("id"))),
            ]
    elif sel_type == "law":
        item = next(
            (
                l for l in (state.get("law_updates") or [])
                if (l.get("id") or l.get("api_id")) == sel_id
            ),
            None,
        )
        if item:
            title = item.get("title") or "(без названия)"
            subtitle = f"Закон-апдейт · категория: {item.get('category', '—')}"
            body_rows = [
                ("Краткое описание", item.get("summary") or "—"),
                ("Статус", item.get("status") or "—"),
                ("Дата", item.get("published_at") or "—"),
            ]

    if item is None:
        return ft.Container(
            content=ft.Text(
                "Элемент не найден в кэше. Нажмите «Обновить» в верхней панели.",
                size=ts(14),
                color=APP_COLORS["muted"],
            ),
            padding=ft.Padding(left=40, top=40, right=40, bottom=40),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

    field_rows = []
    for label, value in body_rows:
        field_rows.append(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            label,
                            size=ts(12),
                            color=APP_COLORS["muted"],
                            weight=ft.FontWeight.W_600,
                        ),
                        width=160,
                    ),
                    ft.Text(
                        value,
                        size=ts(14),
                        color=APP_COLORS["text"],
                        expand=True,
                        selectable=True,
                    ),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )

    notice = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, size=ts(18), color=APP_COLORS["primary"]),
                ft.Text(
                    "Фаза 1: предпросмотр. Inline-редактирование появится в Фазе 2.",
                    size=ts(12),
                    color=APP_COLORS["text"],
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=14, vertical=10),
        bgcolor=APP_COLORS["primary_light"],
        border_radius=10,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    title,
                    size=ts(24),
                    weight=ft.FontWeight.W_800,
                    color=APP_COLORS["text"],
                ),
                ft.Text(
                    subtitle,
                    size=ts(13),
                    color=APP_COLORS["muted"],
                ),
                ft.Container(height=14),
                notice,
                ft.Container(height=18),
                app_card(
                    ft.Column(controls=field_rows, spacing=14),
                    padding=22,
                ),
                ft.Container(height=40),
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=padding_symmetric(horizontal=36, vertical=24),
        expand=True,
    )


def build_admin_workspace_page(
    *,
    is_desktop: bool,
    admin_state: dict,
    workspace_state: dict,
    search_field: ft.TextField,
    on_select,
    on_toggle_section,
    on_toggle_scenario,
    on_toggle_stage,
    on_save,
    on_refresh,
    on_open_legacy,
    on_back_to_tree=None,
) -> ft.Control:
    """
    Точка входа workspace-редактора.

    Desktop: главная область + правый sidebar.
    Mobile: либо дерево на весь экран, либо редактор на весь экран с кнопкой "Назад".
    """
    main_area = _editor_preview(admin_state, workspace_state)

    if is_desktop:
        body = ft.Row(
            controls=[
                ft.Container(content=main_area, expand=True),
                _sidebar(
                    state=admin_state,
                    workspace_state=workspace_state,
                    search_field=search_field,
                    on_select=on_select,
                    on_toggle_section=on_toggle_section,
                    on_toggle_scenario=on_toggle_scenario,
                    on_toggle_stage=on_toggle_stage,
                    on_open_legacy=on_open_legacy,
                ),
            ],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    _topbar(
                        state=admin_state,
                        workspace_state=workspace_state,
                        on_save=on_save,
                        on_refresh=on_refresh,
                    ),
                    ft.Container(content=body, expand=True),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor=APP_COLORS["background"],
        )

    # Mobile: master-detail single column
    has_selection = workspace_state.get("selected_id") is not None
    if has_selection:
        mobile_body = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                on_click=on_back_to_tree,
                            ),
                            ft.Text(
                                "К дереву контента",
                                size=ts(14),
                                color=APP_COLORS["text"],
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=padding_symmetric(horizontal=10, vertical=8),
                ),
                main_area,
            ],
            spacing=0,
            expand=True,
        )
    else:
        mobile_body = ft.Column(
            controls=[
                _topbar(
                    state=admin_state,
                    workspace_state=workspace_state,
                    on_save=on_save,
                    on_refresh=on_refresh,
                ),
                _sidebar(
                    state=admin_state,
                    workspace_state=workspace_state,
                    search_field=search_field,
                    on_select=on_select,
                    on_toggle_section=on_toggle_section,
                    on_toggle_scenario=on_toggle_scenario,
                    on_toggle_stage=on_toggle_stage,
                    on_open_legacy=on_open_legacy,
                ),
            ],
            spacing=0,
            expand=True,
        )

    return ft.Container(
        content=mobile_body,
        expand=True,
        bgcolor=APP_COLORS["background"],
    )
