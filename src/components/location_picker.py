"""Cascading location picker: region → district → city + address.

Returns a control plus a get_value() closure yielding a normalized dict:
{label, region, district, city, address}
Used in registration and in the profile multi-address editor.
"""
from __future__ import annotations

import flet as ft

from services import geo_data
from theme.app_theme import APP_COLORS, APP_RADIUS, padding_symmetric


LOCATION_LABELS = ["Прописка", "Фактический адрес", "Место учёбы", "Временный адрес"]


def _dropdown(label: str, options: list[str], value: str | None = None, on_select=None, hint: str = "") -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        hint_text=hint or label,
        value=value if value in options else None,
        options=[ft.dropdown.Option(key=o, text=o) for o in options],
        on_select=on_select,
        border_radius=APP_RADIUS["input"],
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        bgcolor=APP_COLORS["search"],
        fill_color=APP_COLORS["search"],
        filled=True,
        color=APP_COLORS["text"],
        text_size=15,
        label_style=ft.TextStyle(color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
        content_padding=padding_symmetric(horizontal=14, vertical=12),
    )


def build_location_picker(
    *,
    initial: dict | None = None,
    show_label_select: bool = True,
    compact: bool = False,
):
    """Returns (control, get_value). get_value() -> dict."""
    initial = initial or {}
    regions = geo_data.region_names()

    label_dd = _dropdown(
        "Тип адреса",
        LOCATION_LABELS,
        value=initial.get("label", LOCATION_LABELS[0]),
        hint="Прописка / учёба / факт. адрес",
    )

    region_dd = _dropdown("Регион", regions, value=initial.get("region"))
    district_dd = _dropdown(
        "Район",
        geo_data.districts_for(initial.get("region", "")),
        value=initial.get("district"),
        hint="Сначала выберите регион",
    )
    city_field = ft.TextField(
        label="Город / населённый пункт",
        value=initial.get("city", ""),
        border_radius=APP_RADIUS["input"],
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        bgcolor=APP_COLORS["search"],
        filled=True,
        fill_color=APP_COLORS["search"],
        color=APP_COLORS["text"],
        text_size=15,
        label_style=ft.TextStyle(color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
        content_padding=padding_symmetric(horizontal=14, vertical=12),
    )
    address_field = ft.TextField(
        label="Улица, дом, кв.",
        value=initial.get("address", ""),
        border_radius=APP_RADIUS["input"],
        border_color=APP_COLORS["stroke2"],
        focused_border_color=APP_COLORS["blue"],
        bgcolor=APP_COLORS["search"],
        filled=True,
        fill_color=APP_COLORS["search"],
        color=APP_COLORS["text"],
        text_size=15,
        label_style=ft.TextStyle(color=APP_COLORS["muted"], weight=ft.FontWeight.W_700),
        content_padding=padding_symmetric(horizontal=14, vertical=12),
    )

    def _on_region_change(_=None) -> None:
        region = region_dd.value or ""
        new_districts = geo_data.districts_for(region)
        district_dd.options = [ft.dropdown.Option(key=o, text=o) for o in new_districts]
        district_dd.value = None
        district_dd.hint_text = "Выберите район" if new_districts else "Нет данных по региону"
        if district_dd.page:
            district_dd.update()

    def _on_district_change(_=None) -> None:
        # autofill city from district center if empty
        region = region_dd.value or ""
        district = district_dd.value or ""
        if district and not (city_field.value or "").strip():
            city_field.value = geo_data.city_for_district(region, district)
            if city_field.page:
                city_field.update()

    region_dd.on_select = _on_region_change
    district_dd.on_select = _on_district_change

    rows: list[ft.Control] = []
    if show_label_select:
        rows.append(label_dd)
    rows.append(region_dd)
    if compact:
        rows.append(ft.Row(spacing=10, controls=[
            ft.Container(expand=True, content=district_dd),
            ft.Container(expand=True, content=city_field),
        ]))
    else:
        rows.append(district_dd)
        rows.append(city_field)
    rows.append(address_field)

    control = ft.Column(spacing=10, controls=rows)

    def get_value() -> dict:
        return {
            "label": (label_dd.value or LOCATION_LABELS[0]) if show_label_select else initial.get("label", LOCATION_LABELS[0]),
            "region": region_dd.value or "",
            "district": district_dd.value or "",
            "city": (city_field.value or "").strip(),
            "address": (address_field.value or "").strip(),
        }

    return control, get_value
