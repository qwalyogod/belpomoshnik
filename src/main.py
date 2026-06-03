from datetime import date, datetime, timedelta
import asyncio
import copy
import flet as ft
from pathlib import Path
import re
import shutil
import time

from components.ai_chat import build_ai_chat_fab, build_ai_chat_overlay
from components.bottom_nav import NAV_ITEMS, build_bottom_nav
from components.layout import (
    app_safe_area,
    bottom_nav_safe_area,
    build_desktop_footer,
    build_desktop_header,
    mobile_page_layout,
)
from components.mobile_topbar import build_mobile_topbar, build_notification_button
from components.sidebar import build_sidebar
from data.mock_data import (
    ADMIN_AUDIT_LOGS,
    ADMIN_ROLES,
    ADMIN_USERS,
    DOCUMENTS,
    DOCUMENT_TYPES,
    INSTITUTIONS,
    LAW_DETAIL,
    LEGAL_UPDATES,
    MOCK_USER,
    NOTIFICATIONS,
    OFFICIAL_SOURCES,
    SCENARIO_TEMPLATES,
    SITUATION_TASKS,
    SITUATIONS,
    TAX_OBLIGATIONS,
    UTILITY_ACCOUNTS,
    UTILITY_PAYMENTS,
)
from pages.about_page import build_about_page
from pages.admin_page import build_admin_page
from pages.admin_workspace_page import build_admin_workspace_page
from pages.documents_page import build_documents_page
from pages.home_page import build_home_page
from pages.law_detail_page import build_law_detail_page
from pages.learning_progress_page import build_learning_progress_page
from pages.legal_updates_page import build_legal_updates_page
from pages.login_page import build_login_page
from pages.email_preview_page import build_doc_expiry_email_data, build_email_preview_page
from pages.notifications_page import build_notifications_page
from pages.onboarding_page import build_onboarding_page
from pages.problem_detail_page import build_problem_detail_page, find_problem
from pages.problems_page import build_problems_page
from pages.profile_page import build_profile_page
from pages.register_page import build_register_page
from pages.scenario_detail_page import build_scenario_detail_page, find_scenario_template
from pages.scenario_templates_page import build_scenario_templates_page
from pages.search_page import build_search_page
from pages.situation_detail_page import build_situation_detail_page
from pages.situations_page import build_situations_page
from pages.tax_tracker_page import build_tax_tracker_page
from pages.utility_tracker_page import build_utility_tracker_page
from services.admin_api import AdminAPIClient, AdminAPIError
from services.dashboard import build_dashboard_data, parse_due_date, status_from_progress
from services.file_crypto import ENCRYPTED_SUFFIX, decrypt_bytes, encrypt_bytes, is_encrypted_path
from services.institutions import match_institutions
from services.auth_api import AuthAPIClient, AuthAPIError
from services.local_store import load_app_state, save_app_state
from services.public_api import PublicAPIClient, PublicAPIError
from services.user_api import UserAPIClient, UserAPIError
from services import role_guard, user_sync
from components.guest_modal import open_guest_modal as _open_guest_modal_dialog
from theme.app_theme import APP_COLORS, border_all, build_theme, padding_symmetric, set_large_text, set_theme_mode


NAV_ROUTES = {
    "home": "/",
    "search": "/search",
    "problems": "/problems",
    "scenarios": "/scenarios",
    "situations": "/situations",
    "documents": "/documents",
    "laws": "/legal-updates",
    "notifications": "/notifications",
    "profile": "/profile",
    "settings": "/settings",
    "learning": "/learning",
    "utility": "/utility",
    "taxes": "/taxes",
}


