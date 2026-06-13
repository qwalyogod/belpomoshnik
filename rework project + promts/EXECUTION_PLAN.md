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

## Промпт 2 — ЖКХ и налоги
(пойдём после промпта 1)

## Промпт 3 — Backend AI
## Промпт 4 — Frontend AI помощника citizen
## Промпт 5 — Редакторский AI
## Промпт 6 — Уведомления
## Промпт 7 — Админ-панель
## Промпт 8 — Регионы и города
## Промпт 9 — Финальная стабилизация
## Промпт 10 — Control Center

Подпункты заполняются перед стартом каждого промпта, чтобы не забивать файл преждевременно.
