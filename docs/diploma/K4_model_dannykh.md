# K4. Модель данных

## 4.1 ER-диаграмма (текстовое представление)

```
roles ──< users >── refresh_tokens
              │
              └──< user_documents

problems ──< scenarios >── scenario_stages >── scenario_steps
                  │                                   │
                  ├──< scenario_dependencies           ├── authority_id → authorities
                  ├──< related_scenarios               ├── deadline_id  → deadlines
                  └──< law_updates                     ├──< step_documents >── documents
                                                        └──< notification_rules

scenarios / stages / steps >── source_references

email_notifications ── user_id? → users
audit_logs ── user_id? → users
```

## 4.2 Таблицы и поля

### `problems`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| slug | VARCHAR UNIQUE | URL-идентификатор (`family`, `work`) |
| title | VARCHAR | Название проблемы |
| description | TEXT | Описание |
| icon | VARCHAR | Иконка (emoji или имя иконки) |
| category | VARCHAR | Категория |
| difficulty | VARCHAR | Сложность: easy / medium / hard |
| is_published | BOOLEAN | Опубликована ли |
| created_at, updated_at | TIMESTAMP | |

### `scenarios`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| problem_id | UUID FK → problems | |
| slug | VARCHAR UNIQUE | URL-идентификатор |
| title | VARCHAR | Название сценария |
| description | TEXT | |
| category | VARCHAR | |
| icon | VARCHAR | |
| difficulty | VARCHAR | easy / medium / hard |
| estimated_time | VARCHAR | Ориентировочное время («2–3 недели») |
| tags | TEXT | JSON-список тегов |
| required_documents | TEXT | JSON-список |
| is_published | BOOLEAN | |
| last_checked | DATE | Дата последней проверки источников |
| created_at, updated_at | TIMESTAMP | |

### `scenario_stages`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| scenario_id | UUID FK → scenarios | |
| title | VARCHAR | |
| description | TEXT | |
| order_index | INTEGER | Порядок отображения |
| created_at, updated_at | TIMESTAMP | |

### `scenario_steps`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| stage_id | UUID FK → scenario_stages | |
| title | VARCHAR | |
| description | TEXT | |
| order_index | INTEGER | |
| is_required | BOOLEAN | |
| authority_id | UUID FK → authorities nullable | |
| deadline_id | UUID FK → deadlines nullable | |
| step_type | VARCHAR | action / info / document / payment |
| source_url | VARCHAR | Ссылка на официальный источник |
| created_at, updated_at | TIMESTAMP | |

### `authorities`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| name | VARCHAR | Название учреждения |
| address | VARCHAR | |
| phone | VARCHAR | |
| website | VARCHAR | |
| working_hours | VARCHAR | |
| district | VARCHAR | Район/город |
| created_at, updated_at | TIMESTAMP | |

### `deadlines`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| label | VARCHAR | Описание срока |
| days | INTEGER nullable | Кол-во дней |
| date | DATE nullable | Конкретная дата |
| is_hard | BOOLEAN | Жёсткий срок (нельзя пропустить) |
| created_at, updated_at | TIMESTAMP | |

### `documents`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| title | VARCHAR | Название документа |
| description | TEXT | |
| is_template | BOOLEAN | Шаблон для скачивания |
| download_url | VARCHAR nullable | |
| created_at, updated_at | TIMESTAMP | |

### `step_documents` (M2M)
| Поле | Тип |
|------|-----|
| step_id | UUID FK |
| document_id | UUID FK |
| created_at | TIMESTAMP |

### `notification_rules`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| step_id | UUID FK → scenario_steps | |
| trigger_type | VARCHAR | deadline_before / status_change |
| days_before | INTEGER nullable | |
| message | TEXT | |
| created_at, updated_at | TIMESTAMP | |

### `scenario_dependencies`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| scenario_id | UUID FK → scenarios | |
| step_id | UUID FK → scenario_steps | Зависимый шаг |
| depends_on_step_id | UUID FK → scenario_steps | Предпосылка |
| created_at, updated_at | TIMESTAMP | |

### `related_scenarios`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| scenario_id | UUID FK → scenarios | |
| related_scenario_id | UUID FK → scenarios | |
| relation_type | VARCHAR | related / follow_up / alternative |
| created_at, updated_at | TIMESTAMP | |

### `source_references`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| title | VARCHAR | |
| url | VARCHAR | |
| entity_type | VARCHAR | scenario / stage / step |
| entity_id | UUID | |
| last_checked_at | DATE | |
| status | VARCHAR | checked / outdated |
| created_at, updated_at | TIMESTAMP | |