def main(page: ft.Page) -> None:
    private_uploads_dir = Path(__file__).resolve().parents[1] / "data" / "private_uploads"
    private_uploads_dir.mkdir(parents=True, exist_ok=True)
    exports_dir = Path(__file__).resolve().parents[1] / "data" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    page.title = "Белпомощник"
    page.theme = build_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = APP_COLORS["screen"]
    page.padding = 0
    page.window.min_width = 360
    page.window.min_height = 640

    default_users = {
        MOCK_USER["email"]: {
            "password": "123456",
            "profile": MOCK_USER.copy(),
        }
    }
    default_profile = MOCK_USER.copy()
    default_profile["interests"] = list(MOCK_USER.get("interests", []))
    default_settings = {
        "large_text": False,
        "high_contrast": False,
        "learning_mode": bool(MOCK_USER.get("learning_mode", True)),
        "email_notifications": True,
        "onboarding_completed": False,
        "dark_theme": False,
        "task_reminders_enabled": True,
        "task_reminder_days": 7,
        "document_reminders_enabled": True,
        "doc_reminder_days": 30,
        "utility_reminders_enabled": True,
        "utility_reminder_days": 7,
        "tax_reminders_enabled": True,
        "tax_reminder_days": 14,
        "law_update_notifications_enabled": True,
    }
    default_privacy_settings = {
        "hide_sensitive_documents": True,
    }
    default_state = {
        "users": copy.deepcopy(default_users),
        "auth_state": {
            "logged_in": False,
            "email": MOCK_USER["email"],
            "remember": True,
            "access_token": "",
            "refresh_token": "",
            "role": "guest",
            "_login_in_progress": False,
        },
        "app_user": copy.deepcopy(default_profile),
        "app_settings": copy.deepcopy(default_settings),
        "documents": copy.deepcopy(DOCUMENTS),
        "personal_documents": copy.deepcopy(DOCUMENTS),
        "privacy_settings": copy.deepcopy(default_privacy_settings),
        "uploaded_files": [],
        "institutions": copy.deepcopy(INSTITUTIONS),
        "admin_roles": copy.deepcopy(ADMIN_ROLES),
        "admin_users": copy.deepcopy(ADMIN_USERS),
        "admin_audit_logs": copy.deepcopy(ADMIN_AUDIT_LOGS),
        "current_admin_role": "content_editor",
        "official_sources": copy.deepcopy(OFFICIAL_SOURCES),
        "situations": copy.deepcopy(SITUATIONS),
        "situation_tasks": copy.deepcopy(SITUATION_TASKS),
        "notifications": copy.deepcopy(NOTIFICATIONS),
        "law_updates": copy.deepcopy(LEGAL_UPDATES),
        "law_detail": copy.deepcopy(LAW_DETAIL),
        "saved_problem_ids": [],
        "saved_law_ids": [],
        "favorite_scenario_ids": [],
        "theme_mode": "light",
        "doc_activity_log": [],
        "user_activity_log": [],
        "utility_accounts": copy.deepcopy(UTILITY_ACCOUNTS),
        "utility_payments": copy.deepcopy(UTILITY_PAYMENTS),
        "tax_obligations": copy.deepcopy(TAX_OBLIGATIONS),
    }
    stored_state = load_app_state(default_state)
    theme_mode_state = {"value": "dark" if stored_state.get("theme_mode") == "dark" else "light"}
    app_settings_from_store = stored_state.get("app_settings", {})
    if app_settings_from_store.get("dark_theme"):
        theme_mode_state["value"] = "dark"
    set_theme_mode(theme_mode_state["value"])
    page.theme = build_theme(
        theme_mode_state["value"],
        large_text=bool(app_settings_from_store.get("large_text", False)),
        high_contrast=bool(app_settings_from_store.get("high_contrast", False)),
    )
    page.theme_mode = ft.ThemeMode.DARK if theme_mode_state["value"] == "dark" else ft.ThemeMode.LIGHT
    page.bgcolor = APP_COLORS["screen"]
    session = getattr(page, "session", None)
    if session is not None:
        try:
            session.set("theme_mode", theme_mode_state["value"])
        except Exception:
            pass
    users = stored_state["users"]
    if MOCK_USER["email"] not in users:
        users[MOCK_USER["email"]] = default_users[MOCK_USER["email"]]
    auth_state = stored_state["auth_state"]
    auth_state.setdefault("role", "guest")
    auth_state.setdefault("_login_in_progress", False)
    if auth_state.get("logged_in") and auth_state.get("email") not in users:
        auth_state["logged_in"] = False
        auth_state["email"] = MOCK_USER["email"]
    # Тестовые аккаунты — загружаются с backend ниже после инициализации auth_api.
    test_accounts_state: dict[str, list[dict]] = {"items": []}
    app_user = stored_state["app_user"]
    app_user["interests"] = list(app_user.get("interests", []))
    for _profile_key, _profile_default in MOCK_USER.items():
        if _profile_key in ("interests", "interest_tags", "locations"):
            continue
        app_user.setdefault(_profile_key, _profile_default)
    app_user["interest_tags"] = list(app_user.get("interest_tags", []) or [])
    # Migrate flat region/city/district/address → locations[] (primary)
    if not app_user.get("locations"):
        app_user["locations"] = [{
            "id": "loc-primary",
            "label": "Прописка",
            "region": app_user.get("region", "Минская область"),
            "district": app_user.get("district", ""),
            "city": app_user.get("city", "Минск"),
            "address": app_user.get("address", ""),
            "is_primary": True,
        }]
    app_settings = stored_state["app_settings"]
    app_settings["dark_theme"] = theme_mode_state["value"] == "dark"

    def apply_page_theme() -> None:
        large = bool(app_settings.get("large_text", False))
        set_theme_mode(theme_mode_state["value"])
        set_large_text(large)
        page.theme_mode = ft.ThemeMode.DARK if theme_mode_state["value"] == "dark" else ft.ThemeMode.LIGHT
        page.theme = build_theme(
            theme_mode_state["value"],
            large_text=large,
            high_contrast=bool(app_settings.get("high_contrast", False)),
        )
        page.bgcolor = APP_COLORS["screen"]

    apply_page_theme()

    documents_state = stored_state.get("personal_documents") or stored_state["documents"]
    privacy_settings = stored_state["privacy_settings"]
    uploaded_files_state = stored_state["uploaded_files"]
    institutions_state = stored_state.get("institutions", copy.deepcopy(INSTITUTIONS))
    admin_roles_state = stored_state.get("admin_roles", copy.deepcopy(ADMIN_ROLES))
    admin_users_state = stored_state.get("admin_users", copy.deepcopy(ADMIN_USERS))
    admin_audit_logs_state = stored_state.get("admin_audit_logs", copy.deepcopy(ADMIN_AUDIT_LOGS))
    current_admin_role = {"value": stored_state.get("current_admin_role", "content_editor")}
    official_sources_state = stored_state.get("official_sources", copy.deepcopy(OFFICIAL_SOURCES))
    situations_state = stored_state["situations"]
    situation_tasks_state = stored_state["situation_tasks"]
    for task in situation_tasks_state:
        task.setdefault("situation_id", "childbirth")
    notifications_state = stored_state["notifications"]
    doc_activity_log_state: list[dict] = stored_state.get("doc_activity_log", [])
    user_activity_log_state: list[dict] = stored_state.get("user_activity_log", [])
    utility_accounts_state: list[dict] = stored_state.get("utility_accounts", copy.deepcopy(UTILITY_ACCOUNTS))
    utility_payments_state: list[dict] = stored_state.get("utility_payments", copy.deepcopy(UTILITY_PAYMENTS))
    tax_obligations_state: list[dict] = stored_state.get("tax_obligations", copy.deepcopy(TAX_OBLIGATIONS))
    from services.import_loader import (
        load_news as _load_news,
        load_problems as _load_problems,
        load_scenarios as _load_scenarios,
    )
    _imported_news = _load_news()
    law_updates_state = _imported_news if _imported_news else stored_state.get("law_updates", copy.deepcopy(LEGAL_UPDATES))
    # Replace mock lists in-place so all `from data.mock_data import X` see imported sets
    import data.mock_data as _mock_data
    _imported_problems = _load_problems()
    if _imported_problems:
        _mock_data.PROBLEMS[:] = _imported_problems
    _imported_scenarios = _load_scenarios()
    if _imported_scenarios:
        _mock_data.SCENARIO_TEMPLATES[:] = _imported_scenarios
    law_detail_state = stored_state.get("law_detail", copy.deepcopy(LAW_DETAIL))
    saved_problem_ids: set[str] = set(stored_state.get("saved_problem_ids", []))
    saved_law_ids: set[str] = set(stored_state.get("saved_law_ids", []))
    favorite_scenario_ids: set[str] = set(stored_state.get("favorite_scenario_ids", []))
    visible_document_ids: set[str] = set()
    active_document_scan_field: dict[str, ft.TextField | None] = {"field": None}
    active_file_import: dict[str, str] = {"mode": ""}
    current_problem = {"id": "lost-passport"}
    current_situation = {"id": "childbirth"}
    current_law = {"id": "law1"}
    current_scenario_template = {"id": SCENARIO_TEMPLATES[0]["id"]}
    email_preview_data: dict = {}
    situation_task_filter = {"value": "all"}
    user_notes_state: dict[str, list[dict]] = {}  # keyed by situation_id
    problem_filters = {"query": "", "category": "all"}
    search_filters = {"query": "", "pending_query": "", "filter": "all"}
    law_filters = {"query": "", "category": "all", "sort": "new"}
    scenario_filters = {"query": "", "category": "Все"}
    situation_filters = {"status": "Все"}
    search_debounce = {"token": 0}
    learning_state = {"enabled": bool(MOCK_USER.get("learning_mode", True))}
    problem_steps: dict[str, list[bool]] = {}
    quiz_states: dict[str, dict] = {}
    problem_overrides: dict[str, dict] = {}
    admin_api = AdminAPIClient()
    public_api = PublicAPIClient()
    auth_api = AuthAPIClient()
    user_api = UserAPIClient()

    # Загрузить список тестовых аккаунтов с backend (один раз при старте)
    try:
        test_accounts_state["items"] = auth_api.list_test_accounts()
    except Exception:
        test_accounts_state["items"] = []

    def _user_api_ready() -> UserAPIClient | None:
        """Вернуть авторизованный UserAPIClient, если есть токен и backend жив.

        Local-first: при недоступном backend возвращает None, приложение
        продолжает работать на локальном состоянии.
        """
        token = auth_state.get("access_token")
        if not token:
            return None
        try:
            if not auth_api.health():
                return None
        except Exception:
            return None
        user_api.set_token(token)
        return user_api

    def _sync_pull_documents() -> None:
        """Best-effort загрузка документов из backend в локальное состояние."""
        client = _user_api_ready()
        if client is None:
            return
        try:
            remote = user_sync.pull_documents(client)
        except UserAPIError:
            return
        for doc in remote:
            doc.setdefault("document_type", "Другое")
            doc["status"] = _document_status(doc.get("expiry_date", ""), "Активен")
            doc["icon"] = _document_icon(doc.get("document_type", "Другое"))
            doc["details"] = _document_details(doc)
        documents_state[:] = remote

    def _sync_pull_taxes() -> None:
        client = _user_api_ready()
        if client is None:
            return
        try:
            remote = user_sync.pull_taxes(client)
        except UserAPIError:
            return
        tax_obligations_state[:] = remote

    def _sync_push_tax(tax: dict) -> None:
        client = _user_api_ready()
        if client is None:
            return
        try:
            synced = user_sync.push_tax(client, tax)
        except UserAPIError:
            return
        if synced.get("id"):
            tax["id"] = synced["id"]

    def _sync_delete_tax(tax: dict) -> None:
        client = _user_api_ready()
        if client is None:
            return
        try:
            user_sync.delete_tax(client, tax)
        except UserAPIError:
            return

    def _sync_pull_utility() -> None:
        client = _user_api_ready()
        if client is None:
            return
        try:
            accounts, payments = user_sync.pull_utility(client)
        except UserAPIError:
            return
        utility_accounts_state[:] = accounts
        utility_payments_state[:] = payments

    def _sync_push_utility_account(account: dict) -> None:
        client = _user_api_ready()
        if client is None:
            return
        old_id = account.get("id")
        try:
            synced = user_sync.push_utility_account(client, account)
        except UserAPIError:
            return
        new_id = synced.get("id")
        if new_id and new_id != old_id:
            account["id"] = new_id
            for payment in utility_payments_state:
                if payment.get("account_id") == old_id:
                    payment["account_id"] = new_id

    def _sync_delete_utility_account(account: dict) -> None:
        client = _user_api_ready()
        if client is None:
            return
        try:
            user_sync.delete_utility_account(client, account)
        except UserAPIError:
            return

    def _sync_push_utility_payment(payment: dict) -> None:
        client = _user_api_ready()
        if client is None:
            return
        account = _find_item(utility_accounts_state, payment.get("account_id"))
        account_server_id = account.get("id") if account else payment.get("account_id")
        try:
            synced = user_sync.push_utility_payment(client, payment, account_server_id)
        except UserAPIError:
            return
        if synced and synced.get("id"):
            payment["id"] = synced["id"]

    def _sync_delete_utility_payment(payment: dict) -> None:
        client = _user_api_ready()
        if client is None:
            return
        try:
            user_sync.delete_utility_payment(client, payment)
        except UserAPIError:
            return
    public_state = {"connected": False, "error": "", "loaded_once": False, "last_sync": ""}
    from pages.admin_page import _DEFAULT_NOTIFICATION_RULES as _NOTIF_RULES_INIT, _DEFAULT_CATEGORIES as _CAT_INIT
    admin_state = {
        "connected": False,
        "error": "",
        "last_sync": "",
        "problems": [],
        "scenarios": [],
        "documents": [],
        "authorities": [],
        "deadlines": [],
        "selected_scenario_id": None,
        "scenario_detail": None,
        "loaded_once": False,
        "roles": admin_roles_state,
        "admin_users": admin_users_state,
        "audit_logs": admin_audit_logs_state,
        "current_role": current_admin_role["value"],
        "law_updates": law_updates_state,
        "official_sources": official_sources_state,
        # new
        "current_tab": "problems",
        "notification_rules": [r.copy() for r in _NOTIF_RULES_INIT],
        "categories": [c.copy() for c in _CAT_INIT],
    }
    admin_workspace_state: dict = {
        "selected_type": None,
        "selected_id": None,
        "expanded_sections": {"scenarios"},
        "expanded_scenarios": set(),
        "expanded_stages": set(),
        "search": "",
        "dirty": False,
    }
    admin_workspace_search_field = ft.TextField(
        hint_text="Поиск по контенту…",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=10,
        dense=True,
        content_padding=padding_symmetric(horizontal=12, vertical=8),
        text_size=13,
    )

    def _fetch_public_content(show_message: bool = False) -> None:
        """
        G2/G4 — Загрузить публичный контент из backend.
        При успехе обновляет problem_overrides (проблемы из БД).
        При ошибке оставляет mock-данные без изменений.
        """
        try:
            if not public_api.health():
                raise PublicAPIError("Backend недоступен.")
            problems_from_api = public_api.get_problems()
            for p in problems_from_api:
                slug = p.get("slug", "")
                if slug:
                    problem_overrides[slug] = p
            law_updates_from_api = public_api.get_law_updates()
            if law_updates_from_api:
                _api_law_ids = {str(item.get("id")) for item in law_updates_from_api}
                for law_item in law_updates_state:
                    if law_item.get("api_id") and str(law_item["api_id"]) in _api_law_ids:
                        pass
            public_state["connected"] = True
            public_state["error"] = ""
            public_state["loaded_once"] = True
            public_state["last_sync"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            if show_message:
                _show_message("Публичный контент обновлён из backend.")
        except PublicAPIError as exc:
            public_state["connected"] = False
            public_state["error"] = str(exc)

    def _law_category_name(category_id: str) -> str:
        return {
            "taxes": "Налоги",
            "home": "ЖКХ",
            "docs": "Документы",
            "family": "Семья",
            "work": "Работа",
            "auto": "Авто",
            "business": "Бизнес/ИП",
        }.get(category_id, category_id or "Категория")

    def _split_related_scenarios(value) -> list[str]:
        if isinstance(value, list):
            raw_items = value
        else:
            raw_items = re.split(r"[,;\n]+", str(value or ""))
        seen: set[str] = set()
        result: list[str] = []
        for item in raw_items:
            title = str(item or "").strip()
            if title and title.lower() not in seen:
                seen.add(title.lower())
                result.append(title)
        return result

    def _split_law_problem_ids(value) -> list[str]:
        if isinstance(value, list):
            raw_items = value
        else:
            raw_items = re.split(r"[,;\n]+", str(value or ""))
        seen: set[str] = set()
        result: list[str] = []
        for item in raw_items:
            problem_id = str(item or "").strip()
            normalized = problem_id.lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(problem_id)
        return result

    def _normalize_law_update(law: dict) -> dict:
        category = law.get("category") or "family"
        law.setdefault("category", category)
        law.setdefault("category_name", _law_category_name(category))
        law.setdefault("date", "Требует уточнения")
        law.setdefault("target", "Требует уточнения")
        law.setdefault("short", "Описание будет уточнено редактором.")
        law.setdefault("source_url", "https://pravo.by/")
        law.setdefault("status", "published")
        law.setdefault("priority", "medium")
        law.setdefault("processing_status", "new")
        law.setdefault("last_checked", "")
        law.setdefault("related_problems", [])
        if not isinstance(law.get("profile_tags"), list):
            law["profile_tags"] = []
        law["related_scenarios"] = _split_related_scenarios(law.get("related_scenarios"))
        law.setdefault(
            "what_to_do",
            "Проверьте актуальность информации на официальном ресурсе и уточните порядок действий перед подачей документов.",
        )
        return law

    def sync_task_notifications() -> None:
        today = date.today()
        situation_titles = {item.get("id"): item.get("title", "Ситуация") for item in situations_state}
        existing_by_id = {str(note.get("id")): note for note in notifications_state}
        _auto_sources = {"task_due", "doc_expiry", "email_demo", "util-readings", "util-payment", "tax_deadline", "law_important"}
        static_notifications = [note for note in notifications_state if note.get("source") not in _auto_sources]
        generated_notifications: list[dict] = []

        def _setting_bool(key: str, default: bool = True) -> bool:
            return bool(app_settings.get(key, default))

        def _setting_days(key: str, default: int) -> int:
            try:
                value = int(app_settings.get(key, default))
            except (TypeError, ValueError):
                value = default
            return max(0, value)

        task_reminder_days = _setting_days("task_reminder_days", 7)
        doc_reminder_days = _setting_days("doc_reminder_days", 30)
        utility_reminder_days = _setting_days("utility_reminder_days", 7)
        tax_reminder_days = _setting_days("tax_reminder_days", 14)

        if _setting_bool("task_reminders_enabled", True):
            for task in situation_tasks_state:
                if task.get("completed"):
                    continue
                due_date = parse_due_date(task.get("due_date")) or parse_due_date(task.get("deadline"))
                if not due_date:
                    continue
                days_left = (due_date - today).days
                if days_left > task_reminder_days:
                    continue

                task_id = str(task.get("id", ""))
                if not task_id:
                    continue
                notification_id = f"task-due-{task_id}"
                existing = existing_by_id.get(notification_id, {})
                situation_title = situation_titles.get(task.get("situation_id"), "Ситуация")
                if days_left < 0:
                    title = "Просрочена задача"
                    date_label = "Просрочено"
                elif days_left == 0:
                    title = "Задача на сегодня"
                    date_label = "Сегодня"
                elif days_left == 1:
                    title = "Задача на завтра"
                    date_label = "Завтра"
                else:
                    title = "Скоро срок задачи"
                    date_label = f"Через {days_left} дн."

                generated_notifications.append(
                    {
                        "id": notification_id,
                        "title": title,
                        "desc": f"{task.get('title', 'Задача')} · {situation_title} · срок {due_date.strftime('%d.%m.%Y')}",
                        "type": "task",
                        "is_read": bool(existing.get("is_read", False)),
                        "date": date_label,
                        "source": "task_due",
                        "task_id": task_id,
                        "situation_id": task.get("situation_id"),
                        "due_date": due_date.isoformat(),
                    }
                )

        soon_expiring_doc_titles: list[str] = []
        if _setting_bool("document_reminders_enabled", True):
            for doc in documents_state:
                expiry_raw = (doc.get("expiry_date") or "").strip()
                if not expiry_raw:
                    continue
                expiry = parse_due_date(expiry_raw)
                if not expiry:
                    continue
                days_left = (expiry - today).days
                if days_left > doc_reminder_days:
                    continue
                doc_id = str(doc.get("id", ""))
                notification_id = "doc-expiry-" + doc_id
                existing = existing_by_id.get(notification_id, {})
                if days_left < 0:
                    note_title = "Документ просрочен"
                    note_desc = doc.get("title", "Документ") + " · истёк " + str(-days_left) + " дн. назад"
                    date_label = "Просрочен"
                elif days_left == 0:
                    note_title = "Документ истекает сегодня"
                    note_desc = doc.get("title", "Документ") + " · действие заканчивается сегодня"
                    date_label = "Сегодня"
                else:
                    note_title = "Документ истекает скоро"
                    note_desc = doc.get("title", "Документ") + " · осталось " + str(days_left) + " дн."
                    date_label = "Через " + str(days_left) + " дн."
                generated_notifications.append(
                    {
                        "id": notification_id,
                        "title": note_title,
                        "desc": note_desc,
                        "type": "document",
                        "is_read": bool(existing.get("is_read", False)),
                        "date": date_label,
                        "source": "doc_expiry",
                        "doc_id": doc_id,
                        "expiry_date": expiry.isoformat(),
                        "days_left": days_left,
                    }
                )
                if 0 <= days_left <= 7:
                    soon_expiring_doc_titles.append(doc.get("title", "Документ"))

        if _setting_bool("utility_reminders_enabled", True):
            for payment in utility_payments_state:
                if payment.get("status") == "Оплачено":
                    continue
                for field, label, source_key in [
                    ("readings_deadline", "Передача показаний ЖКХ", "util-readings"),
                    ("payment_deadline", "Оплата ЖКХ", "util-payment"),
                ]:
                    deadline = parse_due_date(payment.get(field))
                    if not deadline:
                        continue
                    days_left = (deadline - today).days
                    if days_left > utility_reminder_days:
                        continue
                    pid = str(payment.get("id", ""))
                    note_id = source_key + "-" + pid
                    existing = existing_by_id.get(note_id, {})
                    if days_left < 0:
                        note_title = label + " — просрочено"
                        date_label = "Просрочено"
                    elif days_left == 0:
                        note_title = label + " — сегодня"
                        date_label = "Сегодня"
                    else:
                        note_title = label + " — через " + str(days_left) + " дн."
                        date_label = "Через " + str(days_left) + " дн."
                    generated_notifications.append(
                        {
                            "id": note_id,
                            "title": note_title,
                            "desc": payment.get("period", "Период") + " · " + label,
                            "type": "task",
                            "is_read": bool(existing.get("is_read", False)),
                            "date": date_label,
                            "source": source_key,
                            "due_date": deadline.isoformat(),
                        }
                    )

        if _setting_bool("tax_reminders_enabled", True):
            for obligation in tax_obligations_state:
                if obligation.get("status") == "Оплачено":
                    continue
                deadline = parse_due_date(obligation.get("deadline"))
                if not deadline:
                    continue
                days_left = (deadline - today).days
                if days_left > tax_reminder_days:
                    continue
                oid = str(obligation.get("id", ""))
                note_id = "tax-deadline-" + oid
                existing = existing_by_id.get(note_id, {})
                if days_left < 0:
                    note_title = "Налог просрочен"
                    date_label = "Просрочено"
                elif days_left == 0:
                    note_title = "Налоговый срок — сегодня"
                    date_label = "Сегодня"
                else:
                    note_title = "Налоговый срок — через " + str(days_left) + " дн."
                    date_label = "Через " + str(days_left) + " дн."
                generated_notifications.append(
                    {
                        "id": note_id,
                        "title": note_title,
                        "desc": obligation.get("title", "Обязательство") + " · " + (obligation.get("period") or ""),
                        "type": "law",
                        "is_read": bool(existing.get("is_read", False)),
                        "date": date_label,
                        "source": "tax_deadline",
                        "due_date": deadline.isoformat(),
                    }
                )

        if soon_expiring_doc_titles and app_settings.get("email_notifications", True):
            demo_id = "email-demo-notice"
            existing_demo = existing_by_id.get(demo_id, {})
            names = ", ".join(soon_expiring_doc_titles[:2])
            generated_notifications.append(
                {
                    "id": demo_id,
                    "title": "Email готов к отправке",
                    "desc": "Документы: " + names + ". В production будет отправлено SMTP-письмо.",
                    "type": "email_demo",
                    "is_read": bool(existing_demo.get("is_read", False)),
                    "date": "Авто",
                    "source": "email_demo",
                }
            )

        seen_law_ids = {str(note.get("law_id")) for note in static_notifications if note.get("source") == "law_important"}
        user_profile_tags_notif: set[str] = set(app_user.get("interest_tags") or [])
        if app_user.get("employment_status") == "ip":
            user_profile_tags_notif.add("ip")
        if app_user.get("has_children"):
            user_profile_tags_notif.update({"has_children", "family"})
        if app_user.get("owns_property"):
            user_profile_tags_notif.update({"housing_owner", "utility"})
        if _setting_bool("law_update_notifications_enabled", True):
            for law_item in law_updates_state:
                _normalize_law_update(law_item)
                if law_item.get("status") != "published":
                    continue
                if law_item.get("priority") not in ("high", "medium"):
                    continue
                law_item_id = str(law_item.get("id", ""))
                note_id = "law-important-" + law_item_id
                if note_id in seen_law_ids:
                    continue
                tag_match = bool(user_profile_tags_notif & set(law_item.get("profile_tags") or []))
                high_priority = law_item.get("priority") == "high"
                if not (high_priority or tag_match):
                    continue
                existing = existing_by_id.get(note_id, {})
                generated_notifications.append(
                    {
                        "id": note_id,
                        "title": "Важное изменение законодательства",
                        "desc": law_item.get("title", "Закон-апдейт") + " · " + law_item.get("category_name", ""),
                        "type": "law",
                        "is_read": bool(existing.get("is_read", False)),
                        "date": law_item.get("date", ""),
                        "source": "law_important",
                        "law_id": law_item_id,
                    }
                )

        generated_notifications.sort(key=lambda note: (parse_due_date(note.get("due_date")) or today, note.get("title", "")))
        notifications_state[:] = generated_notifications + static_notifications


    def _smtp_notification_stub(doc: dict) -> None:
        """
        C7 — SMTP-уведомление (заглушка MVP).
        Production: smtplib / SendGrid / Mailgun.
          recipient  = app_user["email"]
          subject    = f"Срок документа «{doc['title']}» истекает"
          template   = docs/email_templates/doc_expiry.html
          throttle   = 1 письмо/сутки на тип уведомления
          gate       = app_settings["email_notifications"] is True
        Производит запись в очередь email-уведомлений; рассылка по cron.
        """
        if app_settings.get("email_notifications", True):
            _show_message("[Demo] Email о документе «" + doc.get("title", "") + "» готов к отправке.")

    def save_current_state() -> None:
        sync_task_notifications()
        profile_snapshot = app_user.copy()
        profile_snapshot["interests"] = list(app_user.get("interests", []))
        current_email = auth_state.get("email")
        if current_email in users:
            users[current_email]["profile"] = profile_snapshot.copy()
        persisted_auth = auth_state.copy()
        if not persisted_auth.get("remember", True):
            persisted_auth["logged_in"] = False
        try:
            save_app_state(
                {
                    "users": users,
                    "auth_state": persisted_auth,
                    "app_user": profile_snapshot,
                    "app_settings": app_settings,
                    "documents": documents_state,
                    "personal_documents": documents_state,
                    "privacy_settings": privacy_settings,
                    "uploaded_files": uploaded_files_state,
                    "institutions": institutions_state,
                    "admin_roles": admin_roles_state,
                    "admin_users": admin_users_state,
                    "admin_audit_logs": admin_audit_logs_state,
                    "current_admin_role": current_admin_role["value"],
                    "official_sources": official_sources_state,
                    "situations": situations_state,
                    "situation_tasks": situation_tasks_state,
                    "notifications": notifications_state,
                    "law_updates": law_updates_state,
                    "law_detail": law_detail_state,
                    "saved_problem_ids": sorted(saved_problem_ids),
                    "saved_law_ids": sorted(saved_law_ids),
                    "favorite_scenario_ids": sorted(favorite_scenario_ids),
                    "theme_mode": theme_mode_state["value"],
                    "doc_activity_log": doc_activity_log_state[-200:],
                    "user_activity_log": user_activity_log_state[-500:],
                    "utility_accounts": utility_accounts_state,
                    "utility_payments": utility_payments_state,
                    "tax_obligations": tax_obligations_state,
                }
            )
        except OSError:
            pass

    def _open_control(control: ft.Control) -> None:
        open_method = getattr(page, "open", None)
        if callable(open_method):
            open_method(control)
            return
        show_dialog = getattr(page, "show_dialog", None)
        if callable(show_dialog):
            show_dialog(control)
            return
        if control not in page.overlay:
            page.overlay.append(control)
        control.open = True
        page.update()

    def _show_message(text: str, color: str = APP_COLORS["primary"]) -> None:
        _open_control(ft.SnackBar(content=ft.Text(text), bgcolor=color))

    _pdf_translit = str.maketrans(
        {
            "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E", "Ж": "Zh", "З": "Z",
            "И": "I", "Й": "Y", "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P", "Р": "R",
            "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "Kh", "Ц": "Ts", "Ч": "Ch", "Ш": "Sh",
            "Щ": "Sch", "Ъ": "", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "Yu", "Я": "Ya",
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
            "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
            "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh",
            "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
        }
    )

    def _pdf_text(value: str) -> str:
        cleaned = str(value or "").translate(_pdf_translit)
        cleaned = cleaned.encode("ascii", "replace").decode("ascii")
        return cleaned.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _write_simple_pdf(path: Path, title: str, lines: list[str]) -> None:
        visible_lines = [title, "", *lines][:38]
        text_ops = ["BT", "/F1 16 Tf", "50 792 Td", f"({_pdf_text(visible_lines[0])}) Tj"]
        text_ops.extend(["/F1 11 Tf"])
        for line in visible_lines[1:]:
            text_ops.append("0 -18 Td")
            text_ops.append(f"({_pdf_text(line)}) Tj")
        text_ops.append("ET")
        stream = "\n".join(text_ops).encode("ascii")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        chunks = [b"%PDF-1.4\n"]
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(sum(len(chunk) for chunk in chunks))
            chunks.append(f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
        xref_at = sum(len(chunk) for chunk in chunks)
        chunks.append(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        chunks.append(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            chunks.append(f"{offset:010d} 00000 n \n".encode("ascii"))
        chunks.append(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii")
        )
        path.write_bytes(b"".join(chunks))

    def _safe_upload_name(filename: str) -> str:
        source_name = Path(filename or "document").name
        stem = re.sub(r"[^A-Za-zА-Яа-я0-9_.-]+", "-", Path(source_name).stem, flags=re.UNICODE).strip(".-")
        suffix = re.sub(r"[^A-Za-z0-9.]+", "", Path(source_name).suffix)
        return f"{stem or 'document'}{suffix or '.dat'}"

    def _private_upload_relative_path(path: Path) -> str:
        project_root = Path(__file__).resolve().parents[1]
        try:
            return str(path.relative_to(project_root))
        except ValueError:
            return str(path)

    def _handle_document_files(files: list) -> None:
        target_field = active_document_scan_field.get("field")
        if not target_field:
            return
        if not files:
            _show_message("Файл не выбран.", APP_COLORS["warning"])
            return

        selected_file = files[0]
        selected_name = getattr(selected_file, "name", "") or "document"
        selected_path = getattr(selected_file, "path", None)
        selected_bytes = getattr(selected_file, "bytes", None)
        safe_name = _safe_upload_name(selected_name)
        destination = private_uploads_dir / f"{int(time.time())}-{safe_name}{ENCRYPTED_SUFFIX}"

        try:
            raw: bytes | None = None
            if selected_bytes:
                raw = selected_bytes
            elif selected_path:
                source_path = Path(selected_path)
                if not source_path.exists():
                    target_field.value = selected_name
                    target_field.update()
                    _show_message("Файл выбран, но локальный путь недоступен.", APP_COLORS["warning"])
                    return
                raw = source_path.read_bytes()
            else:
                target_field.value = selected_name
                target_field.update()
                _show_message(
                    "Не удалось получить данные файла. Укажите путь вручную.",
                    APP_COLORS["warning"],
                )
                return
            try:
                destination.write_bytes(encrypt_bytes(raw))
            except RuntimeError:
                destination.write_bytes(raw)
        except OSError:
            _show_message("Не удалось скопировать файл в локальное хранилище.", APP_COLORS["danger"])
            return

        relative_path = _private_upload_relative_path(destination)
        target_field.value = relative_path
        target_field.update()
        uploaded_files_state.append(
            {
                "id": f"upload-{int(time.time())}",
                "original_name": selected_name,
                "stored_path": relative_path,
                "uploaded_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        save_current_state()
        _show_message("Файл скана сохранён локально.")

    document_file_picker = ft.FilePicker()
    page.services.append(document_file_picker)
    document_import_file_picker = ft.FilePicker()
    page.services.append(document_import_file_picker)

    def _pick_document_scan(target_field: ft.TextField) -> None:
        active_document_scan_field["field"] = target_field

        async def pick_file() -> None:
            try:
                files = await document_file_picker.pick_files(allow_multiple=False, with_data=True)
            except Exception:
                _show_message("Выбор файла недоступен на этой платформе. Укажите путь вручную.", APP_COLORS["warning"])
                return
            _handle_document_files(files or [])

        page.run_task(pick_file)

    def _handle_document_import_files(files: list) -> None:
        if not files:
            _show_message("Файл для импорта не выбран.", APP_COLORS["warning"])
            return

        selected_file = files[0]
        selected_name = getattr(selected_file, "name", "") or "document.pdf"
        selected_path = getattr(selected_file, "path", None)
        selected_bytes = getattr(selected_file, "bytes", None)
        safe_name = _safe_upload_name(selected_name)
        destination = private_uploads_dir / f"{int(time.time())}-{safe_name}{ENCRYPTED_SUFFIX}"
        relative_path = selected_name

        try:
            raw: bytes | None = None
            if selected_bytes:
                raw = selected_bytes
            elif selected_path:
                source_path = Path(selected_path)
                if source_path.exists():
                    raw = source_path.read_bytes()
            if raw is not None:
                try:
                    destination.write_bytes(encrypt_bytes(raw))
                except RuntimeError:
                    destination.write_bytes(raw)
                relative_path = _private_upload_relative_path(destination)
            uploaded_files_state.append(
                {
                    "id": f"upload-{int(time.time())}",
                    "original_name": selected_name,
                    "stored_path": relative_path,
                    "uploaded_at": datetime.now().isoformat(timespec="seconds"),
                    "encrypted": True,
                }
            )
        except OSError:
            _show_message("Не удалось импортировать PDF-файл.", APP_COLORS["danger"])
            return

        title = Path(selected_name).stem.replace("_", " ").replace("-", " ").strip() or "Импортированный документ"
        payload = {
            "id": f"doc-import-{int(time.time())}",
            "title": title,
            "document_type": "Другое",
            "document_number": "",
            "issue_date": "",
            "expiry_date": "",
            "issuer": "",
            "comment": "Документ импортирован из PDF-файла.",
            "scan_path": relative_path,
            "status": "Активен",
            "icon": _document_icon("Другое"),
        }
        payload["details"] = _document_details(payload)
        documents_state.insert(0, payload)
        _log_doc_action("imported", payload)
        _log_user_action("doc_imported", f"Импортирован документ «{payload.get('title')}»")
        save_current_state()
        _show_message("PDF импортирован как личный документ.")
        route_change()

    def import_documents_pdf(_=None) -> None:
        active_file_import["mode"] = "document_pdf"

        async def pick_file() -> None:
            try:
                files = await document_import_file_picker.pick_files(
                    allow_multiple=False,
                    allowed_extensions=["pdf"],
                    with_data=True,
                )
            except Exception:
                _show_message("Импорт PDF недоступен на этой платформе.", APP_COLORS["warning"])
                return
            _handle_document_import_files(files or [])

        page.run_task(pick_file)

    def _slugify(value: str, fallback: str) -> str:
        base = re.sub(r"[^\w]+", "-", (value or "").strip().lower(), flags=re.UNICODE).strip("-")
        if not base:
            base = fallback
        return f"{base}-{int(time.time())}"

    def _to_int(value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _document_icon(document_type: str) -> str:
        return {
            "Паспорт / ID": "CREDIT_CARD",
            "Водительское удостоверение": "DIRECTIONS_CAR_OUTLINED",
            "Медкнижка": "MEDICAL_SERVICES_OUTLINED",
            "Свидетельство о рождении": "CHILD_CARE_OUTLINED",
            "Документ на жильё": "HOME_WORK_OUTLINED",
            "Квитанция / подтверждение оплаты": "RECEIPT_LONG_OUTLINED",
        }.get(document_type, "ARTICLE_OUTLINED")

    def _document_status(expiry_date: str | None, fallback: str = "Активен") -> str:
        parsed = parse_due_date(expiry_date)
        if not parsed:
            return fallback or "Активен"
        today = date.today()
        if parsed < today:
            return "Истёк"
        if parsed <= today + timedelta(days=60):
            return "Истекает скоро"
        return "Активен"

    def _document_details(document: dict) -> str:
        parts: list[str] = []
        document_number = (document.get("document_number") or "").strip()
        expiry_date = (document.get("expiry_date") or "").strip()
        if document_number:
            parts.append(document_number)
        if expiry_date:
            parts.append(f"действ. до {expiry_date}")
        return " · ".join(parts) or document.get("details") or "Данные будут уточнены"

    def _normalize_document(document: dict) -> None:
        document.setdefault("document_type", "Другое")
        document.setdefault("document_number", document.get("details", ""))
        document.setdefault("issue_date", "")
        document.setdefault("expiry_date", "")
        document.setdefault("issuer", "")
        document.setdefault("comment", "")
        document.setdefault("scan_path", "")
        document["status"] = _document_status(document.get("expiry_date"), document.get("status", "Активен"))
        document["icon"] = _document_icon(document.get("document_type", "Другое"))
        document["details"] = _document_details(document)

    def _close(control=None) -> None:
        dialogs = getattr(page, "_dialogs", None)
        if dialogs is not None:
            pop_dialog = getattr(page, "pop_dialog", None)
            if control is None:
                if callable(pop_dialog):
                    pop_dialog()
                    return
            elif control in dialogs.controls:
                if callable(pop_dialog):
                    top_dialog = next(
                        (dialog for dialog in reversed(dialogs.controls) if getattr(dialog, "open", False)),
                        None,
                    )
                    if top_dialog is control:
                        pop_dialog()
                        return
                control.open = False
                try:
                    control.update()
                except Exception:
                    pass
                try:
                    dialogs.update()
                except Exception:
                    page.update()
                return

        if control is None:
            page.update()
            return

        if control in page.overlay:
            control.open = False
            page.overlay.remove(control)
            page.update()
            return

        control.open = False
        try:
            control.update()
        except Exception:
            page.update()

    def _text_value(field: ft.TextField) -> str:
        return (field.value or "").strip()

    def _due_date_value(field: ft.TextField) -> str | None:
        raw_value = _text_value(field)
        if not raw_value:
            return None
        parsed = parse_due_date(raw_value)
        return parsed.isoformat() if parsed else ""

    def _parse_task_documents(value: str) -> list[dict]:
        documents: list[dict] = []
        for raw_item in re.split(r"[\n;,]+", value or ""):
            title = raw_item.strip(" \t-•")
            if not title:
                continue
            required = True
            if re.search(r"(необязательно|при необходимости|optional)", title, flags=re.IGNORECASE):
                required = False
                title = re.sub(
                    r"\(?\s*(необязательно|при необходимости|optional)\s*\)?",
                    "",
                    title,
                    flags=re.IGNORECASE,
                ).strip(" \t-•")
            if title:
                documents.append({"title": title, "required": required})
        return documents

    def _format_task_documents(documents: list[dict]) -> str:
        rows: list[str] = []
        for document in documents or []:
            title = document.get("title", "").strip()
            if not title:
                continue
            rows.append(title if document.get("required", True) else f"{title} (необязательно)")
        return "\n".join(rows)

    def _dialog_content(controls: list[ft.Control], preferred_width: int = 420) -> ft.Container:
        page_width = page.width or 393
        page_height = page.height or 760
        if page_width >= 720:
            safe_width = min(max(preferred_width, 420), 640)
        else:
            safe_width = max(300, min(preferred_width, int(page_width) - 40))
        max_height = max(260, int(page_height) - 220)
        needs_scroll = len(controls) >= 4 or page_height < 780
        return ft.Container(
            width=safe_width,
            height=max_height if needs_scroll else None,
            content=ft.Column(
                tight=True,
                spacing=12,
                scroll=ft.ScrollMode.AUTO if needs_scroll else None,
                controls=controls,
            ),
        )

    def _dialog_button(label: str, on_click, primary: bool = False, danger: bool = False) -> ft.Control:
        background = APP_COLORS["surface2"]
        foreground = APP_COLORS["muted"]
        side_color = APP_COLORS["stroke2"]
        if primary:
            background = APP_COLORS["blue"]
            foreground = ft.Colors.WHITE
            side_color = APP_COLORS["blue"]
        if danger:
            background = ft.Colors.with_opacity(0.12, APP_COLORS["danger"])
            foreground = APP_COLORS["danger"]
            side_color = ft.Colors.with_opacity(0.22, APP_COLORS["danger"])
        return ft.Button(
            content=ft.Text(label, size=14, weight=ft.FontWeight.W_700),
            height=44,
            style=ft.ButtonStyle(
                bgcolor=background,
                color=foreground,
                side=ft.BorderSide(1, side_color),
                padding=ft.Padding(left=18, top=10, right=18, bottom=10),
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
            on_click=on_click,
        )

    def _form_dialog(
        title: str,
        controls: list[ft.Control],
        actions: list[ft.Control],
        preferred_width: int = 420,
    ) -> ft.AlertDialog:
        return ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color=APP_COLORS["text"]),
            content=_dialog_content(controls, preferred_width=preferred_width),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding(left=24, top=22, right=24, bottom=8),
            content_padding=ft.Padding(left=24, top=6, right=24, bottom=10),
            actions_padding=ft.Padding(left=16, top=4, right=16, bottom=14),
            action_button_padding=ft.Padding(left=4, top=0, right=4, bottom=0),
            inset_padding=ft.Padding(left=20, top=24, right=20, bottom=24),
            bgcolor=APP_COLORS["surface"],
            shape=ft.RoundedRectangleBorder(radius=20),
        )

    def _find_item(items: list[dict], item_id) -> dict | None:
        return next((item for item in items if item.get("id") == item_id), None)

    def recalculate_situation_progress(situation_id: str) -> int:
        current_tasks = [task for task in situation_tasks_state if task.get("situation_id") == situation_id]
        completed = len([task for task in current_tasks if task.get("completed")])
        progress = round(completed / len(current_tasks) * 100) if current_tasks else 0
        situation = _find_item(situations_state, situation_id)
        if situation:
            situation["progress"] = progress
            situation["status"] = status_from_progress(progress)
        return progress

    def _normalize_task_dependencies() -> None:
        situations_by_id = {situation.get("id"): situation for situation in situations_state}
        templates_by_id = {template.get("id"): template for template in SCENARIO_TEMPLATES}
        tasks_by_situation: dict[str, list[dict]] = {}
        for task in situation_tasks_state:
            tasks_by_situation.setdefault(task.get("situation_id", "childbirth"), []).append(task)

        for situation_id, tasks in tasks_by_situation.items():
            situation = situations_by_id.get(situation_id, {})
            template = templates_by_id.get(situation.get("template_id"))
            if not template:
                for task in tasks:
                    task.setdefault("depends_on", [])
                    task.setdefault("depends_on_template_ids", [])
                    task.setdefault("institution_types", [])
                continue

            template_tasks_by_id = {task.get("id"): task for task in template.get("tasks", [])}
            local_task_by_template_id = {
                task.get("template_task_id"): task
                for task in tasks
                if task.get("template_task_id")
            }
            for task in tasks:
                template_task_id = task.get("template_task_id")
                template_task = template_tasks_by_id.get(template_task_id, {})
                template_dependencies = list(template_task.get("depends_on", []) or [])
                task.setdefault("depends_on_template_ids", template_dependencies)
                if "depends_on" not in task or not task.get("depends_on"):
                    task["depends_on"] = [
                        local_task_by_template_id[dependency_id]["id"]
                        for dependency_id in template_dependencies
                        if dependency_id in local_task_by_template_id
                    ]
                if template_task:
                    task.setdefault("stage_id", template_task.get("stage_id"))
                    task.setdefault("order_index", template_task.get("order_index", 0))
                    task.setdefault("institution_types", list(template_task.get("institution_types", []) or []))

    def _unmet_dependencies(task: dict, tasks: list[dict] | None = None) -> list[dict]:
        task_lookup = {item.get("id"): item for item in (tasks or situation_tasks_state)}
        unmet: list[dict] = []
        for dependency_id in task.get("depends_on", []) or []:
            dependency = task_lookup.get(dependency_id)
            if dependency and not dependency.get("completed"):
                unmet.append(dependency)
        return unmet

    def _dependency_message(task: dict, tasks: list[dict] | None = None) -> str:
        unmet = _unmet_dependencies(task, tasks)
        if not unmet:
            return ""
        titles = [item.get("title", "предыдущую задачу") for item in unmet]
        return "Сначала выполните: " + ", ".join(titles[:2]) + ("..." if len(titles) > 2 else "")

    def _tasks_with_dependency_state(tasks: list[dict]) -> list[dict]:
        result: list[dict] = []
        for task in tasks:
            item = task.copy()
            unmet = _unmet_dependencies(task, tasks)
            item["blocked"] = bool(unmet) and not bool(task.get("completed"))
            item["blocked_reason"] = _dependency_message(task, tasks)
            item["blocked_by_titles"] = [dependency.get("title", "Задача") for dependency in unmet]
            item["matched_institutions"] = match_institutions(
                institutions_state,
                app_user,
                item.get("institution_types", []),
                limit=2,
            )
            result.append(item)
        return result

    _normalize_task_dependencies()
    for document in documents_state:
        _normalize_document(document)
    for situation in situations_state:
        recalculate_situation_progress(situation["id"])
    sync_task_notifications()

    def _confirm_action(title: str, message: str, confirm_label: str, on_confirm, danger: bool = False) -> None:
        dialog = _form_dialog(
            title,
            [ft.Text(message, size=15, color=APP_COLORS["muted"])],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button(confirm_label, lambda _: on_confirm(dialog), primary=not danger, danger=danger),
            ],
            preferred_width=400,
        )
        _open_control(dialog)

    def reset_demo_data(_=None) -> None:
        def reset(dialog) -> None:
            initial = copy.deepcopy(default_state)
            users.clear()
            users.update(initial["users"])
            auth_state.clear()
            auth_state.update(initial["auth_state"])
            auth_state["logged_in"] = True
            auth_state["email"] = MOCK_USER["email"]
            auth_state["remember"] = True
            app_user.clear()
            app_user.update(initial["app_user"])
            app_user["interests"] = list(app_user.get("interests", []))
            app_settings.clear()
            app_settings.update(initial["app_settings"])
            theme_mode_state["value"] = initial["theme_mode"]
            app_settings["dark_theme"] = False
            set_theme_mode(theme_mode_state["value"])
            apply_page_theme()
            session = getattr(page, "session", None)
            if session is not None:
                try:
                    session.set("theme_mode", theme_mode_state["value"])
                except Exception:
                    pass
            privacy_settings.clear()
            privacy_settings.update(initial["privacy_settings"])
            uploaded_files_state[:] = initial["uploaded_files"]
            institutions_state[:] = initial["institutions"]
            admin_roles_state[:] = initial["admin_roles"]
            admin_users_state[:] = initial["admin_users"]
            admin_audit_logs_state[:] = initial["admin_audit_logs"]
            current_admin_role["value"] = initial["current_admin_role"]
            admin_state["roles"] = admin_roles_state
            admin_state["admin_users"] = admin_users_state
            admin_state["audit_logs"] = admin_audit_logs_state
            admin_state["current_role"] = current_admin_role["value"]
            official_sources_state[:] = initial["official_sources"]
            admin_state["official_sources"] = official_sources_state
            visible_document_ids.clear()
            documents_state[:] = initial["personal_documents"]
            for document in documents_state:
                _normalize_document(document)
            situations_state[:] = initial["situations"]
            situation_tasks_state[:] = initial["situation_tasks"]
            notifications_state[:] = initial["notifications"]
            law_updates_state[:] = initial["law_updates"]
            law_detail_state.clear()
            law_detail_state.update(initial["law_detail"])
            admin_state["law_updates"] = law_updates_state
            saved_problem_ids.clear()
            saved_law_ids.clear()
            favorite_scenario_ids.clear()
            problem_steps.clear()
            quiz_states.clear()
            current_problem["id"] = "lost-passport"
            current_situation["id"] = situations_state[0]["id"] if situations_state else "childbirth"
            current_scenario_template["id"] = SCENARIO_TEMPLATES[0]["id"]
            app_settings["learning_mode"] = bool(app_user.get("learning_mode", True))
            learning_state["enabled"] = app_settings["learning_mode"]
            for situation in situations_state:
                recalculate_situation_progress(situation["id"])
            save_current_state()
            _close(dialog)
            _show_message("Данные сброшены.")
            page.run_task(page.push_route, "/")

        _confirm_action(
            "Сбросить данные?",
            "Будут восстановлены начальные документы, ситуации, задачи, уведомления и профиль.",
            "Сбросить",
            reset,
            danger=True,
        )

    def _load_childbirth_scenario() -> dict | None:
        cached = problem_overrides.get("childbirth")
        if cached:
            return cached
        try:
            scenario = public_api.get_scenario("rozhdenie-rebenka")
            stages = sorted(scenario.get("stages", []), key=lambda item: item.get("order_index", 0))
            all_steps: list[dict] = []
            for stage in stages:
                for step in sorted(stage.get("steps", []), key=lambda item: item.get("order_index", 0)):
                    all_steps.append(step)

            immediate = [item.get("description") or item.get("title", "") for item in all_steps[:3]]
            progress_steps = [item.get("title", "") for item in all_steps]

            documents_set: list[str] = []
            terms_set: list[str] = []
            contacts_set: list[str] = []
            for step in all_steps:
                for doc in step.get("documents", []):
                    title = doc.get("title", "").strip()
                    if title and title not in documents_set:
                        documents_set.append(title)
                deadline = step.get("deadline")
                if deadline and deadline.get("title") and deadline["title"] not in terms_set:
                    terms_set.append(deadline["title"])
                authority = step.get("authority")
                if authority and authority.get("title") and authority["title"] not in contacts_set:
                    contacts_set.append(authority["title"])

            override = {
                "id": "childbirth",
                "title": scenario.get("title", "Рождение ребёнка"),
                "category": "family",
                "category_name": "Семья",
                "description": scenario.get("short_description") or scenario.get("description", ""),
                "immediate": immediate or ["Откройте карточку и следуйте шагам по порядку."],
                "steps": progress_steps or ["Шаги будут добавлены позже."],
                "documents": documents_set or ["Документы будут уточнены после загрузки сценария."],
                "terms": terms_set or ["Сроки будут уточнены после загрузки сценария."],
                "contacts": contacts_set or ["Организации будут уточнены после загрузки сценария."],
                "errors": [
                    "Пропускать обязательные этапы и нарушать порядок.",
                    "Не проверять актуальность требований перед подачей документов.",
                ],
            }
            problem_overrides["childbirth"] = override
            public_state["connected"] = True
            public_state["error"] = ""
            return override
        except PublicAPIError as exc:
            public_state["connected"] = False
            public_state["error"] = str(exc)
            return None

    def _apply_login(normalized_email: str, profile: dict, remember: bool, tokens: dict | None = None) -> None:
        auth_state["logged_in"] = True
        auth_state["email"] = normalized_email
        auth_state["remember"] = bool(remember)
        # Дефолтная роль из локального профиля или citizen; backend перезапишет точнее.
        auth_state["role"] = profile.get("role") or "citizen"
        if tokens:
            auth_state["access_token"] = tokens.get("access_token", "")
            auth_state["refresh_token"] = tokens.get("refresh_token", "")
            # Подтянуть точную роль с backend через /api/auth/me
            try:
                user_api.set_token(auth_state["access_token"])
                me = user_api._request("GET", "/api/auth/me")
                if me and me.get("role"):
                    auth_state["role"] = me["role"]
            except Exception:
                pass
            _sync_pull_documents()
            _sync_pull_taxes()
            _sync_pull_utility()
        app_user.update(profile)
        app_user["first_name"] = app_user.get("name", "Пользователь").split()[0]
        app_user["interests"] = list(app_user.get("interests", []))
        app_settings["learning_mode"] = bool(app_user.get("learning_mode", app_settings["learning_mode"]))
        learning_state["enabled"] = app_settings["learning_mode"]
        save_current_state()
        page.run_task(page.push_route, "/")

    def login_user(email: str, password: str, remember: bool = True) -> None:
        # Race-фикс: блокировать повторные клики пока идёт запрос.
        if auth_state.get("_login_in_progress"):
            return
        auth_state["_login_in_progress"] = True
        try:
            normalized_email = (email or "").strip().lower()
            backend_alive = False
            tokens: dict | None = None
            try:
                backend_alive = auth_api.health()
            except Exception:
                backend_alive = False

            if backend_alive:
                # Backend живой — используем ТОЛЬКО его. Локальный fallback не запускаем,
                # иначе при правильных credentials backend возвращает 401 (юзер не в БД)
                # а local fallback впускает — гонка.
                try:
                    tokens = auth_api.login(normalized_email, password)
                except AuthAPIError as exc:
                    if exc.status_code in (400, 401):
                        _show_message("Неверный email или пароль.", APP_COLORS["danger"])
                    else:
                        _show_message(f"Ошибка входа: {exc}", APP_COLORS["danger"])
                    return
                local_user = users.get(normalized_email)
                profile = (local_user or {}).get("profile") or {
                    "name": normalized_email.split("@")[0].title(),
                    "email": normalized_email,
                    "city": "Минск",
                    "region": "Минская область",
                    "avatar_url": MOCK_USER["avatar_url"],
                    "interests": [],
                    "learning_mode": True,
                }
                _apply_login(normalized_email, profile, remember, tokens)
                _show_message("Вход выполнен.")
                return

            # Backend недоступен — fallback на локальный словарь (offline-режим).
            local_user = users.get(normalized_email)
            if not local_user or local_user.get("password") != password:
                _show_message("Неверный email или пароль.", APP_COLORS["danger"])
                return
            _apply_login(normalized_email, local_user["profile"], remember)
            _show_message("Вы вошли в профиль.")
        finally:
            auth_state["_login_in_progress"] = False

    def oauth_login(provider: str) -> None:
        """Demo Google / Yandex OAuth — issues a backend JWT for a demo identity."""
        demo = {
            "google": ("ivan.google@gmail.com", "Иван Иванов"),
            "yandex": ("ivan.yandex@yandex.ru", "Иван Иванов"),
        }.get(provider, ("ivan@example.by", "Иван Иванов"))
        email, name = demo
        tokens: dict | None = None
        try:
            if auth_api.health():
                tokens = auth_api.oauth(provider, email, name)
        except AuthAPIError:
            tokens = None
        profile = {
            "name": name,
            "first_name": name.split()[0],
            "email": email,
            "region": "Минская область",
            "city": "Минск",
            "avatar_url": MOCK_USER["avatar_url"],
            "interests": [],
            "learning_mode": True,
        }
        users.setdefault(email, {"password": f"{provider}-oauth", "profile": profile})
        _apply_login(email, profile, True, tokens)
        label = "Google" if provider == "google" else "Яндекс"
        _show_message(f"Вход через {label} выполнен.")

    def register_user(
        name: str,
        email: str,
        city: str,
        region: str,
        password: str,
        confirm_password: str,
        accepted: bool,
        location: dict | None = None,
    ) -> None:
        normalized_email = (email or "").strip().lower()
        normalized_name = (name or "").strip()
        if len(normalized_name) < 2:
            _show_message("Введите имя и фамилию.", APP_COLORS["warning"])
            return
        if "@" not in normalized_email:
            _show_message("Введите корректный email.", APP_COLORS["warning"])
            return
        if len(password or "") < 6:
            _show_message("Пароль должен быть не короче 6 символов.", APP_COLORS["warning"])
            return
        if password != confirm_password:
            _show_message("Пароли не совпадают.", APP_COLORS["warning"])
            return
        if not accepted:
            _show_message("Подтвердите согласие с условиями использования.", APP_COLORS["warning"])
            return
        if normalized_email in users:
            _show_message("Пользователь с таким email уже есть.", APP_COLORS["warning"])
            return

        loc = location or {}
        primary_location = {
            "id": "loc-primary",
            "label": loc.get("label", "Прописка"),
            "region": (loc.get("region") or region or "Минская область").strip(),
            "district": loc.get("district", ""),
            "city": (loc.get("city") or city or "Минск").strip(),
            "address": loc.get("address", ""),
            "is_primary": True,
        }
        profile = {
            "name": normalized_name,
            "first_name": normalized_name.split()[0],
            "email": normalized_email,
            "region": primary_location["region"],
            "city": primary_location["city"],
            "district": primary_location["district"],
            "address": primary_location["address"],
            "locations": [primary_location],
            "avatar_url": MOCK_USER["avatar_url"],
            "interests": [],
            "learning_mode": True,
        }
        users[normalized_email] = {"password": password, "profile": profile}

        # Try backend registration (JWT). Backend offline → local-only account.
        tokens: dict | None = None
        try:
            if auth_api.health():
                tokens = auth_api.register(normalized_name, normalized_email, password)
        except AuthAPIError as exc:
            if exc.status_code == 400:
                _show_message("Пользователь с таким email уже есть.", APP_COLORS["warning"])
                return
            tokens = None

        _apply_login(normalized_email, profile, True, tokens)
        _show_message("Аккаунт создан (API)." if tokens else "Аккаунт создан.")

    def logout_user(_=None) -> None:
        auth_state["logged_in"] = False
        auth_state["access_token"] = ""
        auth_state["refresh_token"] = ""
        auth_state["role"] = "guest"
        save_current_state()
        _show_message("Вы вышли из профиля.")
        page.run_task(page.push_route, "/")  # гостевой режим — на главную, не на /login

    def switch_test_account(email: str, name: str = "", role: str = "") -> None:
        """Быстрый login через переключатель тестовых аккаунтов."""
        if not email:
            return
        # Используем стандартный login_user — backend проверит пароль
        login_user(email, "Test12345!", remember=True)

    def go_to(route: str) -> None:
        page.run_task(page.push_route, route)

    def _open_guest_modal(description: str = "Чтобы выполнить это действие, нужен аккаунт.") -> None:
        _open_guest_modal_dialog(page, go_to, description=description)

    def require_user(description: str = "Чтобы выполнить это действие, нужен аккаунт.") -> bool:
        """Защита мутирующих handlers. True если пользователь авторизован."""
        return role_guard.require_auth(auth_state, lambda: _open_guest_modal(description))

    def complete_onboarding(_=None) -> None:
        app_settings["onboarding_completed"] = True
        save_current_state()
        page.run_task(page.push_route, "/" if auth_state.get("logged_in") else "/login")

    def toggle_favorite_scenario(template_id: str) -> None:
        if template_id in favorite_scenario_ids:
            favorite_scenario_ids.remove(template_id)
            _show_message("Сценарий убран из избранного.")
        else:
            favorite_scenario_ids.add(template_id)
            _show_message("Сценарий добавлен в избранное.")
        save_current_state()
        route_change()

    def create_plan(_=None) -> None:
        if current_problem["id"] == "childbirth":
            create_situation_from_template("childbirth")
            return
        problem = problem_overrides.get(current_problem["id"]) or find_problem(current_problem["id"])
        situation_id = f"plan-{current_problem['id']}"
        existing = next((item for item in situations_state if item["id"] == situation_id), None)
        if existing:
            current_situation["id"] = situation_id
            _show_message("План уже есть в «Моих ситуациях».")
        else:
            situations_state.insert(
                0,
                {
                    "id": situation_id,
                    "title": problem["title"],
                    "status": "В процессе",
                    "progress": 0,
                },
            )
            current_situation["id"] = situation_id
            save_current_state()
            _show_message("Персональный план создан.")
        page.run_task(page.push_route, "/situations")

    def save_problem(_=None) -> None:
        saved_problem_ids.add(current_problem["id"])
        save_current_state()
        _show_message("Карточка сохранена.")

    def open_problem(problem_id: str) -> None:
        current_problem["id"] = problem_id or "lost-passport"
        if current_problem["id"] == "childbirth":
            _load_childbirth_scenario()
        page.run_task(page.push_route, "/problem-detail")

    def open_situation(situation_id: str) -> None:
        current_situation["id"] = situation_id or "childbirth"
        situation_task_filter["value"] = "all"
        page.run_task(page.push_route, "/situation-detail")

    def open_law(law_id: str) -> None:
        current_law["id"] = law_id or "law1"
        page.run_task(page.push_route, "/law-detail")

    def open_scenario_templates(_=None) -> None:
        page.run_task(page.push_route, "/scenarios")

    def open_scenario_template(template_id: str) -> None:
        current_scenario_template["id"] = template_id or SCENARIO_TEMPLATES[0]["id"]
        page.run_task(page.push_route, "/scenario-detail")

    def go_back_to_scenarios(_=None) -> None:
        page.run_task(page.push_route, "/scenarios")

    def open_template_source(url: str) -> None:
        if url:
            page.launch_url(url)

    def _create_situation_from_template(template_id: str) -> None:
        if not require_user("Чтобы создать личную ситуацию, войдите или зарегистрируйтесь."):
            return
        template = find_scenario_template(template_id)
        created_at = int(time.time() * 1000)
        situation_id = f"scenario-{template['id']}-{created_at}"
        stages_by_id = {stage["id"]: stage for stage in template.get("stages", [])}
        situations_state.insert(
            0,
            {
                "id": situation_id,
                "template_id": template["id"],
                "title": template["title"],
                "status": "В процессе",
                "progress": 0,
                "category": template.get("category", ""),
                "estimated_duration": template.get("estimated_duration", ""),
                "difficulty": template.get("difficulty", ""),
            },
        )
        template_task_ids = {
            task.get("id"): f"{situation_id}-task-{index}"
            for index, task in enumerate(template.get("tasks", []), start=1)
            if task.get("id")
        }
        for index, task in enumerate(template.get("tasks", []), start=1):
            stage = stages_by_id.get(task.get("stage_id"), {})
            due_date = date.today() + timedelta(days=int(task.get("due_in_days", index * 3)))
            situation_tasks_state.append(
                {
                    "id": template_task_ids.get(task.get("id"), f"{situation_id}-task-{index}"),
                    "situation_id": situation_id,
                    "template_task_id": task.get("id"),
                    "stage_id": task.get("stage_id"),
                    "stage_title": stage.get("title", "Этап"),
                    "stage_order": stage.get("order_index", 999),
                    "order_index": index,
                    "title": task["title"],
                    "completed": False,
                    "depends_on": [
                        template_task_ids[dependency_id]
                        for dependency_id in task.get("depends_on", []) or []
                        if dependency_id in template_task_ids
                    ],
                    "depends_on_template_ids": list(task.get("depends_on", []) or []),
                    "institution_types": list(task.get("institution_types", []) or []),
                    "deadline": task.get("deadline", "Без срока"),
                    "due_date": due_date.isoformat(),
                    "documents": [document.copy() for document in task.get("documents", [])],
                }
            )
        recalculate_situation_progress(situation_id)
        current_situation["id"] = situation_id
        _log_user_action("situation_created", f"Создана ситуация «{template['title']}»", f"Сценарий: {template.get('category', '')}")
        save_current_state()
        _show_message("Ситуация создана из шаблона.")
        page.run_task(page.push_route, "/situations")

    def create_situation_from_template(template_id: str) -> None:
        template = find_scenario_template(template_id)
        existing = next(
            (item for item in situations_state if item.get("template_id") == template.get("id") and item.get("progress", 0) < 100),
            None,
        )
        if existing:
            current_situation["id"] = existing["id"]

            def open_existing(dialog) -> None:
                _close(dialog)
                page.run_task(page.push_route, "/situation-detail")

            def create_anyway(dialog) -> None:
                _close(dialog)
                _create_situation_from_template(template_id)

            dialog = _form_dialog(
                "Такая ситуация уже есть",
                [
                    ft.Text(
                    f"У вас уже есть активная ситуация «{existing.get('title', template['title'])}». "
                    "Открыть её или создать ещё одну?",
                    size=15,
                    color=APP_COLORS["muted"],
                    )
                ],
                [
                    _dialog_button("Открыть", lambda _: open_existing(dialog), primary=True),
                    _dialog_button("Создать ещё", lambda _: create_anyway(dialog)),
                ],
                preferred_width=420,
            )
            _open_control(dialog)
            return
        _create_situation_from_template(template_id)

    def open_problem_search(query: str) -> None:
        problem_filters["query"] = (query or "").strip()
        problem_filters["category"] = "all"
        page.run_task(page.push_route, "/problems")

    def open_global_search(query: str = "") -> None:
        search_filters["query"] = (query or "").strip()
        search_filters["pending_query"] = search_filters["query"]
        search_filters["filter"] = "all"
        page.run_task(page.push_route, "/search")

    def update_search_query(query: str) -> None:
        search_filters["pending_query"] = query or ""
        search_debounce["token"] += 1
        token = search_debounce["token"]

        async def apply_debounced_search() -> None:
            await asyncio.sleep(0.6)
            if token == search_debounce["token"]:
                search_filters["query"] = search_filters.get("pending_query", "")
                route_change()

        page.run_task(apply_debounced_search)

    def update_search_filter(filter_key: str) -> None:
        search_filters["filter"] = filter_key or "all"
        route_change()

    def open_problem_category(category_id: str) -> None:
        problem_filters["query"] = ""
        problem_filters["category"] = category_id or "all"
        page.run_task(page.push_route, "/problems")

    def update_problem_query(query: str) -> None:
        problem_filters["query"] = query or ""
        route_change()

    def update_problem_category(category_id: str) -> None:
        problem_filters["category"] = category_id or "all"
        route_change()

    def update_law_query(query: str) -> None:
        law_filters["query"] = query or ""
        route_change()

    def update_law_category(category_id: str) -> None:
        law_filters["category"] = category_id or "all"
        route_change()

    def update_law_sort(sort_id: str) -> None:
        law_filters["sort"] = sort_id or "new"
        route_change()

    def update_scenario_query(query: str) -> None:
        scenario_filters["query"] = query or ""
        route_change()

    def update_scenario_category(category_name: str) -> None:
        scenario_filters["category"] = category_name or "Все"
        route_change()

    def update_situation_filter(status: str) -> None:
        situation_filters["status"] = status or "Все"
        route_change()

    def get_step_values(problem_id: str) -> list[bool]:
        if problem_id == "childbirth":
            override = problem_overrides.get("childbirth")
            if override is None:
                override = _load_childbirth_scenario()
            steps_count = len((override or find_problem(problem_id)).get("steps", []))
        else:
            steps_count = len(find_problem(problem_id).get("steps", []))
        values = problem_steps.setdefault(problem_id, [False] * steps_count)
        if len(values) < steps_count:
            values.extend([False] * (steps_count - len(values)))
        return values[:steps_count]

    def toggle_problem_step(index: int, value: bool) -> None:
        values = get_step_values(current_problem["id"])
        if 0 <= index < len(values):
            values[index] = value
            problem_steps[current_problem["id"]] = values
        route_change()

    def get_quiz_state(problem_id: str) -> dict:
        return quiz_states.setdefault(problem_id, {"answers": {}, "submitted": False})

    def set_quiz_answer(question_id: str, answer: str) -> None:
        quiz_state = get_quiz_state(current_problem["id"])
        quiz_state["answers"][question_id] = answer
        quiz_state["submitted"] = False
        route_change()

    def submit_quiz(_=None) -> None:
        get_quiz_state(current_problem["id"])["submitted"] = True
        route_change()

    def reset_quiz(_=None) -> None:
        quiz_states[current_problem["id"]] = {"answers": {}, "submitted": False}
        route_change()

    def toggle_learning_mode(value: bool) -> None:
        learning_state["enabled"] = bool(value)
        app_settings["learning_mode"] = bool(value)
        app_user["learning_mode"] = bool(value)
        save_current_state()
        route_change()

    def go_back_to_problems(_=None) -> None:
        page.run_task(page.push_route, "/problems")

    def go_back_to_situations(_=None) -> None:
        page.run_task(page.push_route, "/situations")

    def go_back_to_laws(_=None) -> None:
        page.run_task(page.push_route, "/legal-updates")

    def _document_form_fields(document: dict | None = None) -> dict[str, ft.Control]:
        data = document or {}
        field_padding = ft.Padding(left=14, top=10, right=14, bottom=10)

        def text_field(
            label: str,
            value: str = "",
            hint_text: str = "",
            multiline: bool = False,
            min_lines: int | None = None,
            max_lines: int | None = None,
            helper: str | None = None,
        ) -> ft.TextField:
            return ft.TextField(
                label=label,
                value=value,
                hint_text=hint_text,
                multiline=multiline,
                min_lines=min_lines,
                max_lines=max_lines,
                helper=helper,
                helper_max_lines=2 if helper else None,
                border_radius=14,
                filled=True,
                bgcolor=APP_COLORS["surface"],
                border_color=APP_COLORS["stroke2"],
                focused_border_color=APP_COLORS["blue"],
                text_size=14,
                content_padding=field_padding,
            )

        def dropdown(label: str, value: str, options: list[str]) -> ft.Dropdown:
            return ft.Dropdown(
                label=label,
                value=value,
                border_radius=14,
                filled=True,
                bgcolor=APP_COLORS["surface"],
                border_color=APP_COLORS["stroke2"],
                focused_border_color=APP_COLORS["blue"],
                text_size=14,
                content_padding=field_padding,
                options=[ft.dropdown.Option(item) for item in options],
            )

        fields: dict[str, ft.Control] = {
            "title": text_field("Название документа", data.get("title", ""), "Например: Паспорт"),
            "document_type": dropdown("Тип документа", data.get("document_type", DOCUMENT_TYPES[0]), DOCUMENT_TYPES),
            "document_number": text_field("Серия / номер", data.get("document_number", ""), "Например: MP1234567"),
            "issue_date": text_field("Дата выдачи", data.get("issue_date", ""), "Например: 2024-05-20 или 20.05.2024"),
            "expiry_date": text_field("Срок действия", data.get("expiry_date", ""), "Например: 2030-05-20 или 20.05.2030"),
            "issuer": text_field("Организация выдачи", data.get("issuer", ""), "Например: ОГиМ"),
            "scan_path": text_field(
                "Файл / скан",
                data.get("scan_path", ""),
                "Например: data/private_uploads/passport.pdf",
                helper="Файл хранится локально. В production потребуется шифрование.",
            ),
            "comment": text_field(
                "Комментарий",
                data.get("comment", ""),
                "Заметки по документу",
                multiline=True,
                min_lines=2,
                max_lines=4,
            ),
        }
        fields["scan_pick"] = ft.OutlinedButton(
            "Выбрать файл скана",
            icon=ft.Icons.UPLOAD_FILE_OUTLINED,
            height=44,
            style=ft.ButtonStyle(
                color=APP_COLORS["primary"],
                side=ft.BorderSide(1, APP_COLORS["border"]),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda _: _pick_document_scan(fields["scan_path"]),
        )
        return fields

    def _dialog_section(title: str, icon, controls: list[ft.Control]) -> ft.Container:
        return ft.Container(
            padding=ft.Padding(left=14, top=14, right=14, bottom=14),
            border_radius=18,
            bgcolor=APP_COLORS["surface2"],
            border=border_all(APP_COLORS["stroke2"]),
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=34,
                                height=34,
                                border_radius=12,
                                alignment=ft.Alignment(0, 0),
                                bgcolor=APP_COLORS["active"],
                                content=ft.Icon(icon, size=18, color=APP_COLORS["blue"]),
                            ),
                            ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=APP_COLORS["text"]),
                        ],
                    ),
                    *controls,
                ],
            ),
        )

    def _responsive_fields(*controls: ft.Control) -> ft.ResponsiveRow:
        return ft.ResponsiveRow(
            columns=12,
            spacing=10,
            run_spacing=10,
            controls=[
                ft.Container(col={"xs": 12, "sm": 6}, content=control)
                for control in controls
            ],
        )

    def _document_form_controls(fields: dict[str, ft.Control]) -> list[ft.Control]:
        return [
            ft.Container(
                padding=ft.Padding(left=14, top=12, right=14, bottom=12),
                border_radius=18,
                bgcolor=ft.Colors.with_opacity(0.55, APP_COLORS["active"]),
                border=border_all(ft.Colors.with_opacity(0.45, APP_COLORS["blue"])),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Icon(ft.Icons.PRIVACY_TIP_OUTLINED, size=20, color=APP_COLORS["blue"]),
                        ft.Text(
                            "Документ хранится локально. Номер по умолчанию скрывается в интерфейсе.",
                            size=13,
                            color=APP_COLORS["muted"],
                            expand=True,
                        ),
                    ],
                ),
            ),
            _dialog_section(
                "Документ",
                ft.Icons.BADGE_OUTLINED,
                [
                    _responsive_fields(fields["title"], fields["document_type"]),
                    fields["document_number"],
                ],
            ),
            _dialog_section(
                "Сроки и выдача",
                ft.Icons.EVENT_AVAILABLE_OUTLINED,
                [
                    _responsive_fields(fields["issue_date"], fields["expiry_date"]),
                    fields["issuer"],
                ],
            ),
            _dialog_section(
                "Скан или файл",
                ft.Icons.FOLDER_OUTLINED,
                [
                    fields["scan_path"],
                    fields["scan_pick"],
                ],
            ),
            _dialog_section(
                "Комментарий",
                ft.Icons.NOTES_OUTLINED,
                [fields["comment"]],
            ),
        ]

    def _collect_document_payload(fields: dict[str, ft.Control], fallback_status: str = "Активен") -> dict | None:
        title = _text_value(fields["title"])
        if not title:
            _show_message("Введите название документа.", APP_COLORS["warning"])
            return None
        issue_date = _due_date_value(fields["issue_date"])
        expiry_date = _due_date_value(fields["expiry_date"])
        if issue_date == "" or expiry_date == "":
            _show_message("Введите дату в формате 2026-06-01 или 01.06.2026.", APP_COLORS["warning"])
            return None
        document_type = fields["document_type"].value or "Другое"
        payload = {
            "title": title,
            "document_type": document_type,
            "document_number": _text_value(fields["document_number"]),
            "issue_date": issue_date or "",
            "expiry_date": expiry_date or "",
            "issuer": _text_value(fields["issuer"]),
            "comment": _text_value(fields["comment"]),
            "scan_path": _text_value(fields["scan_path"]),
            "status": _document_status(expiry_date, fallback_status),
            "icon": _document_icon(document_type),
        }
        payload["details"] = _document_details(payload)
        return payload

    def open_add_document_dialog(_=None) -> None:
        fields = _document_form_fields()

        dialog = _form_dialog(
            "Добавить личный документ",
            _document_form_controls(fields),
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: add_document_from_dialog(dialog, fields), primary=True),
            ],
            preferred_width=620,
        )
        _open_control(dialog)

    def _log_doc_action(action: str, doc: dict) -> None:
        from datetime import datetime as _dt
        doc_activity_log_state.append(
            {
                "action": action,
                "doc_id": str(doc.get("id", "")),
                "doc_title": doc.get("title", "Без названия"),
                "date": _dt.now().strftime("%d.%m.%Y %H:%M"),
            }
        )

    def _log_user_action(event_type: str, title: str, description: str = "") -> None:
        from datetime import datetime as _dt
        user_activity_log_state.insert(
            0,
            {
                "id": f"ulog-{int(time.time()*1000)}",
                "event_type": event_type,
                "title": title,
                "description": description,
                "date": _dt.now().strftime("%d.%m.%Y %H:%M"),
            },
        )
        del user_activity_log_state[200:]

    def _sync_push_document(document: dict) -> None:
        """Best-effort отправка документа в backend; обновляет id на серверный."""
        client = _user_api_ready()
        if client is None:
            return
        try:
            synced = user_sync.push_document(client, document)
        except UserAPIError:
            return
        if synced.get("id") is not None:
            document["id"] = synced["id"]

    def _sync_delete_document(document: dict) -> None:
        client = _user_api_ready()
        if client is None:
            return
        try:
            user_sync.delete_document(client, document)
        except UserAPIError:
            return

    def add_document_from_dialog(dialog, fields: dict[str, ft.Control]) -> None:
        if not require_user("Чтобы добавить документ, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        payload = _collect_document_payload(fields)
        if payload is None:
            return
        payload["id"] = f"doc-{int(time.time())}"
        _sync_push_document(payload)
        documents_state.insert(0, payload)
        _log_doc_action("created", payload)
        _log_user_action("doc_added", f"Добавлен документ «{payload.get('title', 'Документ')}»")
        _close(dialog)
        save_current_state()
        _show_message("Личный документ добавлен.")
        route_change()

    def open_edit_document_dialog(document_id) -> None:
        document = _find_item(documents_state, document_id)
        if not document:
            _show_message("Документ не найден.", APP_COLORS["warning"])
            return
        _normalize_document(document)
        fields = _document_form_fields(document)

        dialog = _form_dialog(
            "Редактировать личный документ",
            _document_form_controls(fields),
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button(
                    "Сохранить",
                    lambda _: update_document_from_dialog(dialog, document_id, fields),
                    primary=True,
                ),
            ],
            preferred_width=620,
        )
        _open_control(dialog)

    def update_document_from_dialog(dialog, document_id, fields: dict[str, ft.Control]) -> None:
        if not require_user("Чтобы изменить документ, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        payload = _collect_document_payload(fields)
        if payload is None:
            return
        document = _find_item(documents_state, document_id)
        if not document:
            _show_message("Документ не найден.", APP_COLORS["warning"])
            _close(dialog)
            return
        document.update(payload)
        _sync_push_document(document)
        _log_doc_action("updated", document)
        save_current_state()
        _close(dialog)
        _show_message("Личный документ обновлён.")
        route_change()

    def export_documents_pdf(_=None) -> None:
        if not documents_state:
            _show_message("Нет документов для экспорта.", APP_COLORS["warning"])
            return

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        export_path = exports_dir / f"documents-{timestamp}.pdf"
        lines = [
            f"Date: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            f"User: {app_user.get('name', MOCK_USER.get('name', 'Demo user'))}",
            "",
            "Documents:",
        ]
        for index, document in enumerate(documents_state[:24], start=1):
            _normalize_document(document)
            raw_number = (document.get("document_number") or "").strip()
            masked_number = "not specified"
            if raw_number:
                masked_number = f"****{raw_number[-4:]}" if len(raw_number) > 4 else "****"
            lines.extend(
                [
                    f"{index}. {document.get('title', 'Document')}",
                    f"   Type: {document.get('document_type', 'Other')}",
                    f"   Number: {masked_number}",
                    f"   Valid until: {document.get('expiry_date') or 'not specified'}",
                    f"   Status: {document.get('status', 'Active')}",
                ]
            )
        try:
            _write_simple_pdf(export_path, "Belpomoshnik documents export", lines)
        except OSError:
            _show_message("Не удалось создать PDF-экспорт.", APP_COLORS["danger"])
            return

        relative_path = _private_upload_relative_path(export_path)
        _log_user_action("doc_exported", "Создан PDF-экспорт документов", relative_path)
        save_current_state()
        _show_message(f"PDF-экспорт создан: {relative_path}")

    def toggle_document_sensitive(document_id) -> None:
        document_key = str(document_id)
        if document_key in visible_document_ids:
            visible_document_ids.remove(document_key)
        else:
            visible_document_ids.add(document_key)
        route_change()

    def update_document_privacy(value: bool) -> None:
        privacy_settings["hide_sensitive_documents"] = bool(value)
        if value:
            visible_document_ids.clear()
        save_current_state()
        route_change()

    def open_document_scan(document_id) -> None:
        document = _find_item(documents_state, document_id)
        if not document:
            _show_message("Документ не найден.", APP_COLORS["warning"])
            return
        scan_path = document.get("scan_path", "")
        if not scan_path:
            _show_message("Для документа не указан файл или скан.", APP_COLORS["warning"])
            return

        def show_scan_notice(dialog) -> None:
            _close(dialog)
            full_path = project_root / scan_path if not Path(scan_path).is_absolute() else Path(scan_path)
            if is_encrypted_path(str(full_path)) and full_path.exists():
                try:
                    raw = decrypt_bytes(full_path.read_bytes())
                    import tempfile
                    suffix = Path(full_path.stem).suffix or ".pdf"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(raw)
                        tmp_path = tmp.name
                    _show_message(f"Файл расшифрован: {tmp_path}")
                    return
                except Exception:
                    pass
            _show_message(f"Файл расположен по пути: {scan_path}")

        _confirm_action(
            "Документ содержит личные данные",
            "Файл хранится локально и зашифрован. Перед открытием убедитесь, что экран не видят посторонние.",
            "Понятно",
            show_scan_notice,
        )

    def confirm_delete_document(document_id) -> None:
        if not require_user("Чтобы удалить документ, войдите или зарегистрируйтесь."):
            return
        document = _find_item(documents_state, document_id)
        if not document:
            _show_message("Документ не найден.", APP_COLORS["warning"])
            return

        def delete(dialog) -> None:
            _sync_delete_document(document)
            _log_doc_action("deleted", document)
            _log_user_action("doc_deleted", f"Удалён документ «{document.get('title', 'Документ')}»")
            documents_state[:] = [item for item in documents_state if item.get("id") != document_id]
            save_current_state()
            _close(dialog)
            _show_message("Документ удалён.")
            route_change()

        _confirm_action(
            "Удалить документ?",
            f"Документ «{document.get('title', 'Без названия')}» будет удалён из локального списка.",
            "Удалить",
            delete,
            danger=True,
        )

    def open_add_utility_account_dialog(_=None) -> None:
        address_field = ft.TextField(label="Адрес", hint_text="ул. Независимости, 25, кв. 14", border_radius=12)
        account_number_field = ft.TextField(label="Лицевой счёт", hint_text="ЛС 00124578", border_radius=12)
        provider_field = ft.TextField(label="Организация", hint_text="РСЦ Центральный", border_radius=12)
        dialog = _form_dialog(
            "Добавить лицевой счёт",
            [address_field, account_number_field, provider_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: _add_utility_account(dialog, address_field, account_number_field, provider_field), primary=True),
            ],
            preferred_width=420,
        )
        _open_control(dialog)

    def _add_utility_account(dialog, address_field, account_number_field, provider_field) -> None:
        if not require_user("Чтобы добавить лицевой счёт, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        address = _text_value(address_field)
        if not address:
            _show_message("Укажите адрес.", APP_COLORS["warning"])
            return
        new_account = {
            "id": "util-" + str(int(time.time())),
            "address": address,
            "account_number": _text_value(account_number_field),
            "provider": _text_value(provider_field),
        }
        _sync_push_utility_account(new_account)
        utility_accounts_state.append(new_account)
        _close(dialog)
        save_current_state()
        _show_message("Лицевой счёт добавлен.")
        route_change()

    def open_edit_utility_account_dialog(account_id) -> None:
        account = _find_item(utility_accounts_state, account_id)
        if not account:
            _show_message("Счёт не найден.", APP_COLORS["warning"])
            return
        address_field = ft.TextField(label="Адрес", value=account.get("address", ""), border_radius=12)
        account_number_field = ft.TextField(label="Лицевой счёт", value=account.get("account_number", ""), border_radius=12)
        provider_field = ft.TextField(label="Организация", value=account.get("provider", ""), border_radius=12)
        dialog = _form_dialog(
            "Редактировать счёт",
            [address_field, account_number_field, provider_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: _update_utility_account(dialog, account, address_field, account_number_field, provider_field), primary=True),
            ],
            preferred_width=420,
        )
        _open_control(dialog)

    def _update_utility_account(dialog, account, address_field, account_number_field, provider_field) -> None:
        if not require_user("Чтобы изменить лицевой счёт, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        address = _text_value(address_field)
        if not address:
            _show_message("Укажите адрес.", APP_COLORS["warning"])
            return
        account["address"] = address
        account["account_number"] = _text_value(account_number_field)
        account["provider"] = _text_value(provider_field)
        _sync_push_utility_account(account)
        _close(dialog)
        save_current_state()
        _show_message("Счёт обновлён.")
        route_change()

    def confirm_delete_utility_account(account_id) -> None:
        if not require_user("Чтобы удалить лицевой счёт, войдите или зарегистрируйтесь."):
            return
        account = _find_item(utility_accounts_state, account_id)
        if not account:
            _show_message("Счёт не найден.", APP_COLORS["warning"])
            return
        def delete(dialog) -> None:
            _sync_delete_utility_account(account)
            utility_accounts_state[:] = [a for a in utility_accounts_state if a.get("id") != account_id]
            utility_payments_state[:] = [p for p in utility_payments_state if p.get("account_id") != account_id]
            save_current_state()
            _close(dialog)
            _show_message("Счёт удалён.")
            route_change()
        _confirm_action("Удалить счёт?", f"Счёт «{account.get('address', '')}» и все записи платежей будут удалены.", "Удалить", delete, danger=True)

    def open_add_utility_payment_dialog(account_id) -> None:
        period_field = ft.TextField(label="Период", hint_text="Июнь 2026", border_radius=12)
        readings_date_field = ft.TextField(label="Дата передачи показаний (дд.мм.гггг)", border_radius=12)
        payment_date_field = ft.TextField(label="Дата оплаты (дд.мм.гггг)", border_radius=12)
        amount_field = ft.TextField(label="Сумма (руб.)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)
        readings_deadline_field = ft.TextField(label="Срок передачи показаний (дд.мм.гггг)", border_radius=12)
        payment_deadline_field = ft.TextField(label="Срок оплаты (дд.мм.гггг)", border_radius=12)
        status_field = ft.Dropdown(label="Статус", value="Ожидает", border_radius=12, options=[ft.dropdown.Option("Ожидает"), ft.dropdown.Option("Оплачено"), ft.dropdown.Option("Просрочено")])
        dialog = _form_dialog(
            "Добавить запись платежа",
            [period_field, readings_deadline_field, payment_deadline_field, readings_date_field, payment_date_field, amount_field, status_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: _add_utility_payment(dialog, account_id, period_field, readings_date_field, payment_date_field, amount_field, readings_deadline_field, payment_deadline_field, status_field), primary=True),
            ],
            preferred_width=440,
        )
        _open_control(dialog)

    def _add_utility_payment(dialog, account_id, period_field, readings_date_field, payment_date_field, amount_field, readings_deadline_field, payment_deadline_field, status_field) -> None:
        if not require_user("Чтобы добавить платёж ЖКХ, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        period = _text_value(period_field)
        if not period:
            _show_message("Укажите период.", APP_COLORS["warning"])
            return
        try:
            amount = float((_text_value(amount_field) or "0").replace(",", "."))
        except ValueError:
            amount = 0.0
        new_payment = {
            "id": "upay-" + str(int(time.time())),
            "account_id": account_id,
            "period": period,
            "readings_date": _text_value(readings_date_field),
            "payment_date": _text_value(payment_date_field),
            "amount": amount,
            "status": status_field.value or "Ожидает",
            "readings_deadline": _text_value(readings_deadline_field),
            "payment_deadline": _text_value(payment_deadline_field),
            "comment": "",
        }
        _sync_push_utility_payment(new_payment)
        utility_payments_state.append(new_payment)
        _close(dialog)
        save_current_state()
        _show_message("Запись добавлена.")
        route_change()

    def open_edit_utility_payment_dialog(payment_id) -> None:
        payment = _find_item(utility_payments_state, payment_id)
        if not payment:
            _show_message("Запись не найдена.", APP_COLORS["warning"])
            return
        period_field = ft.TextField(label="Период", value=payment.get("period", ""), border_radius=12)
        readings_date_field = ft.TextField(label="Дата передачи показаний", value=payment.get("readings_date", ""), border_radius=12)
        payment_date_field = ft.TextField(label="Дата оплаты", value=payment.get("payment_date", ""), border_radius=12)
        amount_field = ft.TextField(label="Сумма", value=str(payment.get("amount", "")), keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)
        readings_deadline_field = ft.TextField(label="Срок передачи показаний", value=payment.get("readings_deadline", ""), border_radius=12)
        payment_deadline_field = ft.TextField(label="Срок оплаты", value=payment.get("payment_deadline", ""), border_radius=12)
        status_field = ft.Dropdown(label="Статус", value=payment.get("status", "Ожидает"), border_radius=12, options=[ft.dropdown.Option("Ожидает"), ft.dropdown.Option("Оплачено"), ft.dropdown.Option("Просрочено")])
        dialog = _form_dialog(
            "Редактировать запись",
            [period_field, readings_deadline_field, payment_deadline_field, readings_date_field, payment_date_field, amount_field, status_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: _update_utility_payment(dialog, payment, period_field, readings_date_field, payment_date_field, amount_field, readings_deadline_field, payment_deadline_field, status_field), primary=True),
            ],
            preferred_width=440,
        )
        _open_control(dialog)

    def _update_utility_payment(dialog, payment, period_field, readings_date_field, payment_date_field, amount_field, readings_deadline_field, payment_deadline_field, status_field) -> None:
        if not require_user("Чтобы изменить платёж ЖКХ, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        try:
            amount = float((_text_value(amount_field) or "0").replace(",", "."))
        except ValueError:
            amount = 0.0
        payment["period"] = _text_value(period_field)
        payment["readings_date"] = _text_value(readings_date_field)
        payment["payment_date"] = _text_value(payment_date_field)
        payment["amount"] = amount
        payment["readings_deadline"] = _text_value(readings_deadline_field)
        payment["payment_deadline"] = _text_value(payment_deadline_field)
        payment["status"] = status_field.value or "Ожидает"
        _sync_push_utility_payment(payment)
        _close(dialog)
        save_current_state()
        _show_message("Запись обновлена.")
        route_change()

    def confirm_delete_utility_payment(payment_id) -> None:
        if not require_user("Чтобы удалить платёж ЖКХ, войдите или зарегистрируйтесь."):
            return
        payment = _find_item(utility_payments_state, payment_id)
        if not payment:
            _show_message("Запись не найдена.", APP_COLORS["warning"])
            return
        def delete(dialog) -> None:
            _sync_delete_utility_payment(payment)
            utility_payments_state[:] = [p for p in utility_payments_state if p.get("id") != payment_id]
            save_current_state()
            _close(dialog)
            _show_message("Запись удалена.")
            route_change()
        _confirm_action("Удалить запись?", f"Запись за «{payment.get('period', '')}» будет удалена.", "Удалить", delete, danger=True)

    def open_add_tax_obligation_dialog(_=None) -> None:
        title_field = ft.TextField(label="Обязательство", hint_text="Декларация о доходах", border_radius=12)
        user_type_field = ft.Dropdown(label="Тип плательщика", value="individual", border_radius=12, options=[ft.dropdown.Option("individual", "Физлицо"), ft.dropdown.Option("ip", "ИП")])
        deadline_field = ft.TextField(label="Срок (дд.мм.гггг или гггг-мм-дд)", border_radius=12)
        amount_field = ft.TextField(label="Сумма (руб.)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)
        period_field = ft.TextField(label="Период", hint_text="2026 год", border_radius=12)
        status_field = ft.Dropdown(label="Статус", value="Предстоит", border_radius=12, options=[ft.dropdown.Option("Предстоит"), ft.dropdown.Option("Оплачено"), ft.dropdown.Option("Просрочено")])
        comment_field = ft.TextField(label="Комментарий", multiline=True, border_radius=12)
        dialog = _form_dialog(
            "Добавить налоговое обязательство",
            [title_field, user_type_field, period_field, deadline_field, amount_field, status_field, comment_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: _add_tax_obligation(dialog, title_field, user_type_field, deadline_field, amount_field, period_field, status_field, comment_field), primary=True),
            ],
            preferred_width=460,
        )
        _open_control(dialog)

    def _add_tax_obligation(dialog, title_field, user_type_field, deadline_field, amount_field, period_field, status_field, comment_field) -> None:
        if not require_user("Чтобы добавить налоговое обязательство, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        title = _text_value(title_field)
        if not title:
            _show_message("Укажите название обязательства.", APP_COLORS["warning"])
            return
        try:
            amount = float((_text_value(amount_field) or "0").replace(",", "."))
        except ValueError:
            amount = 0.0
        new_tax = {
            "id": "tax-" + str(int(time.time())),
            "user_type": user_type_field.value or "individual",
            "title": title,
            "deadline": _text_value(deadline_field),
            "amount": amount,
            "receipt_path": "",
            "status": status_field.value or "Предстоит",
            "period": _text_value(period_field),
            "comment": _text_value(comment_field),
        }
        _sync_push_tax(new_tax)
        tax_obligations_state.append(new_tax)
        _close(dialog)
        save_current_state()
        _show_message("Обязательство добавлено.")
        route_change()

    def open_edit_tax_obligation_dialog(obligation_id) -> None:
        obligation = _find_item(tax_obligations_state, obligation_id)
        if not obligation:
            _show_message("Обязательство не найдено.", APP_COLORS["warning"])
            return
        title_field = ft.TextField(label="Обязательство", value=obligation.get("title", ""), border_radius=12)
        user_type_field = ft.Dropdown(label="Тип плательщика", value=obligation.get("user_type", "individual"), border_radius=12, options=[ft.dropdown.Option("individual", "Физлицо"), ft.dropdown.Option("ip", "ИП")])
        deadline_field = ft.TextField(label="Срок", value=obligation.get("deadline", ""), border_radius=12)
        amount_field = ft.TextField(label="Сумма", value=str(obligation.get("amount", "")), keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)
        period_field = ft.TextField(label="Период", value=obligation.get("period", ""), border_radius=12)
        status_field = ft.Dropdown(label="Статус", value=obligation.get("status", "Предстоит"), border_radius=12, options=[ft.dropdown.Option("Предстоит"), ft.dropdown.Option("Оплачено"), ft.dropdown.Option("Просрочено")])
        comment_field = ft.TextField(label="Комментарий", value=obligation.get("comment", ""), multiline=True, border_radius=12)
        dialog = _form_dialog(
            "Редактировать обязательство",
            [title_field, user_type_field, period_field, deadline_field, amount_field, status_field, comment_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: _update_tax_obligation(dialog, obligation, title_field, user_type_field, deadline_field, amount_field, period_field, status_field, comment_field), primary=True),
            ],
            preferred_width=460,
        )
        _open_control(dialog)

    def _update_tax_obligation(dialog, obligation, title_field, user_type_field, deadline_field, amount_field, period_field, status_field, comment_field) -> None:
        if not require_user("Чтобы изменить налоговое обязательство, войдите или зарегистрируйтесь."):
            try:
                _close(dialog)
            except Exception:
                pass
            return
        title = _text_value(title_field)
        if not title:
            _show_message("Укажите название.", APP_COLORS["warning"])
            return
        try:
            amount = float((_text_value(amount_field) or "0").replace(",", "."))
        except ValueError:
            amount = 0.0
        obligation["title"] = title
        obligation["user_type"] = user_type_field.value or "individual"
        obligation["deadline"] = _text_value(deadline_field)
        obligation["amount"] = amount
        obligation["period"] = _text_value(period_field)
        obligation["status"] = status_field.value or "Предстоит"
        obligation["comment"] = _text_value(comment_field)
        _sync_push_tax(obligation)
        _close(dialog)
        save_current_state()
        _show_message("Обязательство обновлено.")
        route_change()

    def confirm_delete_tax_obligation(obligation_id) -> None:
        if not require_user("Чтобы удалить обязательство, войдите или зарегистрируйтесь."):
            return
        obligation = _find_item(tax_obligations_state, obligation_id)
        if not obligation:
            _show_message("Обязательство не найдено.", APP_COLORS["warning"])
            return
        def delete(dialog) -> None:
            _sync_delete_tax(obligation)
            tax_obligations_state[:] = [o for o in tax_obligations_state if o.get("id") != obligation_id]
            save_current_state()
            _close(dialog)
            _show_message("Обязательство удалено.")
            route_change()
        _confirm_action("Удалить обязательство?", f"«{obligation.get('title', '')}» будет удалено.", "Удалить", delete, danger=True)

    def mark_tax_obligation_paid(obligation_id) -> None:
        if not require_user("Чтобы отметить оплату, войдите или зарегистрируйтесь."):
            return
        obligation = _find_item(tax_obligations_state, obligation_id)
        if not obligation:
            return
        obligation["status"] = "Оплачено"
        _sync_push_tax(obligation)
        save_current_state()
        _show_message("Отмечено как оплаченное.")
        route_change()

    def open_add_situation_dialog(_=None) -> None:
        title = ft.TextField(label="Название ситуации", hint_text="Например: Замена паспорта", border_radius=12)
        status = ft.Dropdown(
            label="Статус",
            value="Запланировано",
            border_radius=12,
            options=[
                ft.dropdown.Option("Запланировано"),
                ft.dropdown.Option("В процессе"),
                ft.dropdown.Option("Завершено"),
            ],
        )

        dialog = _form_dialog(
            "Добавить ситуацию",
            [title, status],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: add_situation_from_dialog(dialog, title, status), primary=True),
            ],
        )
        _open_control(dialog)

    def add_situation_from_dialog(dialog, title_field, status_field) -> None:
        title = _text_value(title_field)
        if not title:
            _show_message("Введите название ситуации.", APP_COLORS["warning"])
            return
        situation_id = f"situation-{int(time.time())}"
        situations_state.insert(
            0,
            {
                "id": situation_id,
                "title": title,
                "status": status_field.value or "Запланировано",
                "progress": 0,
            },
        )
        current_situation["id"] = situation_id
        _close(dialog)
        save_current_state()
        _show_message("Ситуация добавлена.")
        route_change()

    def open_edit_situation_dialog(situation_id) -> None:
        situation = _find_item(situations_state, situation_id)
        if not situation:
            _show_message("Ситуация не найдена.", APP_COLORS["warning"])
            return
        title = ft.TextField(
            label="Название ситуации",
            value=situation.get("title", ""),
            border_radius=12,
        )
        status = ft.Dropdown(
            label="Статус",
            value=situation.get("status", "Запланировано"),
            border_radius=12,
            options=[
                ft.dropdown.Option("Запланировано"),
                ft.dropdown.Option("В процессе"),
                ft.dropdown.Option("Завершено"),
            ],
        )

        dialog = _form_dialog(
            "Редактировать ситуацию",
            [title, status],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button(
                    "Сохранить",
                    lambda _: update_situation_from_dialog(dialog, situation_id, title, status),
                    primary=True,
                ),
            ],
        )
        _open_control(dialog)

    def update_situation_from_dialog(dialog, situation_id, title_field, status_field) -> None:
        title = _text_value(title_field)
        if not title:
            _show_message("Введите название ситуации.", APP_COLORS["warning"])
            return
        situation = _find_item(situations_state, situation_id)
        if not situation:
            _show_message("Ситуация не найдена.", APP_COLORS["warning"])
            _close(dialog)
            return
        situation["title"] = title
        situation["status"] = status_field.value or "Запланировано"
        recalculate_situation_progress(situation_id)
        save_current_state()
        _close(dialog)
        _show_message("Ситуация обновлена.")
        route_change()

    def confirm_delete_situation(situation_id) -> None:
        situation = _find_item(situations_state, situation_id)
        if not situation:
            _show_message("Ситуация не найдена.", APP_COLORS["warning"])
            return

        def delete(dialog) -> None:
            situations_state[:] = [item for item in situations_state if item.get("id") != situation_id]
            situation_tasks_state[:] = [
                task for task in situation_tasks_state if task.get("situation_id", "childbirth") != situation_id
            ]
            if current_situation["id"] == situation_id:
                current_situation["id"] = situations_state[0]["id"] if situations_state else "childbirth"
            save_current_state()
            _close(dialog)
            _show_message("Ситуация удалена.")
            page.run_task(page.push_route, "/situations")

        _confirm_action(
            "Удалить ситуацию?",
            f"Ситуация «{situation.get('title', 'Без названия')}» и её локальные задачи будут удалены.",
            "Удалить",
            delete,
            danger=True,
        )

    def open_add_task_dialog(_=None) -> None:
        title = ft.TextField(label="Название задачи", hint_text="Например: Позвонить в ЗАГС", border_radius=12)
        deadline = ft.TextField(label="Срок", hint_text="Например: до пятницы", border_radius=12)
        due_date = ft.TextField(
            label="Дата срока",
            hint_text="Например: 2026-06-01 или 01.06.2026",
            border_radius=12,
        )
        documents = ft.TextField(
            label="Документы для задачи",
            hint_text="Паспорт; Заявление (необязательно)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=12,
            helper="Разделяйте документы новой строкой, точкой с запятой или запятой.",
            helper_max_lines=2,
        )

        dialog = _form_dialog(
            "Добавить задачу",
            [title, deadline, due_date, documents],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button(
                    "Добавить",
                    lambda _: add_task_from_dialog(dialog, title, deadline, due_date, documents),
                    primary=True,
                ),
            ],
            preferred_width=460,
        )
        _open_control(dialog)

    def add_task_from_dialog(dialog, title_field, deadline_field, due_date_field, documents_field) -> None:
        title = _text_value(title_field)
        if not title:
            _show_message("Введите название задачи.", APP_COLORS["warning"])
            return
        due_date = _due_date_value(due_date_field)
        if due_date == "":
            _show_message("Введите дату в формате 2026-06-01 или 01.06.2026.", APP_COLORS["warning"])
            return
        new_task = {
            "id": f"task-{int(time.time() * 1000)}",
            "situation_id": current_situation["id"],
            "title": title,
            "completed": False,
            "deadline": _text_value(deadline_field) or "Без срока",
            "documents": _parse_task_documents(_text_value(documents_field)),
        }
        if due_date:
            new_task["due_date"] = due_date
        situation_tasks_state.append(new_task)
        _close(dialog)
        recalculate_situation_progress(current_situation["id"])
        save_current_state()
        _show_message("Задача добавлена.")
        route_change()

    def open_edit_task_dialog(task_id) -> None:
        task = _find_item(situation_tasks_state, task_id)
        if not task:
            _show_message("Задача не найдена.", APP_COLORS["warning"])
            return
        title = ft.TextField(
            label="Название задачи",
            value=task.get("title", ""),
            border_radius=12,
        )
        deadline = ft.TextField(
            label="Срок",
            value=task.get("deadline", ""),
            border_radius=12,
        )
        due_date = ft.TextField(
            label="Дата срока",
            value=task.get("due_date", ""),
            hint_text="Например: 2026-06-01 или 01.06.2026",
            border_radius=12,
        )
        documents = ft.TextField(
            label="Документы для задачи",
            value=_format_task_documents(task.get("documents", [])),
            hint_text="Паспорт; Заявление (необязательно)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=12,
            helper="Пометка «необязательно» сделает документ дополнительным.",
            helper_max_lines=2,
        )
        completed = ft.Checkbox(
            label="Задача выполнена",
            value=bool(task.get("completed")),
            active_color=APP_COLORS["primary"],
        )

        dialog = _form_dialog(
            "Редактировать задачу",
            [title, deadline, due_date, documents, completed],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button(
                    "Сохранить",
                    lambda _: update_task_from_dialog(
                        dialog,
                        task_id,
                        title,
                        deadline,
                        due_date,
                        documents,
                        completed,
                    ),
                    primary=True,
                ),
            ],
            preferred_width=460,
        )
        _open_control(dialog)

    def update_task_from_dialog(
        dialog,
        task_id,
        title_field,
        deadline_field,
        due_date_field,
        documents_field,
        completed_field,
    ) -> None:
        title = _text_value(title_field)
        if not title:
            _show_message("Введите название задачи.", APP_COLORS["warning"])
            return
        due_date = _due_date_value(due_date_field)
        if due_date == "":
            _show_message("Введите дату в формате 2026-06-01 или 01.06.2026.", APP_COLORS["warning"])
            return
        task = _find_item(situation_tasks_state, task_id)
        if not task:
            _show_message("Задача не найдена.", APP_COLORS["warning"])
            _close(dialog)
            return
        task["title"] = title
        task["deadline"] = _text_value(deadline_field) or "Без срока"
        task["documents"] = _parse_task_documents(_text_value(documents_field))
        if due_date:
            task["due_date"] = due_date
        else:
            task.pop("due_date", None)
        if bool(completed_field.value) and _unmet_dependencies(task):
            _show_message(_dependency_message(task), APP_COLORS["warning"])
            return
        task["completed"] = bool(completed_field.value)
        recalculate_situation_progress(task.get("situation_id", current_situation["id"]))
        save_current_state()
        _close(dialog)
        _show_message("Задача обновлена.")
        route_change()

    def confirm_delete_task(task_id) -> None:
        task = _find_item(situation_tasks_state, task_id)
        if not task:
            _show_message("Задача не найдена.", APP_COLORS["warning"])
            return

        def delete(dialog) -> None:
            situation_id = task.get("situation_id", current_situation["id"])
            situation_tasks_state[:] = [item for item in situation_tasks_state if item.get("id") != task_id]
            recalculate_situation_progress(situation_id)
            save_current_state()
            _close(dialog)
            _show_message("Задача удалена.")
            route_change()

        _confirm_action(
            "Удалить задачу?",
            f"Задача «{task.get('title', 'Без названия')}» будет удалена из этого плана.",
            "Удалить",
            delete,
            danger=True,
        )

    def toggle_situation_task(task_id, value: bool) -> None:
        if not require_user("Чтобы отмечать задачи, войдите или зарегистрируйтесь."):
            return
        for task in situation_tasks_state:
            if task["id"] == task_id:
                if value and _unmet_dependencies(task):
                    _show_message(_dependency_message(task), APP_COLORS["warning"])
                    route_change()
                    return
                task["completed"] = value
                recalculate_situation_progress(task.get("situation_id", current_situation["id"]))
                if value:
                    _log_user_action("task_completed", f"Выполнена задача «{task.get('title', 'Задача')}»")
                break
        save_current_state()
        _show_message("Задача обновлена.")
        route_change()

    def save_situation_changes(_=None) -> None:
        recalculate_situation_progress(current_situation["id"])
        save_current_state()
        _show_message("Изменения ситуации сохранены.")
        route_change()

    def set_situation_task_filter(value: str) -> None:
        situation_task_filter["value"] = value or "all"
        route_change()

    def add_situation_note(note_data: dict) -> None:
        from datetime import date as _date
        sid = current_situation["id"]
        if sid not in user_notes_state:
            user_notes_state[sid] = []
        note_data["date"] = _date.today().strftime("%d.%m.%Y")
        user_notes_state[sid].append(note_data)
        # Generate reminder notification if date set
        reminder = (note_data.get("reminder_date") or "").strip()
        if reminder:
            notifications_state.append({
                "id": f"note-reminder-{len(notifications_state)}",
                "title": "Напоминание по ситуации",
                "desc": note_data.get("text", "")[:80],
                "type": "note_reminder",
                "is_read": False,
                "date": reminder,
            })
        route_change()

    def mark_all_notifications_read(_=None) -> None:
        if not require_user("Чтобы пользоваться уведомлениями, войдите или зарегистрируйтесь."):
            return
        for note in notifications_state:
            note["is_read"] = True
        save_current_state()
        _show_message("Все уведомления прочитаны.")
        route_change()

    def mark_notification_read(note_id: int) -> None:
        if not require_user("Чтобы пользоваться уведомлениями, войдите или зарегистрируйтесь."):
            return
        for note in notifications_state:
            if note["id"] == note_id:
                note["is_read"] = True
                break
        save_current_state()
        route_change()

    def open_email_preview(note: dict) -> None:
        """I1 — Открыть предпросмотр email-уведомления."""
        soon_titles = [
            doc.get("title", "Документ")
            for doc in user_documents_state
            if doc.get("expiry_date")
        ][:3]
        recipient = auth_state.get("email") or app_user.get("email", "user@example.com")
        email_preview_data.update(
            build_doc_expiry_email_data(recipient=recipient, doc_titles=soon_titles or ["Документ"])
        )
        page.run_task(page.push_route, "/email-preview")

    def save_law(law_id: str) -> None:
        saved_law_ids.add(law_id)
        save_current_state()
        _show_message("Закон-апдейт сохранён.")

    def open_law_source(law_id: str) -> None:
        law = next((item for item in law_updates_state if item["id"] == law_id), None)
        source_url = (law or {}).get("source_url")
        if source_url:
            page.launch_url(source_url)
        else:
            _show_message("Для этого обновления пока не указан официальный источник.", APP_COLORS["warning"])

    def update_profile_setting(key: str, value) -> None:
        app_settings[key] = value
        if key == "dark_theme":
            theme_mode_state["value"] = "dark" if value else "light"
            apply_page_theme()
            session = getattr(page, "session", None)
            if session is not None:
                try:
                    session.set("theme_mode", theme_mode_state["value"])
                except Exception:
                    pass
        if key in ("large_text", "high_contrast"):
            apply_page_theme()
        if key == "learning_mode":
            learning_state["enabled"] = value
            app_user["learning_mode"] = value
        save_current_state()
        route_change()

    def toggle_theme(_=None) -> None:
        update_profile_setting("dark_theme", theme_mode_state["value"] != "dark")

    def save_profile(refs: dict[str, ft.TextField]) -> None:
        if not require_user("Чтобы сохранить профиль, войдите или зарегистрируйтесь."):
            return
        name = _text_value(refs["name"])
        email = _text_value(refs["email"]).lower()
        if not name:
            _show_message("Введите имя.", APP_COLORS["warning"])
            return
        if "@" not in email:
            _show_message("Введите корректный email.", APP_COLORS["warning"])
            return
        old_email = auth_state.get("email")
        if email != old_email and email in users:
            _show_message("Этот email уже используется.", APP_COLORS["warning"])
            return
        app_user["name"] = name
        app_user["first_name"] = name.split()[0]
        app_user["email"] = email
        if "birth_date" in refs:
            app_user["birth_date"] = _text_value(refs["birth_date"])
        app_user["region"] = _text_value(refs["region"]) or app_user["region"]
        app_user["city"] = _text_value(refs["city"]) or app_user["city"]
        if "district" in refs:
            app_user["district"] = _text_value(refs["district"])
        if "address" in refs:
            app_user["address"] = _text_value(refs["address"])
        if old_email in users:
            account = users.pop(old_email)
            account["profile"] = app_user.copy()
            users[email] = account
            auth_state["email"] = email
        _log_user_action("profile_updated", "Обновлён профиль", f"Имя: {name}, email: {email}")
        save_current_state()
        _show_message("Профиль сохранён.")
        route_change()

    def set_employment_status(value: str) -> None:
        allowed = {"employee", "entrepreneur", "student", "retired", "unemployed"}
        if value not in allowed:
            return
        if app_user.get("employment_status") == value:
            return
        app_user["employment_status"] = value
        current_email = auth_state.get("email")
        if current_email in users:
            users[current_email]["profile"] = app_user.copy()
        save_current_state()
        _show_message("Статус занятости обновлён.")
        route_change()

    def set_household_flag(key: str, value: bool) -> None:
        if key not in {"has_children", "has_car", "is_homeowner", "is_tenant"}:
            return
        app_user[key] = bool(value)
        current_email = auth_state.get("email")
        if current_email in users:
            users[current_email]["profile"] = app_user.copy()
        save_current_state()
        route_change()

    def open_add_interest_dialog(_=None) -> None:
        interest = ft.TextField(label="Интерес", hint_text="Например: Переезд", border_radius=12)
        dialog = _form_dialog(
            "Добавить интерес",
            [interest],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: add_interest_from_dialog(dialog, interest), primary=True),
            ],
            preferred_width=360,
        )
        _open_control(dialog)

    def add_interest_from_dialog(dialog, interest_field) -> None:
        interest = _text_value(interest_field)
        if not interest:
            _show_message("Введите интерес.", APP_COLORS["warning"])
            return
        if interest not in app_user["interests"]:
            app_user["interests"].append(interest)
        _close(dialog)
        save_current_state()
        _show_message("Интерес добавлен.")
        route_change()

    def toggle_interest_tag(tag_key: str) -> None:
        tags: list = app_user.setdefault("interest_tags", [])
        if tag_key in tags:
            tags.remove(tag_key)
        else:
            tags.append(tag_key)
        current_email = auth_state.get("email")
        if current_email in users:
            users[current_email]["profile"] = app_user.copy()
        save_current_state()
        route_change()

    def _persist_profile() -> None:
        current_email = auth_state.get("email")
        if current_email in users:
            users[current_email]["profile"] = app_user.copy()
        save_current_state()

    def _sync_primary_from_locations() -> None:
        locs = app_user.get("locations", [])
        primary = next((l for l in locs if l.get("is_primary")), locs[0] if locs else None)
        if primary:
            app_user["region"] = primary.get("region", "")
            app_user["district"] = primary.get("district", "")
            app_user["city"] = primary.get("city", "")
            app_user["address"] = primary.get("address", "")

    def add_location(loc: dict) -> None:
        locs: list = app_user.setdefault("locations", [])
        new_loc = {
            "id": f"loc-{int(time.time() * 1000)}",
            "label": loc.get("label", "Адрес"),
            "region": loc.get("region", ""),
            "district": loc.get("district", ""),
            "city": loc.get("city", ""),
            "address": loc.get("address", ""),
            "is_primary": not locs,  # first one becomes primary
        }
        locs.append(new_loc)
        _sync_primary_from_locations()
        _persist_profile()
        _show_message("Адрес добавлен.")
        route_change()

    def delete_location(loc_id: str) -> None:
        locs: list = app_user.get("locations", [])
        was_primary = any(l.get("id") == loc_id and l.get("is_primary") for l in locs)
        app_user["locations"] = [l for l in locs if l.get("id") != loc_id]
        if was_primary and app_user["locations"]:
            app_user["locations"][0]["is_primary"] = True
        _sync_primary_from_locations()
        _persist_profile()
        _show_message("Адрес удалён.")
        route_change()

    def set_primary_location(loc_id: str) -> None:
        for l in app_user.get("locations", []):
            l["is_primary"] = (l.get("id") == loc_id)
        _sync_primary_from_locations()
        _persist_profile()
        _show_message("Основной адрес обновлён.")
        route_change()

    def open_add_location_dialog(_=None) -> None:
        from components.location_picker import build_location_picker
        picker_control, get_loc = build_location_picker(
            initial={"label": "Фактический адрес"},
            show_label_select=True,
            compact=False,
        )

        def _submit(dialog) -> None:
            loc = get_loc()
            if not loc.get("region"):
                _show_message("Выберите регион.", APP_COLORS["warning"])
                return
            _close(dialog)
            add_location(loc)

        dialog = _form_dialog(
            "Добавить местонахождение",
            [picker_control],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: _submit(dialog), primary=True),
            ],
            preferred_width=440,
        )
        _open_control(dialog)

    def admin_select_role(role_id: str) -> None:
        available_role_ids = {role.get("id") for role in admin_roles_state}
        if role_id not in available_role_ids:
            _show_message("Роль не найдена.", APP_COLORS["warning"])
            return
        current_admin_role["value"] = role_id
        admin_state["current_role"] = role_id
        admin_state["roles"] = admin_roles_state
        admin_state["admin_users"] = admin_users_state
        admin_state["audit_logs"] = admin_audit_logs_state
        save_current_state()
        route_change()

    def on_admin_tab_change(tab_key: str) -> None:
        admin_state["current_tab"] = tab_key
        route_change()

    def on_admin_update_user_role(user_id: str, role_id: str) -> None:
        available_role_ids = {r.get("id") for r in admin_roles_state}
        if role_id not in available_role_ids:
            _show_message("Роль не найдена.", APP_COLORS["warning"])
            return
        for user in admin_users_state:
            if user.get("id") == user_id:
                user["role_id"] = role_id
                break
        admin_state["admin_users"] = admin_users_state
        save_current_state()
        route_change()

    def on_admin_toggle_user_status(user_id: str) -> None:
        for user in admin_users_state:
            if user.get("id") == user_id:
                user["active"] = not user.get("active", True)
                break
        admin_state["admin_users"] = admin_users_state
        save_current_state()
        route_change()

    def on_admin_create_admin_user(name: str, email: str, role_id: str) -> None:
        import re as _re
        name = (name or "").strip()
        email = (email or "").strip()
        if not name or not email:
            _show_message("Введите имя и e-mail.", APP_COLORS["warning"])
            return
        if not _re.match(r"[^@]+@[^@]+\.[^@]+", email):
            _show_message("Некорректный e-mail.", APP_COLORS["warning"])
            return
        if any(u.get("email", "").lower() == email.lower() for u in admin_users_state):
            _show_message("Пользователь с таким e-mail уже существует.", APP_COLORS["warning"])
            return
        new_user = {
            "id": _slugify(email, "user"),
            "name": name,
            "email": email,
            "role_id": role_id or "content_editor",
            "active": True,
        }
        admin_users_state.append(new_user)
        admin_state["admin_users"] = admin_users_state
        save_current_state()
        route_change()

    def on_admin_add_category(cat_id: str, cat_name: str) -> None:
        cat_id = (cat_id or "").strip()
        cat_name = (cat_name or "").strip()
        if not cat_id or not cat_name:
            _show_message("Введите ID и название категории.", APP_COLORS["warning"])
            return
        cats = admin_state.get("categories", [])
        if any(c.get("id") == cat_id for c in cats):
            _show_message("Категория с таким ID уже существует.", APP_COLORS["warning"])
            return
        cats.append({"id": cat_id, "name": cat_name})
        admin_state["categories"] = cats
        route_change()

    def on_admin_delete_category(cat_id: str) -> None:
        cats = admin_state.get("categories", [])
        admin_state["categories"] = [c for c in cats if c.get("id") != cat_id]
        route_change()

    def on_admin_toggle_notification_rule(rule_id: str, value: bool) -> None:
        rules = admin_state.get("notification_rules", [])
        for rule in rules:
            if rule.get("id") == rule_id:
                rule["enabled"] = value
                break
        admin_state["notification_rules"] = rules
        route_change()

    def on_admin_edit_rule_days(rule_id: str, days_str: str) -> None:
        try:
            days = int(days_str)
            if days < 1:
                raise ValueError
        except (ValueError, TypeError):
            _show_message("Введите корректное количество дней (≥ 1).", APP_COLORS["warning"])
            return
        rules = admin_state.get("notification_rules", [])
        for rule in rules:
            if rule.get("id") == rule_id:
                rule["threshold_days"] = days
                break
        admin_state["notification_rules"] = rules
        route_change()

    def _source_type_name(source_type: str) -> str:
        return {
            "law": "Право",
            "government_portal": "Госпортал",
            "ministry": "Министерство",
            "court": "Суд",
            "tax": "Налоги",
            "registry": "Реестр / ЗАГС",
            "local_authority": "Исполком",
            "other": "Другое",
        }.get(source_type, source_type or "Другое")

    def _is_allowed_official_source(url: str) -> bool:
        normalized = (url or "").strip().lower()
        if not normalized.startswith(("https://", "http://")):
            return False
        official_markers = (
            "pravo.by",
            ".gov.by",
            "portal.gov.by",
            "nalog.gov.by",
            "mintrud.gov.by",
            "minjust.gov.by",
            "court.gov.by",
        )
        return any(marker in normalized for marker in official_markers)

    def _normalize_official_source(source: dict) -> dict:
        source.setdefault("id", _slugify(source.get("title", ""), "source"))
        source.setdefault("title", "Официальный источник")
        source.setdefault("url", "https://pravo.by/")
        source.setdefault("source_type", "other")
        source.setdefault("description", "Описание будет уточнено редактором.")
        source.setdefault("last_checked_at", "")
        source.setdefault("status", "active" if source.get("last_checked_at") else "requires_check")
        return source

    def _normalized_published_laws() -> list[dict]:
        for law in law_updates_state:
            _normalize_law_update(law)
        return [item for item in law_updates_state if item.get("status", "published") == "published"]

    def _collect_user_tags() -> set[str]:
        tags: set[str] = set(app_user.get("interest_tags") or [])
        employment = app_user.get("employment_status", "")
        if employment == "ip":
            tags.add("ip")
        if employment == "student":
            tags.add("student")
        if employment == "retired":
            tags.add("retired")
        if app_user.get("has_children"):
            tags.update({"has_children", "family"})
        if app_user.get("is_homeowner") or app_user.get("owns_property"):
            tags.update({"housing", "housing_owner", "utility"})
        if app_user.get("is_tenant"):
            tags.update({"housing", "utility"})
        if app_user.get("has_car"):
            tags.add("auto")
        return tags

    def _important_laws_for_user(published_laws: list[dict]) -> list[dict]:
        interests = {str(item).lower() for item in app_user.get("interests", [])}
        active_situation_titles = {
            str(item.get("title", "")).lower()
            for item in situations_state
            if item.get("status") != "Завершена"
        }
        favorite_titles = {
            str(template.get("title", "")).lower()
            for template in SCENARIO_TEMPLATES
            if template.get("id") in favorite_scenario_ids
        }
        relevant_categories: set[str] = set()
        if any("дет" in item or "сем" in item for item in interests):
            relevant_categories.add("family")
        if any("жиль" in item or "собствен" in item or "жкх" in item for item in interests):
            relevant_categories.add("home")
        if any("авто" in item for item in interests):
            relevant_categories.update({"auto", "docs"})
        if any("ип" in item or "бизнес" in item or "самозан" in item for item in interests):
            relevant_categories.update({"business", "taxes"})
        if any("работ" in item for item in interests):
            relevant_categories.add("work")

        user_profile_tags: set[str] = set(app_user.get("interest_tags") or [])
        employment = app_user.get("employment_status", "")
        if employment == "ip":
            user_profile_tags.add("ip")
        if app_user.get("has_children"):
            user_profile_tags.update({"has_children", "family"})
        if app_user.get("owns_property"):
            user_profile_tags.update({"housing_owner", "utility"})

        important: list[dict] = []
        for law in published_laws:
            related_titles = {str(item).lower() for item in law.get("related_scenarios", [])}
            target_text = str(law.get("target", "")).lower()
            category_match = law.get("category") in relevant_categories
            related_match = bool(related_titles & (active_situation_titles | favorite_titles))
            interest_match = any(interest and interest in target_text for interest in interests)
            high_priority = law.get("priority") == "high"
            tag_match = bool(user_profile_tags & set(law.get("profile_tags") or []))
            if category_match or related_match or interest_match or high_priority or tag_match:
                important.append(law)

        important.sort(key=lambda law: (0 if law.get("priority") == "high" else 1, law.get("date", ""), law.get("title", "")))
        return important[:3]

    def _add_admin_audit(action: str, role_id: str | None = None, event_type: str = "") -> None:
        role_value = role_id or current_admin_role["value"]
        if not event_type:
            action_lower = action.lower()
            if action_lower.startswith("создан") or action_lower.startswith("добавлен"):
                event_type = "create"
            elif action_lower.startswith("отредактирован") or action_lower.startswith("статус") or action_lower.startswith("изменён"):
                event_type = "update"
            elif action_lower.startswith("удалён"):
                event_type = "delete"
            else:
                event_type = "other"
        admin_audit_logs_state.insert(
            0,
            {
                "id": f"audit-{int(time.time())}",
                "actor": "Локальный редактор",
                "role_id": role_value,
                "action": action,
                "event_type": event_type,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": "demo",
            },
        )
        del admin_audit_logs_state[20:]
        admin_state["audit_logs"] = admin_audit_logs_state

    def admin_create_law_update(
        title: str,
        category: str,
        target: str,
        date_value: str,
        short: str,
        what_to_do: str,
        related_scenarios,
        related_problems,
        source_url: str,
        priority: str,
    ) -> None:
        normalized_title = (title or "").strip()
        if not normalized_title:
            _show_message("Введите заголовок закон-апдейта.", APP_COLORS["warning"])
            return
        law_id = _slugify(normalized_title, "law-update")
        law_updates_state.insert(
            0,
            {
                "id": law_id,
                "title": normalized_title,
                "category": category or "family",
                "category_name": _law_category_name(category or "family"),
                "date": (date_value or "Требует уточнения").strip(),
                "target": (target or "Требует уточнения").strip(),
                "short": (short or "Описание будет уточнено редактором.").strip(),
                "what_to_do": (what_to_do or "Проверьте официальный источник и уточните актуальный порядок действий.").strip(),
                "related_scenarios": _split_related_scenarios(related_scenarios),
                "source_url": (source_url or "https://pravo.by/").strip(),
                "status": "draft",
                "priority": priority or "medium",
                "processing_status": "new",
                "last_checked": "",
                "related_problems": _split_law_problem_ids(related_problems),
                "profile_tags": [],
            },
        )
        law_detail_state[law_id] = {
            "summary": (short or "Описание будет уточнено редактором.").strip(),
            "details": [
                (what_to_do or "Проверьте актуальность информации по официальному источнику.").strip(),
                "Перед публикацией редактор должен уточнить дату вступления, аудиторию и официальный источник.",
            ],
        }
        admin_state["law_updates"] = law_updates_state
        _add_admin_audit(f"Создан закон-апдейт «{normalized_title}»", "content_editor")
        save_current_state()
        _show_message("Закон-апдейт добавлен в черновики.")
        route_change()

    def admin_set_law_update_status(law_id: str, status_value: str) -> None:
        law = _find_item(law_updates_state, law_id)
        if not law:
            _show_message("Закон-апдейт не найден.", APP_COLORS["warning"])
            return
        law["status"] = status_value
        admin_state["law_updates"] = law_updates_state
        _add_admin_audit(f"Статус закон-апдейта «{law.get('title', law_id)}» изменён на {status_value}", "content_editor")
        save_current_state()
        _show_message("Статус закон-апдейта обновлён.")
        route_change()

    def admin_delete_law_update(law_id: str) -> None:
        law = _find_item(law_updates_state, law_id)
        if not law:
            _show_message("Закон-апдейт не найден.", APP_COLORS["warning"])
            return

        def delete(dialog) -> None:
            law_updates_state[:] = [item for item in law_updates_state if item.get("id") != law_id]
            law_detail_state.pop(law_id, None)
            saved_law_ids.discard(law_id)
            if current_law["id"] == law_id:
                current_law["id"] = law_updates_state[0]["id"] if law_updates_state else "law1"
            admin_state["law_updates"] = law_updates_state
            _add_admin_audit(f"Удалён закон-апдейт «{law.get('title', law_id)}»", "content_editor")
            save_current_state()
            _close(dialog)
            _show_message("Закон-апдейт удалён.")
            route_change()

        _confirm_action(
            "Удалить закон-апдейт?",
            f"Запись «{law.get('title', 'Без названия')}» будет удалена.",
            "Удалить",
            delete,
            danger=True,
        )

    def admin_open_edit_law_update_dialog(law_id: str) -> None:
        law = _find_item(law_updates_state, law_id)
        if not law:
            _show_message("Закон-апдейт не найден.", APP_COLORS["warning"])
            return
        _normalize_law_update(law)
        detail = law_detail_state.get(law_id, {})
        title_field = ft.TextField(label="Заголовок", value=law.get("title", ""), border_radius=12)
        category_dropdown = ft.Dropdown(
            label="Категория",
            value=law.get("category", "family"),
            options=[
                ft.dropdown.Option("taxes", "Налоги"),
                ft.dropdown.Option("home", "ЖКХ"),
                ft.dropdown.Option("docs", "Документы"),
                ft.dropdown.Option("family", "Семья"),
                ft.dropdown.Option("work", "Работа"),
                ft.dropdown.Option("auto", "Авто"),
                ft.dropdown.Option("business", "Бизнес/ИП"),
            ],
            border_radius=12,
        )
        status_dropdown = ft.Dropdown(
            label="Статус",
            value=law.get("status", "draft"),
            options=[
                ft.dropdown.Option("draft", "draft"),
                ft.dropdown.Option("published", "published"),
                ft.dropdown.Option("archived", "archived"),
            ],
            border_radius=12,
        )
        priority_dropdown = ft.Dropdown(
            label="Приоритет",
            value=law.get("priority", "medium"),
            options=[
                ft.dropdown.Option("low", "Низкий"),
                ft.dropdown.Option("medium", "Средний"),
                ft.dropdown.Option("high", "Высокий"),
            ],
            border_radius=12,
        )
        target_field = ft.TextField(label="Кого касается", value=law.get("target", ""), border_radius=12)
        date_field = ft.TextField(label="Дата вступления", value=law.get("date", ""), border_radius=12)
        short_field = ft.TextField(
            label="Что изменилось",
            value=law.get("short", ""),
            min_lines=2,
            max_lines=3,
            border_radius=12,
        )
        action_field = ft.TextField(
            label="Что сделать пользователю",
            value=law.get("what_to_do", ""),
            min_lines=2,
            max_lines=3,
            border_radius=12,
        )
        related_field = ft.TextField(
            label="Связанные сценарии",
            value=", ".join(law.get("related_scenarios", []) or []),
            hint_text="Через запятую",
            border_radius=12,
        )
        related_problems_field = ft.TextField(
            label="Связанные проблемы (ID через запятую)",
            value=", ".join(law.get("related_problems", []) or []),
            hint_text="lost-passport, childbirth, …",
            border_radius=12,
        )
        profile_tags_field = ft.TextField(
            label="Теги профиля (через запятую)",
            value=", ".join(law.get("profile_tags", []) or []),
            hint_text="ip, has_children, housing_owner, …",
            border_radius=12,
        )
        source_field = ft.TextField(label="Официальный источник", value=law.get("source_url", ""), border_radius=12)
        last_checked_field = ft.TextField(label="Дата проверки источника (дд.мм.гггг)", value=law.get("last_checked", ""), border_radius=12)
        processing_dropdown = ft.Dropdown(
            label="Статус обработки",
            value=law.get("processing_status", "new"),
            options=[
                ft.dropdown.Option("new", "Новое"),
                ft.dropdown.Option("reviewed", "Проверено"),
                ft.dropdown.Option("applied", "Применено"),
            ],
            border_radius=12,
        )
        detail_field = ft.TextField(
            label="Подробности для карточки",
            value="\n".join(detail.get("details", [])),
            min_lines=3,
            max_lines=5,
            border_radius=12,
        )

        def _split_tags(raw) -> list[str]:
            if isinstance(raw, list):
                return [str(x).strip() for x in raw if str(x).strip()]
            return [x.strip() for x in (raw or "").split(",") if x.strip()]

        def save(dialog) -> None:
            normalized_title = _text_value(title_field)
            if not normalized_title:
                _show_message("Введите заголовок закон-апдейта.", APP_COLORS["warning"])
                return
            law.update(
                {
                    "title": normalized_title,
                    "category": category_dropdown.value or "family",
                    "category_name": _law_category_name(category_dropdown.value or "family"),
                    "date": _text_value(date_field) or "Требует уточнения",
                    "target": _text_value(target_field) or "Требует уточнения",
                    "short": _text_value(short_field) or "Описание будет уточнено редактором.",
                    "what_to_do": _text_value(action_field) or "Проверьте официальный источник и уточните актуальный порядок действий.",
                    "related_scenarios": _split_related_scenarios(related_field.value),
                    "related_problems": _split_law_problem_ids(related_problems_field.value),
                    "profile_tags": _split_tags(profile_tags_field.value),
                    "source_url": _text_value(source_field) or "https://pravo.by/",
                    "last_checked": _text_value(last_checked_field),
                    "status": status_dropdown.value or "draft",
                    "priority": priority_dropdown.value or "medium",
                    "processing_status": processing_dropdown.value or "new",
                }
            )
            details = [line.strip() for line in (detail_field.value or "").splitlines() if line.strip()]
            law_detail_state[law_id] = {
                "summary": law["short"],
                "details": details or [law["what_to_do"]],
            }
            admin_state["law_updates"] = law_updates_state
            _add_admin_audit(f"Отредактирован закон-апдейт «{normalized_title}»", "content_editor")
            save_current_state()
            _close(dialog)
            _show_message("Закон-апдейт обновлён.")
            route_change()

        dialog = _form_dialog(
            "Редактировать закон-апдейт",
            [
                title_field,
                ft.Row(
                    spacing=10,
                    run_spacing=10,
                    wrap=True,
                    controls=[
                        ft.Container(expand=True, content=category_dropdown),
                        ft.Container(expand=True, content=status_dropdown),
                        ft.Container(expand=True, content=priority_dropdown),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    run_spacing=10,
                    wrap=True,
                    controls=[
                        ft.Container(expand=True, content=processing_dropdown),
                        ft.Container(expand=True, content=last_checked_field),
                    ],
                ),
                target_field,
                date_field,
                short_field,
                action_field,
                related_field,
                related_problems_field,
                profile_tags_field,
                source_field,
                detail_field,
            ],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=560,
        )
        _open_control(dialog)

    for law_item in law_updates_state:
        _normalize_law_update(law_item)
    for source_item in official_sources_state:
        _normalize_official_source(source_item)

    def admin_create_source(
        title: str,
        url: str,
        source_type: str,
        description: str,
        last_checked_at: str,
    ) -> None:
        normalized_title = (title or "").strip()
        normalized_url = (url or "").strip()
        if not normalized_title:
            _show_message("Введите название источника.", APP_COLORS["warning"])
            return
        if not _is_allowed_official_source(normalized_url):
            _show_message("Укажите официальный ресурс Беларуси: pravo.by или домен .gov.by.", APP_COLORS["warning"])
            return
        source_id = _slugify(normalized_title, "source")
        source = {
            "id": source_id,
            "title": normalized_title,
            "url": normalized_url,
            "source_type": source_type or "other",
            "description": (description or "Описание будет уточнено редактором.").strip(),
            "last_checked_at": (last_checked_at or "").strip(),
            "status": "active" if (last_checked_at or "").strip() else "requires_check",
        }
        official_sources_state.insert(0, source)
        admin_state["official_sources"] = official_sources_state
        _add_admin_audit(f"Добавлен официальный источник «{normalized_title}»", "content_editor")
        save_current_state()
        _show_message("Источник добавлен.")
        route_change()

    def admin_set_source_status(source_id: str, status_value: str) -> None:
        source = _find_item(official_sources_state, source_id)
        if not source:
            _show_message("Источник не найден.", APP_COLORS["warning"])
            return
        source["status"] = status_value or "requires_check"
        admin_state["official_sources"] = official_sources_state
        _add_admin_audit(f"Статус источника «{source.get('title', source_id)}» изменён на {source['status']}", "content_editor")
        save_current_state()
        _show_message("Статус источника обновлён.")
        route_change()

    def admin_delete_source(source_id: str) -> None:
        source = _find_item(official_sources_state, source_id)
        if not source:
            _show_message("Источник не найден.", APP_COLORS["warning"])
            return

        def delete(dialog) -> None:
            official_sources_state[:] = [item for item in official_sources_state if item.get("id") != source_id]
            admin_state["official_sources"] = official_sources_state
            _add_admin_audit(f"Удалён официальный источник «{source.get('title', source_id)}»", "content_editor")
            save_current_state()
            _close(dialog)
            _show_message("Источник удалён.")
            route_change()

        _confirm_action(
            "Удалить источник?",
            f"Источник «{source.get('title', 'Без названия')}» будет удалён.",
            "Удалить",
            delete,
            danger=True,
        )

    def admin_open_edit_source_dialog(source_id: str) -> None:
        source = _find_item(official_sources_state, source_id)
        if not source:
            _show_message("Источник не найден.", APP_COLORS["warning"])
            return
        _normalize_official_source(source)
        title_field = ft.TextField(label="Название источника", value=source.get("title", ""), border_radius=12)
        url_field = ft.TextField(label="Сайт", value=source.get("url", ""), border_radius=12)
        source_type = ft.Dropdown(
            label="Тип источника",
            value=source.get("source_type", "other"),
            options=[
                ft.dropdown.Option("law", "Право"),
                ft.dropdown.Option("government_portal", "Госпортал"),
                ft.dropdown.Option("ministry", "Министерство"),
                ft.dropdown.Option("court", "Суд"),
                ft.dropdown.Option("tax", "Налоги"),
                ft.dropdown.Option("registry", "Реестр / ЗАГС"),
                ft.dropdown.Option("local_authority", "Исполком"),
                ft.dropdown.Option("other", "Другое"),
            ],
            border_radius=12,
        )
        status = ft.Dropdown(
            label="Статус",
            value=source.get("status", "requires_check"),
            options=[
                ft.dropdown.Option("active", "active"),
                ft.dropdown.Option("requires_check", "requires_check"),
                ft.dropdown.Option("archived", "archived"),
            ],
            border_radius=12,
        )
        last_checked = ft.TextField(label="Дата проверки", value=source.get("last_checked_at", ""), border_radius=12)
        description = ft.TextField(
            label="Описание",
            value=source.get("description", ""),
            min_lines=3,
            max_lines=5,
            border_radius=12,
        )

        def save(dialog) -> None:
            normalized_title = _text_value(title_field)
            normalized_url = _text_value(url_field)
            if not normalized_title:
                _show_message("Введите название источника.", APP_COLORS["warning"])
                return
            if not _is_allowed_official_source(normalized_url):
                _show_message("Укажите официальный ресурс Беларуси: pravo.by или домен .gov.by.", APP_COLORS["warning"])
                return
            source.update(
                {
                    "title": normalized_title,
                    "url": normalized_url,
                    "source_type": source_type.value or "other",
                    "description": _text_value(description) or "Описание будет уточнено редактором.",
                    "last_checked_at": _text_value(last_checked),
                    "status": status.value or ("active" if _text_value(last_checked) else "requires_check"),
                }
            )
            admin_state["official_sources"] = official_sources_state
            _add_admin_audit(f"Отредактирован официальный источник «{normalized_title}»", "content_editor")
            save_current_state()
            _close(dialog)
            _show_message("Источник обновлён.")
            route_change()

        dialog = _form_dialog(
            "Редактировать источник",
            [
                title_field,
                url_field,
                ft.Row(
                    spacing=10,
                    run_spacing=10,
                    wrap=True,
                    controls=[
                        ft.Container(expand=True, content=source_type),
                        ft.Container(expand=True, content=status),
                    ],
                ),
                last_checked,
                description,
            ],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=540,
        )
        _open_control(dialog)

    def admin_refresh_data(show_message: bool = False, rerender: bool = True) -> None:
        try:
            if not admin_api.health():
                raise AdminAPIError("API вернуло некорректный статус.")
            admin_state["problems"] = admin_api.list_admin_problems()
            admin_state["scenarios"] = admin_api.list_admin_scenarios()
            admin_state["documents"] = admin_api.list_admin_documents()
            admin_state["authorities"] = admin_api.list_admin_authorities()
            admin_state["deadlines"] = admin_api.list_admin_deadlines()

            scenario_ids = [item["id"] for item in admin_state["scenarios"] if isinstance(item.get("id"), int)]
            selected_scenario_id = _to_int(admin_state.get("selected_scenario_id"))
            if selected_scenario_id not in scenario_ids:
                selected_scenario_id = scenario_ids[0] if scenario_ids else None
            admin_state["selected_scenario_id"] = selected_scenario_id
            admin_state["scenario_detail"] = (
                admin_api.get_admin_scenario(selected_scenario_id) if selected_scenario_id is not None else None
            )

            admin_state["connected"] = True
            admin_state["error"] = ""
            admin_state["last_sync"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            if show_message:
                _show_message("Данные админ-панели обновлены.")
        except AdminAPIError as exc:
            admin_state["connected"] = False
            admin_state["error"] = str(exc)
            if show_message:
                _show_message(str(exc), APP_COLORS["warning"])
        if rerender:
            route_change()

    def admin_refresh(_=None) -> None:
        admin_refresh_data(show_message=True, rerender=True)

    def admin_workspace_select(item_type: str | None, item_id) -> None:
        admin_workspace_state["selected_type"] = item_type
        admin_workspace_state["selected_id"] = item_id
        if item_type == "scenario" and item_id is not None:
            admin_workspace_state.setdefault("expanded_scenarios", set()).add(item_id)
            try:
                admin_state["selected_scenario_id"] = item_id
                admin_state["scenario_detail"] = admin_api.get_admin_scenario(item_id)
            except AdminAPIError as exc:
                _show_message(f"Не удалось загрузить сценарий: {exc}", APP_COLORS["danger"])
        elif item_type in {"stage", "step"}:
            pass
        route_change()

    def admin_workspace_toggle_section(section_key: str) -> None:
        sections: set = admin_workspace_state.setdefault("expanded_sections", set())
        if section_key in sections:
            sections.remove(section_key)
        else:
            sections.add(section_key)
        route_change()

    def admin_workspace_toggle_scenario(scenario_id) -> None:
        expanded: set = admin_workspace_state.setdefault("expanded_scenarios", set())
        if scenario_id in expanded:
            expanded.remove(scenario_id)
            route_change()
            return
        expanded.clear()
        expanded.add(scenario_id)
        try:
            admin_state["selected_scenario_id"] = scenario_id
            admin_state["scenario_detail"] = admin_api.get_admin_scenario(scenario_id)
        except AdminAPIError as exc:
            _show_message(f"Не удалось загрузить сценарий: {exc}", APP_COLORS["danger"])
        route_change()

    def admin_workspace_toggle_stage(stage_key) -> None:
        expanded: set = admin_workspace_state.setdefault("expanded_stages", set())
        if stage_key in expanded:
            expanded.remove(stage_key)
        else:
            expanded.add(stage_key)
        route_change()

    def admin_workspace_save(_=None) -> None:
        if not admin_workspace_state.get("dirty"):
            _show_message("Нет изменений для сохранения.")
            return
        _show_message("Сохранение появится в Фазе 2.")

    def admin_workspace_open_legacy(_=None) -> None:
        page.run_task(page.push_route, "/admin")

    def admin_workspace_back_to_tree(_=None) -> None:
        admin_workspace_state["selected_type"] = None
        admin_workspace_state["selected_id"] = None
        route_change()

    def admin_create_problem(title: str, category: str, short_description: str) -> None:
        normalized_title = (title or "").strip()
        if not normalized_title:
            _show_message("Введите название проблемы.", APP_COLORS["warning"])
            return
        payload = {
            "title": normalized_title,
            "slug": _slugify(normalized_title, "problem"),
            "short_description": (short_description or "").strip(),
            "description": (short_description or "").strip(),
            "icon": "CATEGORY_OUTLINED",
            "category": (category or "Общее").strip() or "Общее",
            "status": "draft",
        }
        try:
            admin_api.create_problem(payload)
            _show_message("Проблема создана.")
            admin_refresh_data(rerender=True)
        except AdminAPIError as exc:
            _show_message(f"Не удалось создать проблему: {exc}", APP_COLORS["danger"])

    def admin_set_problem_status(problem_id: int, status_value: str) -> None:
        try:
            admin_api.update_problem(problem_id, {"status": status_value})
            _show_message("Статус проблемы обновлен.")
            admin_refresh_data(rerender=True)
        except AdminAPIError as exc:
            _show_message(f"Не удалось обновить статус проблемы: {exc}", APP_COLORS["danger"])

    def admin_create_scenario(problem_id: int, title: str, short_description: str, difficulty_level: str) -> None:
        normalized_title = (title or "").strip()
        if not normalized_title:
            _show_message("Введите название сценария.", APP_COLORS["warning"])
            return
        if not problem_id:
            _show_message("Выберите проблему для сценария.", APP_COLORS["warning"])
            return
        payload = {
            "problem_id": problem_id,
            "title": normalized_title,
            "slug": _slugify(normalized_title, "scenario"),
            "short_description": (short_description or "").strip(),
            "description": (short_description or "").strip(),
            "target_audience": "",
            "estimated_duration": "",
            "difficulty_level": difficulty_level or "medium",
            "status": "draft",
            "priority": 0,
        }
        try:
            admin_api.create_scenario(payload)
            _show_message("Сценарий создан.")
            admin_refresh_data(rerender=True)
        except AdminAPIError as exc:
            _show_message(f"Не удалось создать сценарий: {exc}", APP_COLORS["danger"])

    def admin_set_scenario_status(scenario_id: int, status_value: str) -> None:
        try:
            admin_api.update_scenario(scenario_id, {"status": status_value})
            _show_message("Статус сценария обновлен.")
            admin_refresh_data(rerender=True)
        except AdminAPIError as exc:
            _show_message(f"Не удалось обновить статус сценария: {exc}", APP_COLORS["danger"])

    def admin_select_scenario(scenario_id: int | str | None) -> None:
        selected_id = _to_int(scenario_id)
        admin_state["selected_scenario_id"] = selected_id
        if selected_id is None:
            admin_state["scenario_detail"] = None
            route_change()
            return
        try:
            admin_state["scenario_detail"] = admin_api.get_admin_scenario(selected_id)
            admin_state["connected"] = True
            admin_state["error"] = ""
            admin_state["last_sync"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        except AdminAPIError as exc:
            _show_message(f"Не удалось загрузить сценарий: {exc}", APP_COLORS["danger"])
            admin_state["connected"] = False
            admin_state["error"] = str(exc)
        route_change()

    def _refresh_admin_scenario_detail(scenario_id: int | None) -> None:
        if scenario_id is None:
            admin_state["scenario_detail"] = None
            return
        admin_state["scenario_detail"] = admin_api.get_admin_scenario(scenario_id)
        admin_state["last_sync"] = datetime.now().strftime("%d.%m.%Y %H:%M")

    def admin_create_stage(
        scenario_id: int | str | None,
        title: str,
        description: str,
        order_index: int,
        is_required: bool,
    ) -> None:
        selected_id = _to_int(scenario_id)
        normalized_title = (title or "").strip()
        if selected_id is None:
            _show_message("Выберите сценарий для добавления этапа.", APP_COLORS["warning"])
            return
        if not normalized_title:
            _show_message("Введите название этапа.", APP_COLORS["warning"])
            return
        payload = {
            "scenario_id": selected_id,
            "title": normalized_title,
            "description": (description or "").strip(),
            "order_index": max(0, order_index),
            "is_required": bool(is_required),
        }
        try:
            admin_api.create_stage(selected_id, payload)
            admin_state["selected_scenario_id"] = selected_id
            _refresh_admin_scenario_detail(selected_id)
            _show_message("Этап добавлен.")
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Не удалось добавить этап: {exc}", APP_COLORS["danger"])

    def admin_create_step(
        scenario_id: int | str | None,
        stage_id: int | str | None,
        title: str,
        description: str,
        order_index: int,
        action_type: str,
        authority_id: int | str | None,
        deadline_id: int | str | None,
        is_required: bool,
        document_ids: list[int | str] | None,
    ) -> None:
        selected_scenario_id = _to_int(scenario_id)
        normalized_stage_id = _to_int(stage_id)
        normalized_title = (title or "").strip()
        if selected_scenario_id is None:
            _show_message("Выберите сценарий для добавления шага.", APP_COLORS["warning"])
            return
        if normalized_stage_id is None:
            _show_message("Выберите этап для шага.", APP_COLORS["warning"])
            return
        if not normalized_title:
            _show_message("Введите название шага.", APP_COLORS["warning"])
            return
        payload = {
            "stage_id": normalized_stage_id,
            "title": normalized_title,
            "description": (description or "").strip(),
            "order_index": max(0, order_index),
            "action_type": action_type or "info",
            "authority_id": _to_int(authority_id),
            "deadline_id": _to_int(deadline_id),
            "is_required": bool(is_required),
        }
        try:
            created_step = admin_api.create_step(normalized_stage_id, payload)
            created_step_id = _to_int(created_step.get("id"))
            if created_step_id is not None:
                for raw_document_id in document_ids or []:
                    normalized_document_id = _to_int(raw_document_id)
                    if normalized_document_id is not None:
                        admin_api.attach_step_document(created_step_id, normalized_document_id)
            admin_state["selected_scenario_id"] = selected_scenario_id
            _refresh_admin_scenario_detail(selected_scenario_id)
            _show_message("Шаг добавлен.")
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Не удалось добавить шаг: {exc}", APP_COLORS["danger"])

    def admin_set_stage_required(scenario_id: int | str | None, stage_id: int, is_required: bool) -> None:
        selected_scenario_id = _to_int(scenario_id)
        if selected_scenario_id is None:
            _show_message("Сначала выберите сценарий.", APP_COLORS["warning"])
            return
        try:
            admin_api.update_stage(stage_id, {"is_required": is_required})
            _refresh_admin_scenario_detail(selected_scenario_id)
            _show_message("Статус этапа обновлен.")
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Не удалось обновить этап: {exc}", APP_COLORS["danger"])

    def admin_set_step_required(scenario_id: int | str | None, step_id: int, is_required: bool) -> None:
        selected_scenario_id = _to_int(scenario_id)
        if selected_scenario_id is None:
            _show_message("Сначала выберите сценарий.", APP_COLORS["warning"])
            return
        try:
            admin_api.update_step(step_id, {"is_required": is_required})
            _refresh_admin_scenario_detail(selected_scenario_id)
            _show_message("Статус шага обновлен.")
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Не удалось обновить шаг: {exc}", APP_COLORS["danger"])

    def admin_edit_scenario(scenario_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        if sid is None:
            return
        scenario = next((item for item in admin_state.get("scenarios", []) if item.get("id") == sid), None)
        if scenario is None:
            _show_message("Сценарий не найден в кэше.", APP_COLORS["warning"])
            return
        title_field = ft.TextField(label="Название", value=scenario.get("title", ""), border_radius=12)
        slug_field = ft.TextField(label="Slug", value=scenario.get("slug", ""), border_radius=12, helper="Латиница, дефисы", helper_max_lines=1)
        short_desc_field = ft.TextField(label="Краткое описание", value=scenario.get("short_description", ""), border_radius=12, multiline=True, min_lines=2, max_lines=3)
        difficulty_field = ft.Dropdown(
            label="Сложность",
            value=scenario.get("difficulty_level", "medium"),
            border_radius=12,
            options=[ft.dropdown.Option("easy", "Лёгкий"), ft.dropdown.Option("medium", "Средний"), ft.dropdown.Option("hard", "Сложный")],
        )

        def save(dialog) -> None:
            title = _text_value(title_field)
            if not title:
                _show_message("Введите название.", APP_COLORS["warning"])
                return
            payload: dict = {"title": title, "short_description": _text_value(short_desc_field)}
            slug = _text_value(slug_field)
            if slug:
                payload["slug"] = slug
            if difficulty_field.value:
                payload["difficulty_level"] = difficulty_field.value
            try:
                admin_api.update_scenario(sid, payload)
                _show_message("Сценарий обновлён.")
                _close(dialog)
                admin_refresh_data(rerender=True)
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Редактировать сценарий",
            [title_field, slug_field, short_desc_field, difficulty_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=480,
        )
        _open_control(dialog)

    def admin_add_dependency_dialog(scenario_id: int | str | None, step_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        stp_id = _to_int(step_id)
        if sid is None or stp_id is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        existing_dep_ids = {
            d.get("depends_on_step_id")
            for d in detail.get("dependencies", [])
            if d.get("step_id") == stp_id
        }
        options: list[ft.dropdown.Option] = []
        for stage in detail.get("stages", []):
            for s in stage.get("steps", []):
                if s.get("id") != stp_id and s.get("id") not in existing_dep_ids:
                    label = f"{stage.get('title', '?')} → {s.get('title', '?')}"
                    options.append(ft.dropdown.Option(str(s["id"]), label))
        if not options:
            _show_message("Нет доступных шагов для зависимости.", APP_COLORS["warning"])
            return
        dropdown = ft.Dropdown(label="Шаг-предшественник", border_radius=12, options=options)

        def save(dialog) -> None:
            prereq_id = _to_int(dropdown.value)
            if prereq_id is None:
                _show_message("Выберите шаг.", APP_COLORS["warning"])
                return
            try:
                admin_api.create_dependency({
                    "scenario_id": sid,
                    "step_id": stp_id,
                    "depends_on_step_id": prereq_id,
                    "description": "",
                })
                _show_message("Зависимость добавлена.")
                _close(dialog)
                _refresh_admin_scenario_detail(sid)
                route_change()
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Добавить зависимость",
            [ft.Text("Шаг будет заблокирован до выполнения выбранного шага.", size=13, color=APP_COLORS["muted"]), dropdown],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=440,
        )
        _open_control(dialog)

    def admin_delete_dependency(scenario_id: int | str | None, dependency_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        dep_id = _to_int(dependency_id)
        if sid is None or dep_id is None:
            return
        try:
            admin_api.delete_dependency(dep_id)
            _show_message("Зависимость удалена.")
            _refresh_admin_scenario_detail(sid)
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_add_related_dialog(scenario_id: int | str | None, available_scenarios: list) -> None:
        sid = _to_int(scenario_id)
        if sid is None:
            return
        if not available_scenarios:
            _show_message("Нет доступных сценариев для связи.", APP_COLORS["warning"])
            return
        scenario_options = [ft.dropdown.Option(str(s["id"]), s.get("title", f"#{s['id']}")) for s in available_scenarios]
        relation_options = [
            ft.dropdown.Option("related", "Связанный"),
            ft.dropdown.Option("prerequisite", "Предшествующий"),
            ft.dropdown.Option("alternative", "Альтернативный"),
        ]
        scenario_dd = ft.Dropdown(label="Сценарий", border_radius=12, options=scenario_options)
        relation_dd = ft.Dropdown(label="Тип связи", border_radius=12, options=relation_options, value="related")
        desc_field = ft.TextField(label="Описание (необязательно)", border_radius=12)

        def save(dialog) -> None:
            related_id = _to_int(scenario_dd.value)
            if related_id is None:
                _show_message("Выберите сценарий.", APP_COLORS["warning"])
                return
            try:
                admin_api.create_related_scenario({
                    "scenario_id": sid,
                    "related_scenario_id": related_id,
                    "relation_type": relation_dd.value or "related",
                    "description": _text_value(desc_field),
                })
                _show_message("Связь добавлена.")
                _close(dialog)
                _refresh_admin_scenario_detail(sid)
                route_change()
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Добавить связанный сценарий",
            [scenario_dd, relation_dd, desc_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=460,
        )
        _open_control(dialog)

    def admin_delete_related(scenario_id: int | str | None, related_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        rid = _to_int(related_id)
        if sid is None or rid is None:
            return
        try:
            admin_api.delete_related_scenario(rid)
            _show_message("Связь удалена.")
            _refresh_admin_scenario_detail(sid)
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_add_source_ref_dialog(scenario_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        if sid is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        title_field = ft.TextField(label="Название источника", border_radius=12)
        url_field = ft.TextField(label="URL (https://...)", border_radius=12)
        type_dd = ft.Dropdown(
            label="Тип источника",
            border_radius=12,
            value="other",
            options=[
                ft.dropdown.Option("law", "Право"),
                ft.dropdown.Option("government_portal", "Гос. портал"),
                ft.dropdown.Option("ministry", "Министерство"),
                ft.dropdown.Option("court", "Суд"),
                ft.dropdown.Option("tax", "Налоговая"),
                ft.dropdown.Option("registry", "Реестр"),
                ft.dropdown.Option("other", "Другое"),
            ],
        )
        scenario_label = "Сценарий: " + detail.get("title", "#" + str(sid))
        attach_opts = [ft.dropdown.Option(f"scenario:{sid}", scenario_label)]
        for s in detail.get("stages", []):
            attach_opts.append(ft.dropdown.Option(
                f"stage:{s['id']}",
                "Этап: " + s.get("title", "#" + str(s["id"])),
            ))
        for stg in detail.get("stages", []):
            for step in stg.get("steps", []):
                attach_opts.append(ft.dropdown.Option(
                    f"step:{step['id']}",
                    "Шаг: " + step.get("title", "#" + str(step["id"])),
                ))
        attach_to_dd = ft.Dropdown(
            label="Прикрепить к",
            border_radius=12,
            value=f"scenario:{sid}",
            options=attach_opts,
        )
        desc_field = ft.TextField(label="Описание (необязательно)", border_radius=12)

        def save(dialog) -> None:
            title = _text_value(title_field)
            url = _text_value(url_field)
            if not title:
                _show_message("Введите название источника.", APP_COLORS["warning"])
                return
            if not url:
                _show_message("Введите URL.", APP_COLORS["warning"])
                return
            raw = attach_to_dd.value or f"scenario:{sid}"
            parts = raw.split(":", 1)
            s_type = parts[0] if len(parts) == 2 else "scenario"
            s_id = _to_int(parts[1]) if len(parts) == 2 else sid
            try:
                admin_api.create_source_reference({
                    "sourceable_type": s_type,
                    "sourceable_id": s_id,
                    "title": title,
                    "url": url,
                    "source_type": type_dd.value or "other",
                    "description": _text_value(desc_field),
                })
                _show_message("Источник добавлен.")
                _close(dialog)
                _refresh_admin_scenario_detail(sid)
                route_change()
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Добавить источник права",
            [title_field, url_field, type_dd, attach_to_dd, desc_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Добавить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=480,
        )
        _open_control(dialog)

    def admin_delete_source_ref(scenario_id: int | str | None, ref_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        rid = _to_int(ref_id)
        if sid is None or rid is None:
            return
        try:
            admin_api.delete_source_reference(rid)
            _show_message("Источник удалён.")
            _refresh_admin_scenario_detail(sid)
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_create_authority(
        title: str,
        type_: str,
        address: str,
        phone: str,
        url: str,
        working_hours: str,
        description: str,
    ) -> None:
        title = (title or "").strip()
        if not title:
            _show_message("Введите название учреждения.", APP_COLORS["warning"])
            return
        try:
            admin_api.create_authority({
                "title": title,
                "type": (type_ or "").strip(),
                "address": (address or "").strip(),
                "phone": (phone or "").strip(),
                "website_url": (url or "").strip(),
                "working_hours": (working_hours or "").strip(),
                "description": (description or "").strip(),
            })
            _show_message("Учреждение добавлено.")
            admin_refresh_data(rerender=True)
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_edit_authority_dialog(authority_id: int | str | None) -> None:
        aid = _to_int(authority_id)
        if aid is None:
            return
        item = next((a for a in admin_state.get("authorities", []) if a.get("id") == aid), None)
        if item is None:
            _show_message("Учреждение не найдено.", APP_COLORS["warning"])
            return
        title_f = ft.TextField(label="Название", value=item.get("title", ""), border_radius=12)
        type_f = ft.TextField(label="Тип", value=item.get("type", ""), border_radius=12)
        address_f = ft.TextField(label="Адрес", value=item.get("address", ""), border_radius=12)
        phone_f = ft.TextField(label="Телефон", value=item.get("phone", ""), border_radius=12)
        url_f = ft.TextField(label="Сайт", value=item.get("website_url", ""), border_radius=12)
        hours_f = ft.TextField(label="Часы работы", value=item.get("working_hours", ""), border_radius=12)
        desc_f = ft.TextField(label="Описание", value=item.get("description", ""), border_radius=12, multiline=True, min_lines=2, max_lines=3)

        def save(dialog) -> None:
            title = _text_value(title_f)
            if not title:
                _show_message("Введите название.", APP_COLORS["warning"])
                return
            try:
                admin_api.update_authority(aid, {
                    "title": title,
                    "type": _text_value(type_f),
                    "address": _text_value(address_f),
                    "phone": _text_value(phone_f),
                    "website_url": _text_value(url_f),
                    "working_hours": _text_value(hours_f),
                    "description": _text_value(desc_f),
                })
                _show_message("Учреждение обновлено.")
                _close(dialog)
                admin_refresh_data(rerender=True)
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Редактировать учреждение",
            [title_f, type_f, address_f, phone_f, url_f, hours_f, desc_f],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=480,
        )
        _open_control(dialog)

    def admin_delete_authority(authority_id: int | str | None) -> None:
        aid = _to_int(authority_id)
        if aid is None:
            return
        item = next((a for a in admin_state.get("authorities", []) if a.get("id") == aid), None)
        title = (item or {}).get("title", f"#{aid}")

        def do_delete(dialog) -> None:
            try:
                admin_api.delete_authority(aid)
                _close(dialog)
                _show_message("Учреждение удалено.")
                admin_refresh_data(rerender=True)
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        _confirm_action(
            "Удалить учреждение?",
            f"«{title}» будет удалено из базы.",
            "Удалить",
            do_delete,
            danger=True,
        )

    def admin_create_document(
        title: str,
        document_type: str,
        where_to_get: str,
        validity_period: str,
        description: str,
        is_required: bool,
    ) -> None:
        title = (title or "").strip()
        if not title:
            _show_message("Введите название документа.", APP_COLORS["warning"])
            return
        try:
            admin_api.create_document({
                "title": title,
                "document_type": (document_type or "").strip(),
                "where_to_get": (where_to_get or "").strip(),
                "validity_period": (validity_period or "").strip(),
                "description": (description or "").strip(),
                "is_required": bool(is_required),
            })
            _show_message("Документ добавлен.")
            admin_refresh_data(rerender=True)
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_edit_document_dialog(document_id: int | str | None) -> None:
        did = _to_int(document_id)
        if did is None:
            return
        item = next((d for d in admin_state.get("documents", []) if d.get("id") == did), None)
        if item is None:
            _show_message("Документ не найден.", APP_COLORS["warning"])
            return
        title_f = ft.TextField(label="Название", value=item.get("title", ""), border_radius=12)
        type_f = ft.TextField(label="Тип", value=item.get("document_type", ""), border_radius=12)
        where_f = ft.TextField(label="Где получить", value=item.get("where_to_get", ""), border_radius=12)
        validity_f = ft.TextField(label="Срок действия", value=item.get("validity_period", ""), border_radius=12)
        desc_f = ft.TextField(label="Описание", value=item.get("description", ""), border_radius=12, multiline=True, min_lines=2, max_lines=3)
        required_cb = ft.Checkbox(label="Обязательный", value=bool(item.get("is_required", True)))

        def save(dialog) -> None:
            title = _text_value(title_f)
            if not title:
                _show_message("Введите название.", APP_COLORS["warning"])
                return
            try:
                admin_api.update_document(did, {
                    "title": title,
                    "document_type": _text_value(type_f),
                    "where_to_get": _text_value(where_f),
                    "validity_period": _text_value(validity_f),
                    "description": _text_value(desc_f),
                    "is_required": required_cb.value,
                })
                _show_message("Документ обновлён.")
                _close(dialog)
                admin_refresh_data(rerender=True)
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Редактировать документ",
            [title_f, type_f, where_f, validity_f, desc_f, required_cb],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=480,
        )
        _open_control(dialog)

    def admin_delete_document(document_id: int | str | None) -> None:
        did = _to_int(document_id)
        if did is None:
            return
        item = next((d for d in admin_state.get("documents", []) if d.get("id") == did), None)
        title = (item or {}).get("title", f"#{did}")

        def do_delete(dialog) -> None:
            try:
                admin_api.delete_document(did)
                _close(dialog)
                _show_message("Документ удалён.")
                admin_refresh_data(rerender=True)
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        _confirm_action(
            "Удалить документ?",
            f"«{title}» будет удалён из базы.",
            "Удалить",
            do_delete,
            danger=True,
        )

    def admin_delete_scenario(scenario_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        if sid is None:
            return
        scenario = next((item for item in admin_state.get("scenarios", []) if item.get("id") == sid), None)
        title = (scenario or {}).get("title", f"#{sid}")

        def do_delete(dialog) -> None:
            try:
                admin_api.delete_scenario(sid)
                if admin_state.get("selected_scenario_id") == sid:
                    admin_state["selected_scenario_id"] = None
                    admin_state["scenario_detail"] = None
                _close(dialog)
                _show_message("Сценарий удалён.")
                admin_refresh_data(rerender=True)
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        _confirm_action(
            "Удалить сценарий?",
            f"«{title}» и все его этапы и шаги будут удалены из базы.",
            "Удалить",
            do_delete,
            danger=True,
        )

    def admin_edit_stage(scenario_id: int | str | None, stage_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        stg_id = _to_int(stage_id)
        if sid is None or stg_id is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        stage = next((s for s in detail.get("stages", []) if s.get("id") == stg_id), None)
        if stage is None:
            _show_message("Этап не найден в кэше.", APP_COLORS["warning"])
            return
        title_field = ft.TextField(label="Название этапа", value=stage.get("title", ""), border_radius=12)
        desc_field = ft.TextField(label="Описание", value=stage.get("description", ""), border_radius=12, multiline=True, min_lines=2, max_lines=3)
        order_field = ft.TextField(label="Порядок (order_index)", value=str(stage.get("order_index", 0)), border_radius=12, keyboard_type=ft.KeyboardType.NUMBER)

        def save(dialog) -> None:
            title = _text_value(title_field)
            if not title:
                _show_message("Введите название этапа.", APP_COLORS["warning"])
                return
            order = _to_int(_text_value(order_field)) or 0
            try:
                admin_api.update_stage(stg_id, {"title": title, "description": _text_value(desc_field), "order_index": order})
                _show_message("Этап обновлён.")
                _close(dialog)
                _refresh_admin_scenario_detail(sid)
                route_change()
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Редактировать этап",
            [title_field, desc_field, order_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=460,
        )
        _open_control(dialog)

    def admin_delete_stage(scenario_id: int | str | None, stage_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        stg_id = _to_int(stage_id)
        if sid is None or stg_id is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        stage = next((s for s in detail.get("stages", []) if s.get("id") == stg_id), None)
        title = (stage or {}).get("title", f"Этап #{stg_id}")

        def do_delete(dialog) -> None:
            try:
                admin_api.delete_stage(stg_id)
                _close(dialog)
                _show_message("Этап удалён.")
                _refresh_admin_scenario_detail(sid)
                route_change()
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        _confirm_action(
            "Удалить этап?",
            f"«{title}» и все его шаги будут удалены.",
            "Удалить",
            do_delete,
            danger=True,
        )

    def admin_edit_step(scenario_id: int | str | None, step_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        stp_id = _to_int(step_id)
        if sid is None or stp_id is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        step = next(
            (stp for stage in detail.get("stages", []) for stp in stage.get("steps", []) if stp.get("id") == stp_id),
            None,
        )
        if step is None:
            _show_message("Шаг не найден в кэше.", APP_COLORS["warning"])
            return
        title_field = ft.TextField(label="Название шага", value=step.get("title", ""), border_radius=12)
        desc_field = ft.TextField(label="Описание", value=step.get("description", ""), border_radius=12, multiline=True, min_lines=2, max_lines=3)
        order_field = ft.TextField(label="Порядок (order_index)", value=str(step.get("order_index", 0)), border_radius=12, keyboard_type=ft.KeyboardType.NUMBER)
        action_field = ft.Dropdown(
            label="Тип действия",
            value=step.get("action_type", "info"),
            border_radius=12,
            options=[
                ft.dropdown.Option("info"), ft.dropdown.Option("submit"), ft.dropdown.Option("visit"),
                ft.dropdown.Option("pay"), ft.dropdown.Option("prepare"), ft.dropdown.Option("wait"),
            ],
        )

        def save(dialog) -> None:
            title = _text_value(title_field)
            if not title:
                _show_message("Введите название шага.", APP_COLORS["warning"])
                return
            order = _to_int(_text_value(order_field)) or 0
            try:
                admin_api.update_step(stp_id, {
                    "title": title,
                    "description": _text_value(desc_field),
                    "order_index": order,
                    "action_type": action_field.value or "info",
                })
                _show_message("Шаг обновлён.")
                _close(dialog)
                _refresh_admin_scenario_detail(sid)
                route_change()
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        dialog = _form_dialog(
            "Редактировать шаг",
            [title_field, desc_field, order_field, action_field],
            [
                _dialog_button("Отмена", lambda _: _close(dialog)),
                _dialog_button("Сохранить", lambda _: save(dialog), primary=True),
            ],
            preferred_width=460,
        )
        _open_control(dialog)

    def admin_verify_scenario(scenario_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        if sid is None:
            return
        try:
            admin_api.verify_scenario(sid)
            _refresh_admin_scenario_detail(sid)
            _show_message("Сценарий отмечен как проверенный по источникам.")
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_move_stage(scenario_id: int | str | None, stage_id: int | str | None, direction: str) -> None:
        sid = _to_int(scenario_id)
        stg_id = _to_int(stage_id)
        if sid is None or stg_id is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        stages = sorted(detail.get("stages", []), key=lambda s: s.get("order_index", 0))
        idx = next((i for i, s in enumerate(stages) if s.get("id") == stg_id), None)
        if idx is None:
            return
        swap_idx = idx - 1 if direction == "up" else idx + 1
        if swap_idx < 0 or swap_idx >= len(stages):
            return
        stages[idx], stages[swap_idx] = stages[swap_idx], stages[idx]
        ordered_ids = [s["id"] for s in stages]
        try:
            admin_api.reorder_stages(sid, ordered_ids)
            _refresh_admin_scenario_detail(sid)
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_move_step(scenario_id: int | str | None, step_id: int | str | None, direction: str) -> None:
        sid = _to_int(scenario_id)
        stp_id = _to_int(step_id)
        if sid is None or stp_id is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        parent_stage = next(
            (stage for stage in detail.get("stages", []) if any(s.get("id") == stp_id for s in stage.get("steps", []))),
            None,
        )
        if parent_stage is None:
            return
        steps = sorted(parent_stage.get("steps", []), key=lambda s: s.get("order_index", 0))
        idx = next((i for i, s in enumerate(steps) if s.get("id") == stp_id), None)
        if idx is None:
            return
        swap_idx = idx - 1 if direction == "up" else idx + 1
        if swap_idx < 0 or swap_idx >= len(steps):
            return
        steps[idx], steps[swap_idx] = steps[swap_idx], steps[idx]
        ordered_ids = [s["id"] for s in steps]
        try:
            admin_api.reorder_steps(parent_stage["id"], ordered_ids)
            _refresh_admin_scenario_detail(sid)
            route_change()
        except AdminAPIError as exc:
            _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

    def admin_delete_step(scenario_id: int | str | None, step_id: int | str | None) -> None:
        sid = _to_int(scenario_id)
        stp_id = _to_int(step_id)
        if sid is None or stp_id is None:
            return
        detail = admin_state.get("scenario_detail") or {}
        step = next(
            (stp for stage in detail.get("stages", []) for stp in stage.get("steps", []) if stp.get("id") == stp_id),
            None,
        )
        title = (step or {}).get("title", f"Шаг #{stp_id}")

        def do_delete(dialog) -> None:
            try:
                admin_api.delete_step(stp_id)
                _close(dialog)
                _show_message("Шаг удалён.")
                _refresh_admin_scenario_detail(sid)
                route_change()
            except AdminAPIError as exc:
                _show_message(f"Ошибка: {exc}", APP_COLORS["danger"])

        _confirm_action(
            "Удалить шаг?",
            f"«{title}» будет удалён из этапа.",
            "Удалить",
            do_delete,
            danger=True,
        )

    def route_to_screen(route: str) -> str:
        clean_route = (route or "/").split("?", 1)[0]
        if clean_route.startswith("/problem/"):
            current_problem["id"] = clean_route.split("/problem/", 1)[1] or "lost-passport"
            return "problem_detail"
        if clean_route.startswith("/problem-detail/"):
            current_problem["id"] = clean_route.split("/problem-detail/", 1)[1] or "lost-passport"
            return "problem_detail"
        if clean_route == "/problem-detail":
            return "problem_detail"
        if clean_route.startswith("/situations/"):
            current_situation["id"] = clean_route.split("/situations/", 1)[1] or "childbirth"
            return "situation_detail"
        if clean_route.startswith("/situation-detail/"):
            current_situation["id"] = clean_route.split("/situation-detail/", 1)[1] or "childbirth"
            return "situation_detail"
        if clean_route == "/situation-detail":
            return "situation_detail"
        if clean_route.startswith("/scenarios/"):
            current_scenario_template["id"] = clean_route.split("/scenarios/", 1)[1] or SCENARIO_TEMPLATES[0]["id"]
            return "scenario_detail"
        if clean_route.startswith("/scenario-detail/"):
            current_scenario_template["id"] = clean_route.split("/scenario-detail/", 1)[1] or SCENARIO_TEMPLATES[0]["id"]
            return "scenario_detail"
        if clean_route == "/scenario-detail":
            return "scenario_detail"
        if clean_route.startswith("/laws/"):
            current_law["id"] = clean_route.split("/laws/", 1)[1] or "law1"
            return "law_detail"
        if clean_route.startswith("/legal-updates/"):
            current_law["id"] = clean_route.split("/legal-updates/", 1)[1] or "law1"
            return "law_detail"
        if clean_route.startswith("/law-detail/"):
            current_law["id"] = clean_route.split("/law-detail/", 1)[1] or "law1"
            return "law_detail"
        if clean_route == "/law-detail":
            return "law_detail"
        return {
            "/onboarding": "onboarding",
            "/login": "login",
            "/register": "register",
            "/": "home",
            "/search": "search",
            "/problems": "problems",
            "/scenarios": "scenarios",
            "/situations": "situations",
            "/documents": "documents",
            "/notifications": "notifications",
            "/laws": "laws",
            "/legal-updates": "laws",
            "/profile": "profile",
            "/learning": "learning",
            "/about": "about",
            "/admin": "admin",
            "/admin/workspace": "admin_workspace",
            "/utility": "utility",
            "/taxes": "taxes",
            "/email-preview": "email-preview",
        }.get(clean_route, "home")

    def screen_to_nav(screen_key: str) -> str:
        if screen_key in {"problem_detail", "problems", "search"}:
            return "problems"
        if screen_key == "situation_detail":
            return "situations"
        if screen_key in {"scenarios", "scenario_detail"}:
            return "problems"
        if screen_key in {"documents", "laws", "law_detail", "learning", "about", "admin", "admin_workspace", "email-preview"}:
            return "profile"
        if screen_key in {item[0] for item in NAV_ITEMS}:
            return screen_key
        return "home"

    def screen_to_top_nav(screen_key: str) -> str:
        if screen_key == "problem_detail":
            return "problems"
        if screen_key == "situation_detail":
            return "situations"
        if screen_key in {"scenarios", "scenario_detail"}:
            return "scenarios"
        if screen_key == "law_detail":
            return "laws"
        if screen_key == "search":
            return "home"
        if screen_key == "learning":
            return "home"
        if screen_key in {"about", "admin", "admin_workspace", "email-preview"}:
            return "home"
        if screen_key in {"documents", "laws", "profile", "home", "problems", "situations", "scenarios"}:
            return screen_key
        return "home"

    _PUBLIC_CONTENT_SCREENS = {"home", "search", "problems", "problem_detail", "scenarios", "scenario_detail", "laws", "law_detail"}

    def _with_offline_banner(content: ft.Control, screen_key: str) -> ft.Control:
        """G9 — показывает баннер оффлайн-режима для экранов с публичным контентом."""
        if screen_key not in _PUBLIC_CONTENT_SCREENS:
            return content
        if public_state.get("connected", False) or not public_state.get("loaded_once", False):
            return content
        error_text = public_state.get("error", "Backend недоступен.")
        banner = ft.Container(
            padding=ft.Padding(left=14, top=10, right=14, bottom=10),
            border_radius=12,
            bgcolor=APP_COLORS.get("warning_light", APP_COLORS["surface"]),
            border=border_all(APP_COLORS["warning"]),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.WIFI_OFF_OUTLINED, size=18, color=APP_COLORS["warning"]),
                    ft.Text(
                        "Оффлайн-режим · данные из кэша",
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=APP_COLORS["warning"],
                        expand=True,
                    ),
                    ft.TextButton(
                        "Повторить",
                        on_click=lambda _: _fetch_public_content(show_message=True) or route_change(),
                        style=ft.ButtonStyle(color=APP_COLORS["primary"]),
                    ),
                ],
            ),
        )
        return ft.Column(spacing=0, controls=[banner, content], expand=True)

    def build_content(screen_key: str, is_desktop: bool, is_tablet: bool = False) -> ft.Control:
        if screen_key == "onboarding":
            return build_onboarding_page(complete_onboarding, is_desktop)
        # Auth screens use their own threshold: two-column from 820px wide
        auth_wide = (page.width or 390) >= 820
        if screen_key == "login":
            return build_login_page(auth_wide, login_user, go_to, on_oauth=oauth_login, page=page)
        if screen_key == "register":
            return build_register_page(auth_wide, register_user, go_to, on_oauth=oauth_login, page=page)
        if screen_key == "home":
            return _with_offline_banner(build_home_page(
                open_problem,
                go_to,
                is_desktop,
                open_global_search,
                open_problem_category,
                app_user,
                build_dashboard_data(
                    situations_state,
                    situation_tasks_state,
                    documents=documents_state,
                    reminder_days=int(app_settings.get("doc_reminder_days", 30)),
                    utility_payments=utility_payments_state,
                    tax_obligations=tax_obligations_state,
                    utility_reminder_days=int(app_settings.get("utility_reminder_days", 7)),
                    tax_reminder_days=int(app_settings.get("tax_reminder_days", 14)),
                ),
                notifications_state,
                is_tablet=is_tablet,
            ), "home")
        if screen_key == "search":
            return _with_offline_banner(build_search_page(
                is_desktop=is_desktop,
                query=search_filters["query"],
                selected_filter=search_filters["filter"],
                on_query_change=update_search_query,
                on_filter_change=update_search_filter,
                go_to=go_to,
                open_problem=open_problem,
                open_scenario=open_scenario_template,
                open_law=open_law,
                situations=situations_state,
                documents=documents_state,
                laws=_normalized_published_laws(),
                institutions=institutions_state,
            ), "search")
        if screen_key == "problems":
            return _with_offline_banner(build_problems_page(
                open_problem,
                is_desktop,
                problem_filters["query"],
                problem_filters["category"],
                update_problem_query,
                update_problem_category,
                go_to=go_to,
            ), "problems")
        if screen_key == "problem_detail":
            return _with_offline_banner(build_problem_detail_page(
                current_problem["id"],
                go_back_to_problems,
                create_plan,
                is_desktop,
                get_step_values(current_problem["id"]),
                toggle_problem_step,
                learning_state["enabled"],
                get_quiz_state(current_problem["id"]),
                set_quiz_answer,
                submit_quiz,
                reset_quiz,
                save_problem,
                problem_overrides.get(current_problem["id"]),
            ), "problem_detail")
        if screen_key == "situations":
            return build_situations_page(
                open_situation,
                is_desktop,
                situations_state,
                situation_tasks_state,
                open_add_situation_dialog,
                open_edit_situation_dialog,
                confirm_delete_situation,
                open_scenario_templates,
                situation_filters["status"],
                update_situation_filter,
            )
        if screen_key == "scenarios":
            return _with_offline_banner(build_scenario_templates_page(
                open_scenario_template,
                is_desktop,
                scenario_filters["query"],
                scenario_filters["category"],
                update_scenario_query,
                update_scenario_category,
                favorite_scenario_ids,
                toggle_favorite_scenario,
                user=app_user,
                go_to=go_to,
            ), "scenarios")
        if screen_key == "scenario_detail":
            return _with_offline_banner(build_scenario_detail_page(
                current_scenario_template["id"],
                go_back_to_scenarios,
                create_situation_from_template,
                open_template_source,
                is_desktop,
                user=app_user,
                law_updates=law_updates_state,
                open_law=open_law,
            ), "scenario_detail")
        if screen_key == "situation_detail":
            return build_situation_detail_page(
                current_situation["id"],
                go_back_to_situations,
                is_desktop,
                situations_state,
                _tasks_with_dependency_state(situation_tasks_state),
                toggle_situation_task,
                open_add_task_dialog,
                open_edit_task_dialog,
                confirm_delete_task,
                open_edit_situation_dialog,
                confirm_delete_situation,
                save_situation_changes,
                situation_task_filter["value"],
                set_situation_task_filter,
                notes=user_notes_state.get(current_situation["id"], []),
                on_add_note=add_situation_note,
            )
        if screen_key == "documents":
            return build_documents_page(
                is_desktop,
                documents_state,
                open_add_document_dialog,
                open_edit_document_dialog,
                confirm_delete_document,
                privacy_settings.get("hide_sensitive_documents", True),
                visible_document_ids,
                toggle_document_sensitive,
                update_document_privacy,
                open_document_scan,
                reminder_days=int(app_settings.get("doc_reminder_days", 30)),
                activity_log=doc_activity_log_state,
                on_export_pdf=export_documents_pdf,
                on_import_pdf=import_documents_pdf,
            )
        if screen_key == "notifications":
            return build_notifications_page(
                is_desktop,
                notifications_state,
                mark_all_notifications_read,
                mark_notification_read,
                go_to,
                on_open_email_preview=open_email_preview,
            )
        if screen_key == "laws":
            published_laws = _normalized_published_laws()
            return _with_offline_banner(build_legal_updates_page(
                open_law,
                is_desktop,
                law_filters["query"],
                law_filters["category"],
                update_law_query,
                update_law_category,
                published_laws,
                _important_laws_for_user(published_laws),
                law_filters["sort"],
                update_law_sort,
                user_tags=_collect_user_tags(),
            ), "laws")
        if screen_key == "law_detail":
            return _with_offline_banner(build_law_detail_page(
                current_law["id"],
                go_back_to_laws,
                is_desktop,
                save_law,
                open_law_source,
                law_updates_state,
                law_detail_state,
            ), "law_detail")
        if screen_key == "settings":
            from pages.settings_page import build_settings_page
            return build_settings_page(
                settings=app_settings,
                on_setting_change=update_profile_setting,
                is_desktop=is_desktop,
                go_back=lambda _e: page.run_task(page.push_route, "/profile"),
            )
        if screen_key == "profile":
            return build_profile_page(
                is_desktop,
                app_user,
                app_settings,
                update_profile_setting,
                save_profile,
                logout_user,
                open_add_interest_dialog,
                go_to,
                reset_demo_data,
                favorite_scenario_ids,
                open_scenario_template,
                on_employment_change=set_employment_status,
                on_household_change=set_household_flag,
                on_toggle_tag=toggle_interest_tag,
                activity_log=user_activity_log_state,
                on_add_location=open_add_location_dialog,
                on_delete_location=delete_location,
                on_set_primary_location=set_primary_location,
            )
        if screen_key == "utility":
            return build_utility_tracker_page(
                is_desktop=is_desktop,
                accounts=utility_accounts_state,
                payments=utility_payments_state,
                on_add_account=open_add_utility_account_dialog,
                on_edit_account=open_edit_utility_account_dialog,
                on_delete_account=confirm_delete_utility_account,
                on_add_payment=open_add_utility_payment_dialog,
                on_edit_payment=open_edit_utility_payment_dialog,
                on_delete_payment=confirm_delete_utility_payment,
            )
        if screen_key == "taxes":
            return build_tax_tracker_page(
                is_desktop=is_desktop,
                obligations=tax_obligations_state,
                on_add=open_add_tax_obligation_dialog,
                on_edit=open_edit_tax_obligation_dialog,
                on_delete=confirm_delete_tax_obligation,
                on_mark_paid=mark_tax_obligation_paid,
                user=app_user,
            )
        if screen_key == "about":
            return build_about_page(lambda _: page.run_task(page.push_route, "/profile"), is_desktop)
        if screen_key == "learning":
            return build_learning_progress_page(is_desktop)
        if screen_key == "email-preview":
            def _close_email_preview(_=None):
                page.run_task(page.push_route, "/notifications")
            def _send_email_demo(_=None):
                _show_message("[Demo] Письмо «отправлено» — в production здесь будет SMTP-запрос.")
                _close_email_preview()
            return build_email_preview_page(
                email_data=email_preview_data or None,
                is_desktop=is_desktop,
                on_close=_close_email_preview,
                on_send_demo=_send_email_demo,
            )
        if screen_key == "admin_workspace":
            if not role_guard.has_role(auth_state, "content_editor"):
                from components.forbidden_page import build_forbidden_page
                return build_forbidden_page(
                    go_to,
                    is_desktop=is_desktop,
                    description="Раздел доступен редакторам контента и администраторам.",
                )
            if not admin_state.get("loaded_once"):
                admin_refresh_data(show_message=False, rerender=False)
                admin_state["loaded_once"] = True
            return build_admin_workspace_page(
                is_desktop=is_desktop,
                admin_state=admin_state,
                workspace_state=admin_workspace_state,
                search_field=admin_workspace_search_field,
                on_select=admin_workspace_select,
                on_toggle_section=admin_workspace_toggle_section,
                on_toggle_scenario=admin_workspace_toggle_scenario,
                on_toggle_stage=admin_workspace_toggle_stage,
                on_save=admin_workspace_save,
                on_refresh=admin_refresh,
                on_open_legacy=admin_workspace_open_legacy,
                on_back_to_tree=admin_workspace_back_to_tree,
            )
        if screen_key == "admin":
            # RBAC: только content_editor+ имеют доступ к админке
            if not role_guard.has_role(auth_state, "content_editor"):
                from components.forbidden_page import build_forbidden_page
                return build_forbidden_page(
                    go_to,
                    is_desktop=is_desktop,
                    description="Раздел доступен редакторам контента и администраторам.",
                )
            return build_admin_page(
                is_desktop=is_desktop,
                admin_state=admin_state,
                on_refresh=admin_refresh,
                on_open_workspace=lambda _e: page.run_task(page.push_route, "/admin/workspace"),
                on_create_problem=admin_create_problem,
                on_set_problem_status=admin_set_problem_status,
                on_create_scenario=admin_create_scenario,
                on_set_scenario_status=admin_set_scenario_status,
                on_edit_scenario=admin_edit_scenario,
                on_delete_scenario=admin_delete_scenario,
                on_create_law_update=admin_create_law_update,
                on_set_law_update_status=admin_set_law_update_status,
                on_delete_law_update=admin_delete_law_update,
                on_edit_law_update=admin_open_edit_law_update_dialog,
                on_create_source=admin_create_source,
                on_edit_source=admin_open_edit_source_dialog,
                on_delete_source=admin_delete_source,
                on_set_source_status=admin_set_source_status,
                on_select_scenario=admin_select_scenario,
                on_verify_scenario=admin_verify_scenario,
                on_create_stage=admin_create_stage,
                on_create_step=admin_create_step,
                on_set_stage_required=admin_set_stage_required,
                on_set_step_required=admin_set_step_required,
                on_edit_stage=admin_edit_stage,
                on_delete_stage=admin_delete_stage,
                on_edit_step=admin_edit_step,
                on_delete_step=admin_delete_step,
                on_move_stage=admin_move_stage,
                on_move_step=admin_move_step,
                on_add_dependency=admin_add_dependency_dialog,
                on_delete_dependency=admin_delete_dependency,
                on_add_related=admin_add_related_dialog,
                on_delete_related=admin_delete_related,
                on_add_source_ref=admin_add_source_ref_dialog,
                on_delete_source_ref=admin_delete_source_ref,
                on_create_authority=admin_create_authority,
                on_edit_authority=admin_edit_authority_dialog,
                on_delete_authority=admin_delete_authority,
                on_create_document=admin_create_document,
                on_edit_document=admin_edit_document_dialog,
                on_delete_document=admin_delete_document,
                on_select_admin_role=admin_select_role,
                on_tab_change=on_admin_tab_change,
                on_update_user_role=on_admin_update_user_role,
                on_toggle_user_status=on_admin_toggle_user_status,
                on_create_admin_user=on_admin_create_admin_user,
                on_add_category=on_admin_add_category,
                on_delete_category=on_admin_delete_category,
                on_toggle_notification_rule=on_admin_toggle_notification_rule,
                on_edit_rule_days=on_admin_edit_rule_days,
            )
        return build_home_page(
            open_problem,
            go_to,
            is_desktop,
            user=app_user,
            dashboard=build_dashboard_data(
                situations_state,
                situation_tasks_state,
                documents=documents_state,
                reminder_days=int(app_settings.get("doc_reminder_days", 30)),
                utility_payments=utility_payments_state,
                tax_obligations=tax_obligations_state,
                utility_reminder_days=int(app_settings.get("utility_reminder_days", 7)),
                tax_reminder_days=int(app_settings.get("tax_reminder_days", 14)),
            ),
        )

    # ---------------------------------------------------------------------------
    # AI Chat state
    # ---------------------------------------------------------------------------
    ai_chat_messages: list[dict] = [
        {
            "role": "assistant",
            "text": "Здравствуйте! Я ИИ-помощник Белпомощника.\n\nЗадайте вопрос о правах, документах или жизненных ситуациях.",
        }
    ]
    ai_chat_state: dict = {"visible": False, "mode": "mini", "docked": False}

    def open_ai_chat(_e=None) -> None:
        ai_chat_state["visible"] = True
        route_change()

    def close_ai_chat(_e=None) -> None:
        ai_chat_state["visible"] = False
        ai_chat_state["docked"] = False
        route_change()

    def toggle_ai_fullscreen(_e=None) -> None:
        ai_chat_state["mode"] = "mini" if ai_chat_state["mode"] == "fullscreen" else "fullscreen"
        route_change()

    def toggle_ai_dock(_e=None) -> None:
        ai_chat_state["docked"] = not ai_chat_state["docked"]
        if ai_chat_state["docked"]:
            ai_chat_state["mode"] = "mini"
        route_change()

    def on_nav_change(selected_key) -> None:
        key = selected_key if isinstance(selected_key, str) else None
        if key is None:
            event_data = getattr(selected_key, "data", None)
            if isinstance(event_data, str) and event_data in NAV_ROUTES:
                key = event_data
        if key is None:
            control = getattr(selected_key, "control", None)
            selected_index = getattr(control, "selected_index", None)
            if isinstance(selected_index, int) and 0 <= selected_index < len(NAV_ITEMS):
                key = NAV_ITEMS[selected_index][0]
        if key in NAV_ROUTES:
            page.run_task(page.push_route, NAV_ROUTES[key])

    def route_change(_event: ft.RouteChangeEvent | None = None) -> None:
        apply_page_theme()
        screen_key = route_to_screen(page.route)
        auth_screen = screen_key in {"login", "register"}
        intro_screen = screen_key == "onboarding"
        if not app_settings.get("onboarding_completed", False) and not intro_screen:
            page.route = "/onboarding"
            screen_key = "onboarding"
            intro_screen = True
            auth_screen = False
        elif intro_screen and app_settings.get("onboarding_completed", False):
            page.route = "/" if auth_state.get("logged_in") else "/login"
            screen_key = route_to_screen(page.route)
            auth_screen = screen_key in {"login", "register"}
            intro_screen = False
        # Гостевой режим: read-only маршруты доступны без логина.
        # Запрещены только разделы, требующие персональные данные/мутации.
        GUEST_BLOCKED_SCREENS = {
            "admin", "admin_workspace",
        }
        if not auth_state["logged_in"]:
            if screen_key in GUEST_BLOCKED_SCREENS and not auth_screen and not intro_screen:
                page.route = "/login"
                screen_key = "login"
                auth_screen = True
        elif auth_state["logged_in"] and auth_screen:
            page.route = "/"
            screen_key = "home"
            auth_screen = False
        if not public_state["loaded_once"]:
            _load_childbirth_scenario()
            public_state["loaded_once"] = True
        if screen_key == "admin" and not admin_state["loaded_once"]:
            admin_refresh_data(rerender=False)
            admin_state["loaded_once"] = True

        page_width = page.width or 390
        page_height = page.height or 844
        is_portrait = page_height > page_width
        # Mobile:  width<900  OR  (900-1099 wide portrait) — covers iPhones, Galaxy Fold
        # Tablet:  900-1279 (not mobile) — OnePlus Pad portrait, mid browsers
        # Desktop: >=1280 — MacBook Air fullscreen, OnePlus Pad landscape
        is_mobile = page_width < 900 or (page_width < 1100 and is_portrait)
        is_tablet = not is_mobile and page_width < 1280
        is_desktop = not is_mobile and page_width >= 1280
        chrome_width = min(1400, max(1080, int(page_width) - 64))

        is_wide = is_desktop or is_tablet
        screen_content = build_content(screen_key, is_wide, is_tablet=is_tablet)

        unread_count = sum(1 for n in notifications_state if not n.get("is_read", False))

        page.controls.clear()
        content_area: ft.Container | None = None

        if auth_screen or intro_screen:
            # Auth/onboarding: full-bleed animated background, scrollable, no chrome
            auth_body = ft.Container(
                content=ft.Column(
                    controls=[screen_content],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True,
                bgcolor=APP_COLORS["screen"],
            )
            page.add(app_safe_area(auth_body, include_bottom=True))

        elif is_desktop:
            # ── Desktop: top header + scrollable body + sticky footer ──────────
            # Структура: Column [header(78px), expand body со скроллом, footer(88px)].
            # При длинном контенте — крутится только body, header и footer остаются на местах.
            desktop_body = ft.Container(
                content=ft.Column(
                    controls=[
                        screen_content,
                        ft.Container(height=24),  # нижний воздух, чтобы footer не прилипал к контенту
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                opacity=0.0,
                animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
                expand=True,
                bgcolor=APP_COLORS["screen"],
            )
            content_area = desktop_body
            page.add(
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        build_desktop_header(
                            screen_to_top_nav(screen_key),
                            go_to,
                            chrome_width,
                            page=page,
                            user=app_user,
                            role=role_guard.current_role(auth_state),
                            test_accounts=test_accounts_state["items"],
                            on_logout=logout_user,
                            on_switch_account=switch_test_account,
                            on_login=lambda: go_to("/login"),
                        ),
                        desktop_body,
                        build_desktop_footer(go_to, min(1120, chrome_width)),
                    ],
                )
            )

        elif is_tablet:
            # ── Tablet: left sidebar + content ───────────────────────────────
            content_area = ft.Container(
                content=ft.Column(
                    controls=[screen_content],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                opacity=0.0,
                animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
                expand=True,
                bgcolor=APP_COLORS["screen"],
            )

            sidebar = build_sidebar(
                screen_to_nav(screen_key),
                go_to,
                toggle_theme,
                theme_mode_state["value"],
                app_user,
                tablet=True,
                on_open_ai_chat=open_ai_chat,
                notification_count=unread_count,
                role=role_guard.current_role(auth_state),
            )

            row_controls: list[ft.Control] = [sidebar, content_area]

            if ai_chat_state["visible"] and ai_chat_state["docked"]:
                docked_panel = build_ai_chat_overlay(
                    ai_chat_messages,
                    on_close=close_ai_chat,
                    on_toggle_fullscreen=toggle_ai_fullscreen,
                    on_toggle_dock=toggle_ai_dock,
                    fullscreen=False,
                    docked=True,
                    desktop=False,
                )
                row_controls.append(docked_panel)

            page.add(ft.Row(expand=True, spacing=0, controls=row_controls))

        else:
            # ── Mobile: minimal topbar on home only, content + bottom nav ───
            is_home_screen = screen_key == "home"
            topbar_controls: list[ft.Control] = []
            if is_home_screen:
                topbar_controls = [
                    build_mobile_topbar(
                        "Белпомощник",
                        go_to=go_to,
                        user=app_user,
                        on_open_ai_chat=open_ai_chat,
                        minimal=True,
                        notification_count=unread_count,
                    )
                ]

            page_body = mobile_page_layout(screen_content, include_bottom_nav=True)

            # Floating notification button on non-home, non-profile, non-notifications pages
            show_float_bell = screen_key not in {"home", "profile", "notifications"}
            if show_float_bell:
                page_body = ft.Stack(
                    expand=True,
                    controls=[
                        page_body,
                        ft.Container(
                            content=build_notification_button(go_to, unread_count),
                            right=14,
                            top=10,
                        ),
                    ],
                )

            page.add(
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        *topbar_controls,
                        page_body,
                        bottom_nav_safe_area(
                            build_bottom_nav(
                                screen_to_nav(screen_key),
                                on_nav_change,
                                on_open_ai_chat=open_ai_chat,
                            )
                        ),
                    ],
                )
            )

        # Floating AI chat overlay (mini or fullscreen, non-docked)
        if ai_chat_state["visible"] and not (ai_chat_state["docked"] and is_desktop):
            fullscreen_mode = ai_chat_state["mode"] == "fullscreen" or is_mobile or is_tablet
            chat_overlay = build_ai_chat_overlay(
                ai_chat_messages,
                on_close=close_ai_chat,
                on_toggle_fullscreen=toggle_ai_fullscreen,
                on_toggle_dock=toggle_ai_dock,
                fullscreen=fullscreen_mode,
                docked=False,
                desktop=is_desktop,
            )
            page.overlay.clear()
            page.overlay.append(chat_overlay)
        else:
            page.overlay.clear()

        page.update()

        # Fade-in for sidebar layouts
        if content_area is not None:
            content_area.opacity = 1.0
            content_area.update()

    page.on_route_change = route_change
    page.on_resize = lambda _: route_change()
    if not page.route:
        page.route = "/"
    _fetch_public_content()
    route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
