# MeetPing

**MeetPing** — Telegram-бот для рассылки событий и поиска единомышленников.  
Поддерживает интересы, хобби, города, лайки, RSVP, дайджесты, напоминания, аналитику, CLI, backup.

## Команды

- `/start` — запуск бота
- inline кнопки `❤️` и `🚶` — лайк / я иду / отмена
- админ: `/adminstats`

## Структура

- `cmd/bot_original/`, `cmd/bot_test/` — точки входа
- `internal/service/` — бизнес-логика (digest, rsvp, fsm и др.)
- `internal/repository/` — доступ к SQLite
- `scheduler/` — фоновая активность, фейковые лайки, backup
- `meetctl` — CLI-команды

## CLI

```bash
go run cmd/meetctl/main.go export:csv users
go run cmd/meetctl/main.go backup
```

## Бэкапы и логи

- `logs/` — логи и фидбэк
- `data/` — SQLite база
- backup: `meetctl backup` или автоматом по cron

---

## Используемые технологии

- Golang, SQLite, cron, zap logger
- Telegram API (go-telegram-bot-api)