### `law_updates`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| title | VARCHAR | |
| summary | TEXT | |
| details | TEXT | |
| effective_date | DATE | |
| source_url | VARCHAR | |
| category | VARCHAR | Категория профиля (taxes, family…) |
| processing_status | VARCHAR | new / reviewed / applied |
| affected_scenario_id | UUID FK nullable | |
| affected_step_id | UUID FK nullable | |
| last_source_check | DATE | |
| created_at, updated_at | TIMESTAMP | |

### `roles`
| Поле | Тип |
|------|-----|
| id | UUID PK |
| name | VARCHAR UNIQUE | user / editor / admin |

### `users`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| email | VARCHAR UNIQUE | |
| hashed_password | VARCHAR | bcrypt |
| full_name | VARCHAR | |
| phone | VARCHAR nullable | |
| district | VARCHAR nullable | |
| address | VARCHAR nullable | |
| employment_status | VARCHAR | employed / self_employed / student / pensioner / unemployed |
| has_children | BOOLEAN | |
| has_car | BOOLEAN | |
| is_home_owner | BOOLEAN | |
| is_renter | BOOLEAN | |
| role_id | UUID FK → roles | |
| is_active | BOOLEAN | |
| email_notifications | BOOLEAN | |
| doc_reminder_days | INTEGER | |
| created_at, updated_at | TIMESTAMP | |

### `refresh_tokens`
| Поле | Тип |
|------|-----|
| id | UUID PK |
| user_id | UUID FK → users CASCADE |
| token_hash | VARCHAR UNIQUE |
| expires_at | TIMESTAMP |
| created_at | TIMESTAMP |

### `user_documents`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| user_id | UUID FK → users CASCADE | |
| title | VARCHAR | |
| doc_type | VARCHAR | passport / insurance / license… |
| expiry_date | DATE nullable | |
| issue_date | DATE nullable | |
| notes | TEXT | |
| file_path | VARCHAR nullable | Путь к загруженному файлу |
| is_masked | BOOLEAN | Скрыть детали (конфиденциальный) |
| created_at, updated_at | TIMESTAMP | |

### `email_notifications`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| user_id | UUID FK → users nullable | |
| recipient_email | VARCHAR | |
| subject | VARCHAR | |
| body | TEXT | |
| notification_type | VARCHAR | doc_expiry / tax_deadline / law_update |
| status | VARCHAR | pending / sent / failed / skipped_limit |
| error_message | TEXT nullable | |
| scheduled_at | TIMESTAMP | |
| sent_at | TIMESTAMP nullable | |
| created_at | TIMESTAMP | |

### `audit_logs`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| user_id | UUID FK nullable | |
| action | VARCHAR | created_scenario / deleted_step / published_law_update… |
| entity_type | VARCHAR | scenario / step / law_update / user… |
| entity_id | UUID nullable | |
| details | TEXT | JSON-детали |
| ip_address | VARCHAR nullable | |
| created_at, updated_at | TIMESTAMP | |

## 4.3 Индексы

```sql
CREATE INDEX ix_scenarios_problem_id   ON scenarios(problem_id);
CREATE INDEX ix_stages_scenario_id     ON scenario_stages(scenario_id);
CREATE INDEX ix_steps_stage_id         ON scenario_steps(stage_id);
CREATE INDEX ix_law_updates_category   ON law_updates(category);
CREATE INDEX ix_email_notif_user_status ON email_notifications(user_id, status);
CREATE INDEX ix_email_notif_scheduled  ON email_notifications(scheduled_at);
CREATE INDEX ix_audit_logs_user_id     ON audit_logs(user_id);
CREATE INDEX ix_audit_logs_entity      ON audit_logs(entity_type, entity_id);
```

## 4.4 Локальное состояние (клиент)

В MVP клиент хранит копию данных в `data/app_state.json`. Ключи:

| Ключ | Тип | Описание |
|------|-----|----------|
| `auth_state` | dict | Статус авторизации, email |
| `app_user` | dict | Профиль пользователя |
| `app_settings` | dict | Настройки (тема, уведомления, large_text) |
| `personal_documents` | list | Личные документы |
| `situations` | list | Запущенные ситуации |
| `situation_tasks` | list | Задачи по ситуациям |
| `notifications` | list | Уведомления |
| `law_updates` | list | Закон-апдейты (кеш) |
| `utility_accounts` | list | ЖКХ-аккаунты |
| `utility_payments` | list | ЖКХ-платежи |
| `tax_obligations` | list | Налоговые обязательства |
| `user_activity_log` | list | Журнал действий пользователя |
| `admin_audit_logs` | list | Журнал действий редактора |
