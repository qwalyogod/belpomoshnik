# K9. Скриншоты мобильной версии

> Скриншоты демонстрируют адаптивный mobile-layout приложения.  
> Эмуляция: Chrome DevTools → iPhone 12 Pro (390×844) или Galaxy S21 (360×800).

---

## Инструкция для получения скриншотов (эмуляция в браузере)

1. Запустить приложение:
   ```bash
   flet run -w src/main.py --host 127.0.0.1 -p 8550
   ```
2. Открыть `http://127.0.0.1:8550` в Chrome.
3. Открыть DevTools (F12) → переключить на режим «Device Toolbar» (Ctrl+Shift+M).
4. Выбрать «iPhone 12 Pro» (390×844) или задать ширину 390px.
5. Ширина ≤ 900px активирует mobile-layout с нижней навигацией.

---

## Перечень экранов для скриншотов

| # | Экран | Маршрут | Файл |
|---|-------|---------|------|
| M01 | Onboarding (мобильный) | `/onboarding` | `M01-onboarding-mobile-light.png` |
| M02 | Вход (мобильный) | `/login` | `M02-login-mobile-light.png` |
| M03 | Главная (мобильный) | `/` | `M03-home-mobile-light.png` |
| M04 | Главная — тёмная тема | `/` | `M04-home-mobile-dark.png` |
| M05 | Каталог проблем | `/problems` | `M05-problems-mobile.png` |
| M06 | Сценарий (мобильный) | `/scenarios/childbirth` | `M06-scenario-mobile.png` |
| M07 | Мои ситуации | `/situations` | `M07-situations-mobile.png` |
| M08 | Задачи ситуации | `/situations/{id}` | `M08-situation-tasks-mobile.png` |
| M09 | Документы | `/documents` | `M09-documents-mobile.png` |
| M10 | Профиль | `/profile` | `M10-profile-mobile.png` |
| M11 | Уведомления | `/notifications` | `M11-notifications-mobile.png` |
| M12 | Нижняя навигация (admin) | `/admin` | `M12-admin-bottomnav-mobile.png` |

---

## Особенности mobile-layout

- **Нижняя навигация** (BottomNavigationBar): Главная / Сценарии / Ситуации / Документы / Профиль.
- **Список** вместо двухколоночного grid на desktop.
- **Меньший padding** (16px vs 24px на desktop).
- **AppBar** заменяет sidebar — логотип + кнопка «назад» + иконки действий.
- **Полная ширина** контентных карточек.

---

> **Примечание:** Нативное мобильное приложение (APK/IPA) не собирается в рамках данного MVP.  
> Mobile-layout обеспечивается адаптивной вёрсткой Flet при ширине ≤ 900px.
