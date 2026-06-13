# EXECUTION PLAN — rework-промпты 1–10 (последовательно)

Идём по промптам строго по порядку: 1 → 2 → 3 → ... → 10. Каждый довожу до конца, что не успеется — оставляем как TODO.

Полный план: `~/.claude/plans/twinkling-noodling-petal.md`.

## Промпт 1 — Шифрование «Моих документов» + demo seed

### Backend
- [x] `src/backend/security/document_crypto.py` — Fernet, ключ из `BELPOMOSHNIK_DOCUMENT_MASTER_KEY`
- [x] Миграция `0021_document_encryption.sql` — `*_encrypted` колонки, scan metadata
- [x] `models.py` — поля `number_encrypted`, `issued_by_encrypted`, `comment_encrypted`, `custom_fields_encrypted`, `scan_encrypted_path`, `scan_original_filename`, `scan_mime_type`, `scan_size`, `scan_uploaded_at`
- [x] `api/user.py` — `_doc_to_out` (расшифровка), `_apply_doc_payload` (шифрование), новые scan endpoints с magic-bytes detection, StreamingResponse расшифрованного blob
- [x] `app.py` — убрать static-mount `/uploads/documents`
- [x] Encryption-aware `delete_document` и `_wipe_scan_files`
- [ ] `.env.example` обновлён + команда генерации ключа
- [ ] `scripts/seed_demo_personal_data.py` — idempotent demo docs для всех users, фейковый PDF-скан

### Frontend
- [x] `types.ts` — `scan` metadata, `encryptedAtRest`
- [x] `adapters.ts` — adapt `scan`
- [x] `services/api.ts` — `downloadDocumentScan` через fetch+Blob (Authorization header)
- [x] `store.tsx` — `refreshDocuments` + интеграция в DocumentCardModal
- [x] `DocumentCardModal` — preview через ObjectURL, кнопки Скачать/Удалить, поддержка PDF и img, lock-бейдж
- [x] `pages.tsx` — `onEditDoc(id)` flow вместо общего `onAddDoc()`
- [x] Bug-fix: `valueFor` TDZ в `DocumentEditModal` (Cannot access 'valueFor' before initialization)

### Docs (срезаны до минимума по решению пользователя)
- [x] Frontend проверен в browser preview — модалка/редактор работают

---

## Промпт 2 — ЖКХ и налоги — ✅ завершён
## Промпт 3 — Backend AI — ✅ завершён
## Промпт 4 — Frontend AI помощника citizen — ✅ завершён
## Промпт 5 — Редакторский AI — ✅ завершён
## Промпт 6 — Уведомления — ✅ завершён

- [x] in-app центр, `route`, `dedupe_key`
- [x] backend rules/service/delivery и scheduler
- [x] native push token endpoints и безопасное хранение
- [x] Capacitor Local Notifications + Push Notifications
- [x] desktop browser Notification API
- [x] UI способов доставки, типов и тестового уведомления
- [x] тесты и архитектурная документация
## Промпт 7 — Админ-панель — ✅ основной блок завершён

- [x] Защищены endpoints управления пользователями: только `platform_admin`.
- [x] Добавлен `/api/admin/dashboard/stats` с реальными KPI.
- [x] Добавлены фильтры пользователей, проблем, сценариев и audit log.
- [x] Добавлена проверка целостности сценария `/api/admin/scenarios/{id}/integrity`.
- [x] Удаление пользователя переведено в soft-delete + отзыв refresh-токенов.
- [x] Добавлены админ-действия: отзыв сессий и системное уведомление пользователю.
- [x] Расширены `users` и `audit_logs`; вход редактора/админа логируется.
- [x] React-админка получила раздел «Проблемы», реальные KPI, расширенную таблицу пользователей и фильтры.
- [x] Добавлены tests: `test_admin_users.py`, `test_admin_content.py`, `test_security_fixes.py`.
- [x] Обновлены API/security/status/changelog/demo docs.
- [ ] Дальнейший крупный распил монолитной `AdminPanel` на отдельные компоненты оставить на финальную UI-стабилизацию, чтобы не ломать текущую рабочую админку.
## Промпт 8 — Регионы и города — ✅ frontend/store блок завершён

- [x] Desktop split layout: карта слева, список/инспектор справа.
- [x] Mobile bottom sheet сохранён без desktop-overlay.
- [x] `GeoRegion` расширен координатами карточек, displayName, active/visible state и timestamps.
- [x] Новые регионы получают fallback-позицию, переименование не сбрасывает координаты.
- [x] Добавлен режим «Расположение» с pointer drag и сохранением x/y в процентах.
- [x] Добавлен список активных и архивных регионов.
- [x] Удаление заменено архивированием на frontend/store-уровне.
- [x] Проверка без тестов: `pnpm -C reactvitemaket run build`, `.venv/bin/python -m compileall -q src`.
- [ ] Backend API `/api/admin/regions/*` и отдельная таблица регионов остаются будущим инфраструктурным шагом.
## Промпт 9 — Финальная стабилизация
## Промпт 10 — Control Center

Подпункты заполняются перед стартом каждого промпта, чтобы не забивать файл преждевременно.
