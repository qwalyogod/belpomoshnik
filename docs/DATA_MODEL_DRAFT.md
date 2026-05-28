# Черновик будущей модели данных

Этот документ описывает возможные будущие сущности. SQL сейчас не создается.

## users

Пользователи системы.

- id
- email или phone
- password_hash
- role
- created_at
- updated_at

## user_profile

Профиль пользователя.

- id
- user_id
- full_name
- birth_date
- city
- learning_mode_enabled
- created_at
- updated_at

## problems

Справочник жизненных проблем.

- id
- title
- category
- short_description
- content
- status
- created_at
- updated_at

## plans

Типовые планы действий для проблем.

- id
- problem_id
- title
- description
- estimated_time

## plan_steps

Шаги типового плана.

- id
- plan_id
- step_order
- title
- description
- required_documents

## saved_plans

Сохраненные планы пользователя.

- id
- user_id
- plan_id
- status
- created_at

## user_step_progress

Прогресс выполнения шагов.

- id
- saved_plan_id
- plan_step_id
- is_completed
- completed_at

## life_events_templates

Шаблоны жизненных событий.

- id
- title
- category
- description

## user_life_events

Жизненные события пользователя.

- id
- user_id
- template_id
- title
- status
- created_at

## user_tasks

Задачи пользователя.

- id
- user_id
- saved_plan_id
- title
- due_date
- status

## legal_updates

Законодательные обновления.

- id
- title
- category
- summary
- source_url
- published_at

## notifications

Уведомления пользователя.

- id
- user_id
- title
- text
- type
- is_read
- created_at

## documents

Документы пользователя или справочник документов.

- id
- user_id
- title
- description
- expires_at
- status

## learning_tests

Микро-тесты обучающего модуля.

- id
- problem_id
- category
- title

## test_questions

Вопросы тестов.

- id
- test_id
- question_text
- question_type
- order

## test_answers

Варианты ответов.

- id
- question_id
- answer_text
- is_correct
- order

## user_test_results

Результаты прохождения тестов.

- id
- user_id
- test_id
- score
- completed_at

## achievements

Справочник достижений.

- id
- title
- description
- icon
- condition_type

## user_achievements

Достижения пользователя.

- id
- user_id
- achievement_id
- earned_at

## reading_progress

Прогресс чтения материалов.

- id
- user_id
- problem_id
- progress_percent
- last_read_at

