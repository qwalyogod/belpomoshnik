"""Unit tests for dashboard pure logic (no DB/HTTP)."""
from datetime import date

from services.dashboard import (
    build_dashboard_data,
    calculate_progress,
    parse_due_date,
    status_from_progress,
)


class TestProgress:
    def test_empty(self):
        assert calculate_progress([]) == 0

    def test_half(self):
        tasks = [{"completed": True}, {"completed": False}]
        assert calculate_progress(tasks) == 50

    def test_full(self):
        assert calculate_progress([{"completed": True}]) == 100


class TestStatusFromProgress:
    def test_not_started(self):
        assert status_from_progress(0) == "Не начата"

    def test_in_progress(self):
        assert status_from_progress(50) == "В процессе"

    def test_done(self):
        assert status_from_progress(100) == "Завершена"


class TestParseDueDate:
    def test_iso(self):
        assert parse_due_date("2026-06-02") == date(2026, 6, 2)

    def test_ru(self):
        assert parse_due_date("02.06.2026") == date(2026, 6, 2)

    def test_invalid(self):
        assert parse_due_date("not-a-date") is None

    def test_empty(self):
        assert parse_due_date("") is None


class TestBuildDashboard:
    def test_overdue_and_upcoming_split(self):
        today = date(2026, 6, 2)
        situations = [{"id": "s1", "title": "Ситуация", "status": "В процессе", "progress": 0}]
        tasks = [
            {"id": "t1", "situation_id": "s1", "title": "Просрочена", "completed": False, "due_date": "2026-05-01"},
            {"id": "t2", "situation_id": "s1", "title": "Скоро", "completed": False, "due_date": "2026-06-10"},
        ]
        data = build_dashboard_data(situations, tasks, today=today)
        assert any(t["id"] == "t1" for t in data["overdue_tasks"])
        assert any(t["id"] == "t2" for t in data["upcoming_tasks"])

    def test_active_vs_completed_counts(self):
        today = date(2026, 6, 2)
        situations = [
            {"id": "s1", "title": "Активная", "status": "В процессе", "progress": 40},
            {"id": "s2", "title": "Готова", "status": "Завершена", "progress": 100},
        ]
        tasks = [
            {"id": "t1", "situation_id": "s1", "completed": False},
            {"id": "t2", "situation_id": "s2", "completed": True},
        ]
        data = build_dashboard_data(situations, tasks, today=today)
        assert data["active_count"] == 1
        assert data["completed_count"] == 1

    def test_expiring_documents(self):
        today = date(2026, 6, 2)
        documents = [{"id": "d1", "title": "Паспорт", "expiry_date": "2026-06-20"}]
        data = build_dashboard_data([], [], today=today, documents=documents, reminder_days=30)
        assert any(d["id"] == "d1" for d in data["expiring_documents"])
