# Live-reload на iPhone (Capacitor + Vite HMR)

## Зачем

Стандартный Capacitor APK содержит встроенный JS-бандл (`dist/`). Чтобы увидеть изменения в React, нужно каждый раз:
1. `pnpm build`
2. `npx cap sync android`
3. Переустановить APK на устройстве

Live-reload убирает шаги 1-3 между итерациями: APK при старте **тянет JS с Vite dev-сервера на вашем Mac**, Vite HMR обновляет компоненты **мгновенно в WebView**. Достаточно один раз установить специальный APK с включённым live-reload.

## Подготовка (один раз)

### 1. Узнать LAN-IP вашего Mac

```bash
# Должно вывести что-то вроде 192.168.1.42 или 172.20.10.3
ipconfig getifaddr en0
```

### 2. Создать `capacitor.config.local.json` (НЕ коммитить)

```bash
cd reactvitemaket
cp capacitor.config.json capacitor.config.local.json
```

В `capacitor.config.local.json` добавить блок `server.url`:

```json
{
  "appId": "by.belpomoshnik.app",
  "appName": "Белпомощник",
  "webDir": "dist",
  "server": {
    "url": "http://172.20.10.3:8560",
    "cleartext": true,
    "allowNavigation": ["172.20.*.*", "10.*.*.*", "192.168.*.*", "localhost"]
  }
}
```

⚠️ Замените `172.20.10.3` на **ваш** LAN-IP. Порт `8560` — Vite dev-сервер (см. `vite.config.ts`).

### 3. Добавить в `.gitignore`:

```bash
echo "reactvitemaket/capacitor.config.local.json" >> .gitignore
```

### 4. Собрать и установить APK с live-reload

```bash
cd reactvitemaket

# Сборка (нужна для gradlew, но JS-бандл не используется — APK будет тянуть с dev-сервера)
pnpm build

# Sync с локальным конфигом
npx cap sync android --config capacitor.config.local.json

# Сборка APK
cd android
./gradlew assembleDebug

# APK появится в android/app/build/outputs/apk/debug/app-debug.apk
# Установите его на iPhone (через Xcode → Devices and Simulators → iPhone → drag-and-drop APK
# или через `ideviceinstaller -i app-debug.apk` если у вас libimobiledevice)
```

### 5. Запустить Vite dev-сервер

```bash
cd /Applications/XAMPP/xamppfiles/htdocs/belpomoshnik
pnpm dev:all
# или только frontend: cd reactvitemaket && pnpm dev:lan
```

### 6. Запустить APK на iPhone

- **iPhone и Mac — в одной Wi-Fi сети**
- Откройте приложение «Белпомощник»
- WebView загрузит JS с `http://<LAN-IP>:8560` — увидите обычный UI

## Workflow

1. Меняете код React в `reactvitemaket/src/`
2. Vite пересобирает модуль за ~100-300ms
3. WebView получает HMR-обновление **без перезагрузки страницы**
4. Видите изменения мгновенно
5. **Никакой переустановки APK не нужно**, пока конфиг не меняется

Если HMR «застрял» — shake iPhone (или в DevTools Safari → Web Inspector → Reload). Полная переустановка APK нужна только если:
- Добавили новый `@capacitor/*` плагин
- Изменили `capacitor.config.json`
- Поменяли `Info.plist` или `AndroidManifest.xml`

## Возврат к prod-режиму (без live-reload)

Просто уберите/переименуйте `capacitor.config.local.json` и пересоберите:

```bash
mv capacitor.config.local.json capacitor.config.local.json.bak
cd android && ./gradlew assembleDebug
```

APK снова будет работать автономно со встроенным JS-бандлом — никаких зависимостей от dev-сервера.

## Устранение неполадок

### Белый экран при открытии APK

- `pnpm dev:lan` запущен? Vite слушает `0.0.0.0:8560` (на `--host`)?
- С iPhone в Safari: `http://<LAN-IP>:8560` — открывается? Если нет, **macOS Firewall** блокирует.
  Системные настройки → Сеть → Брандмауэр → Параметры → разрешить `node` / `python3`.
- Правильный IP в `capacitor.config.local.json`? Перезапустите `cap sync` после правки.

### Вижу старый UI, изменения не применяются

- Встряхните iPhone → Reload. Или закройте-откройте приложение.
- Web Inspector (Настройки → Safari → Дополнения → Web Inspector = ON, Mac Safari → Develop → iPhone → приложение): в Console ищите ошибки HMR.

### APK установился, но при запуске выкидывает в ServerPicker

- Это нормально при первом запуске с `server.url`. ServerPicker покажет `http://<LAN-IP>:8560` — тапните.
- В ServerPicker есть автоматический probe через `/api/health` — если `pnpm dev:all` запущен, бэк ответит OK, и карточка подсветится зелёным.
