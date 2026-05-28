# K8. Скриншоты web-версии

> Скриншоты сделаны при запуске `flet run -w src/main.py --host 127.0.0.1 -p 8550` в браузере Chrome.  
> Разрешение: 1440×900 (desktop breakpoint > 900px).

---

## Инструкция для получения скриншотов

1. Запустить приложение:
   ```bash
   cd /Applications/XAMPP/xamppfiles/htdocs/belpomoshnik
   source .venv/bin/activate
   flet run -w src/main.py --host 127.0.0.1 -p 8550
   ```
2. Открыть в браузере: `http://127.0.0.1:8550`
3. Использовать DevTools → режим «Responsive» для эмуляции разрешений.

---

## Перечень экранов для скриншотов

| # | Экран | Маршрут | Файл скриншота |
|---|-------|---------|---------------|
| 01 | Приветственный экран (Onboarding) | `/onboarding` | `01-onboarding-desktop-light.png` |
| 02 | Вход в систему | `/login` | `02-login-desktop-light.png` |
| 03 | Главная — дашборд | `/` | `03-home-desktop-light.png` |
| 04 | Главная — тёмная тема | `/` | `04-home-desktop-dark.png` |
| 05 | Глобальный поиск | `/search` | `05-search-desktop-light.png` |
| 06 | Каталог проблем | `/problems` | `06-problems-desktop-light.png` |
| 07 | Карточка проблемы | `/problems/family` | `07-problem-detail-desktop-light.png` |
| 08 | Сценарий — Рождение ребёнка | `/scenarios/childbirth` | `08-scenario-childbirth-desktop.png` |
| 09 | Мои ситуации | `/situations` | `09-situations-desktop-light.png` |
| 10 | Детальная страница ситуации | `/situations/{id}` | `10-situation-detail-desktop.png` |
| 11 | Документы | `/documents` | `11-documents-desktop-light.png` |
| 12 | Профиль | `/profile` | `12-profile-desktop-light.png` |
| 13 | Уведомления | `/notifications` | `13-notifications-desktop-light.png` |
| 14 | Закон-апдейты | `/legal-updates` | `14-legal-updates-desktop-light.png` |
| 15 | Предпросмотр email | `/email-preview` | `15-email-preview-desktop.png` |
| 16 | Трекер ЖКХ | `/utility` | `16-utility-tracker-desktop.png` |
| 17 | Трекер налогов | `/taxes` | `17-tax-tracker-desktop.png` |
| 18 | Административная панель — сценарии | `/admin` | `18-admin-scenarios-desktop.png` |
| 19 | Административная панель — шаги | `/admin` (вкладка шагов) | `19-admin-steps-desktop.png` |
| 20 | Аудит журнал | `/admin` (вкладка аудита) | `20-admin-audit-desktop.png` |

---

## Хранение скриншотов

Скриншоты размещаются в: `docs/redesign-progress/`

Уже имеющиеся скриншоты редизайна (шаги 01–04): см. `docs/redesign-progress/`.

---

> **Примечание:** Для финальной версии дипломной работы рекомендуется сделать скриншоты после завершения редизайна (Шаги 0–20 из `PLAN-REDESIGN.md`).
