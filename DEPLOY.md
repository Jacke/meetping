# MeetPing: Инструкция по деплойменту

## 1. Подготовка

- Создай бота через @BotFather
- Получи токен и заполни `.env`

## 2. Fly.io

```bash
flyctl launch
flyctl secrets set BOT_TOKEN=xxx
flyctl deploy
```

## 3. Railway (через Git)

- Залей код в GitHub
- Подключи Railway
- Установи переменные окружения (`BOT_TOKEN`, `LOG_FILE`)
- Нажми Deploy

## 4. Локальный запуск

```bash
go run cmd/bot_original/main.go
```

---

## Файлы

- `.env.example` — шаблон
- `Makefile` — команды запуска
- `Dockerfile` — build и run
- `docker-compose.yml` — 2 бота: основной и тест
