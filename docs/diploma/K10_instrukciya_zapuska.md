# K10. Инструкция запуска

## Требования к окружению

| Компонент | Версия | Проверка |
|-----------|--------|---------|
| Python | 3.14+ | `python --version` |
| pip | 24+ | `pip --version` |
| Git | любая | `git --version` |
| Браузер | Chrome / Firefox | для web-режима |

> macOS: рекомендуется Homebrew-версия Python 3.14.  
> Windows: Python с официального python.org, добавить в PATH.

---

## 1. Клонирование репозитория

```bash
git clone https://github.com/<username>/belpomoshnik.git
cd belpomoshnik
```

Или, если проект уже скачан:

```bash
cd /Applications/XAMPP/xamppfiles/htdocs/belpomoshnik
```

---

## 2. Создание виртуального окружения

```bash
python3.14 -m venv .venv
```

Активация:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

---

## 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

Если файла `requirements.txt` нет — установить вручную:

```bash
pip install flet==0.85.2 fastapi uvicorn sqlalchemy pydantic passlib python-jose bcrypt
```

---

## 4. Запуск Flet-приложения (web-режим)

```bash
.venv/bin/flet run -w src/main.py --host 127.0.0.1 -p 8550
```

Открыть в браузере: **http://127.0.0.1:8550**

Для desktop-режима:

```bash
.venv/bin/flet run src/main.py
```

---

## 5. Запуск Backend API (опционально)

Backend работает независимо от UI. При запущенном backend UI переключается с mock-данных на реальный API.

```bash
PYTHONPATH=src .venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8060 --reload
```

Документация API (Swagger): **http://127.0.0.1:8060/docs**

---

## 6. Инициализация базы данных

При первом запуске backend создаёт SQLite-базу автоматически. Для применения SQL-миграций вручную:

```bash
sqlite3 belpomoshnik.db < src/backend/migrations/0001_initial.sql
sqlite3 belpomoshnik.db < src/backend/migrations/0002_auth.sql
```

---

## 7. Переменные окружения (для production-функций)

Создать файл `.env` в корне проекта:

```env
# SMTP (email-уведомления)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@belpomoshnik.by
SMTP_TLS=true

# JWT
SECRET_KEY=your_secret_key_min_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=mysql+pymysql://root:belp_root@127.0.0.1:3306/belpomoshnik?charset=utf8mb4
```

> В MVP эти переменные **не обязательны** — приложение работает без `.env`.

---

## 8. Проверка синтаксиса

```bash
.venv/bin/python -m compileall src
```

Ожидаемый результат: `(Compiled N files in ...)`, без ошибок.

---

## 9. Сброс локального состояния

Если нужно сбросить пользовательские данные к начальным:

```bash
rm data/app_state.json
```

При следующем запуске приложение пересоздаст `app_state.json` из `mock_data.py`.

---

## 10. Структура директорий после установки

```
belpomoshnik/
├── .venv/               # Виртуальное окружение
├── src/                 # Исходный код
├── data/
│   ├── app_state.json   # Локальный стейт (создаётся автоматически)
│   └── private_uploads/ # Загружаемые файлы (создаётся автоматически)
├── docs/                # Документация
└── requirements.txt     # Зависимости Python
```

---

## Устранение типичных проблем

| Проблема | Решение |
|---------|---------|
| `flet: command not found` | Использовать `.venv/bin/flet` |
| `[Errno 48] address already in use` | `lsof -ti:8550 \| xargs kill -9` |
| `ModuleNotFoundError: flet` | Активировать venv: `source .venv/bin/activate` |
| Белый экран в браузере | Подождать 2–3 сек, обновить страницу |
| Backend: `database not found` | Запустить миграции (шаг 6) |
