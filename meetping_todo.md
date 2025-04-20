# ✅ TODO: Полноценный MVP Telegram-бота "MeetPing"

## Архитектура
- Использовать язык **Go**
- Хранение данных — **SQLite** с миграциями
- Бот работает через **long polling**
- Поддержка **одновременного запуска двух ботов** (`cmd/bot_original`, `cmd/bot_test`)
- Использовать **структуру проекта** с разделением:
  - `cmd/` — entrypoints
  - `internal/service/`, `repository/`, `infra/`, `scheduler/`, `bot/`

## Миграции (init.sql)
Создать таблицы:
- `users (telegram_id, username, plan)`
- `events (title, description, datetime, city_id, link, message_id)`
- `cities (name, active)`
- `user_cities (user_id, city_id, is_primary)`
- `interests`, `user_interests`
- `hobbies`, `user_hobbies`
- `likes (user_id, event_id)`
- `rsvps (user_id, event_id)`
- `event_feedback (user_id, event_id, text)`
- `user_actions (user_id, action, meta)`

## Digest
- Формировать дайджест в зависимости от интересов, хобби, городов
- Сортировка: сначала события из основного города, затем из других
- Каждое событие имеет **score**: `likes + 1.8*rsvp + 0.6*fakes`
- Включить inline-кнопки:
  - ❤️ лайк
  - 🚶 "я иду"
- При нажатии "я иду" автоматически ставится ❤️
- Повторное нажатие — снимает действие (undo)

## Настройки пользователя (через Telegram-меню)
- Меню команд `/start`, `ShowMenu(...)`
- Показывать:
  - выбранный город 🏙
  - интересы 🎯
  - время рассылки ⏰
- Встроенные настройки:
  - изменить интересы, удалить интерес
  - изменить хобби, удалить хобби
  - выбрать несколько городов, отметить основной
  - выбрать время получения дайджеста: утром 🌅, днем ☀️, вечером 🌇
- Все действия — через **inline-кнопки без команд**

## Служебные функции
- Напоминание за 30 мин до начала мероприятия (cron)
- Повторная отправка дайджеста по кнопке
- Сбор фидбэка после мероприятия (через cron)
- Fake activity:
  - Подкручивать лайки/RSVP случайно
  - Минимум 1–10 лайков, 0–1 RSVP при вставке события
  - Каждые 5–10 минут в фоне — новые фейковые лайки/going

## CLI (`meetctl`)
- `export:csv <table>` — экспорт любой таблицы в CSV
- `backup` — архивирует папки `logs/` и `data/` в zip
- `adminstats` — вывести общее количество:
  - пользователей, событий, действий
  - топ-мероприятий по лайкам и RSVP

## Cron / Scheduler
- Ежедневная рассылка дайджестов (по времени пользователя)
- Ежедневный `backup` с отправкой архивов админу в Telegram
- `fake_activity` каждые 5–10 минут

## Админ
- Поддержка команды `/adminstats` только для `@stansob`
- Виден:
  - список активных пользователей
  - статистика лайков, RSVP
  - активность по интересам, городам

## Логика
- Все действия логируются в `user_actions`
- `feedback` хранится в `event_feedback`
- Все методы вынести в `repository.go` (DB: saveEvent, toggleLike, RSVP, feedback, interests, cities)
- Использовать `zap` + `lumberjack` для логирования
- Файл `.env.example` с переменными (`BOT_TOKEN`, `LOG_FILE`)

## Инфраструктура
- `Makefile` с командами `run`, `build`
- `Dockerfile`
- `docker-compose.yml`
- Поддержка webhook опциональна, по умолчанию polling
- Старт бота через `main.go`

## Финал
- Добавить:
  - `README.md`
  - `DEPLOY.md` (Fly.io, Railway, локальный запуск)
  - `CHANGELOG.md` (список всех фич MVP)
