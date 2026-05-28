# SETUP REPORT: Белпомощник

Дата проверки: 2026-05-13  
Рабочая папка Codex: `/Applications/XAMPP/xamppfiles/htdocs/belpomoshnik`

## Проверка окружения

| Компонент | Статус | Версия / комментарий |
| --- | --- | --- |
| Python | Найден | `python3`: Python 3.14.3 |
| `python` | Не найден | Команда `python` отсутствует, используйте `python3` |
| pip | Найден | `pip3`: pip 26.0 для Python 3.14 |
| `pip` | Не найден | Команда `pip` отсутствует, используйте `pip3` или `.venv/bin/python -m pip` |
| pip в `.venv` | Найден | pip 26.1.1 |
| Git | Найден | git version 2.51.2 |
| Node.js | Найден | v22.20.0 |
| npm | Найден | 10.9.3 |
| Flet глобально | Не найден | Команда `flet` до установки окружения отсутствовала |
| Flet в `.venv` | Установлен | Flet 0.85.0 |
| Flutter для Flet | Подготовлен Flet CLI | Flutter 3.41.7 |
| Pyodide для Flet | Подготовлен Flet CLI | Pyodide 0.27.7 |

Codex работает внутри папки проекта: да.

## Что было создано

- `.venv/`
- `assets/`
- `src/main.py`
- `src/pages/home_page.py`
- `src/pages/problems_page.py`
- `src/pages/problem_detail_page.py`
- `src/pages/situations_page.py`
- `src/pages/documents_page.py`
- `src/pages/notifications_page.py`
- `src/pages/profile_page.py`
- `src/components/app_bar.py`
- `src/components/bottom_nav.py`
- `src/components/cards.py`
- `src/components/buttons.py`
- `src/data/mock_data.py`
- `src/theme/app_theme.py`
- `requirements.txt`
- `pyproject.toml`
- `README.md`
- `.gitignore`
- `SETUP_REPORT.md`

## Установленные зависимости проекта

Зависимости установлены внутрь виртуального окружения `.venv`.

Основная зависимость:

```text
flet==0.85.0
```

При первом запуске Flet также подготовил служебные пакеты `flet-cli==0.85.0` и `flet-desktop==0.85.0`.

## Как запускать проект

Вариант с активацией окружения:

```bash
source .venv/bin/activate
flet run src/main.py
```

Вариант без активации окружения:

```bash
.venv/bin/flet run src/main.py
```

Если нужно выполнить команду именно как `flet run src/main.py`, сначала активируйте `.venv`.

## Проверка запуска

Проверка синтаксиса выполнена:

```bash
.venv/bin/python -m compileall src
```

Команда запуска проверена:

```bash
PATH="$PWD/.venv/bin:$PATH" flet run src/main.py
```

Приложение стартовало без traceback. Процесс был остановлен вручную через `Ctrl+C`, так как Flet-приложение остается запущенным до ручной остановки.

## Что есть в приложении

- светлая тема;
- белый фон;
- синие и зеленые акценты;
- карточки со скруглением;
- крупный читаемый текст;
- нижняя навигация;
- моковые данные для проблем, документов, ситуаций и уведомлений;
- экраны: Главная, Проблемы, Карточка проблемы, Мои ситуации, Документы, Уведомления, Профиль.

## Что нужно дополнительно для Android

Для будущей сборки и тестирования под Android нужно установить вручную:

- Android Studio;
- Android SDK;
- Android SDK Command-line Tools;
- Android Platform Tools;
- Android Emulator или физическое Android-устройство;
- JDK, если его не установит Android Studio;
- принять Android SDK licenses.

После подготовки Android-окружения можно будет проверять сборку через инструменты Flet.

## Что нужно дополнительно для iOS

Для будущей сборки и тестирования под iOS нужно вручную подготовить:

- macOS с установленным Xcode;
- Xcode Command Line Tools;
- iOS Simulator или физическое iPhone-устройство;
- Apple Developer Account для установки на устройство и публикации;
- CocoaPods, если он потребуется для iOS-сборки.

## Ограничения текущего этапа

- backend не добавлялся;
- база данных не добавлялась;
- PostgreSQL не добавлялся;
- Express не добавлялся;
- авторизация не добавлялась;
- данные пока моковые и лежат в `src/data/mock_data.py`.

