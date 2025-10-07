# Архив и описание логики Go-кода (MeetPing)

Ниже собрана структурированная документация по логике удаляемых Go-файлов. Описание организовано по пакетам/директориям и командам (`cmd/*`). Это позволит восстановить архитектуру и поведение системы без чтения исходников.

---

## Точка входа

- `main.go`
  - Загружает `.env`, стартует бота через `bot.Start()` (в актуальной схеме используется `cmd/bot/main.go`).

- `cmd/bot/main.go`
  - Загружает конфиг (`internal/config.Load`), печатает баннер, инициализирует логгер (`internal/logger.New`).
  - Настраивает Goose для миграций SQLite, открывает БД (`internal/db.InitDB`), применяет миграции `migrations/`.
  - Собирает репозиторий `internal/repo.NewRepository`, сервис дайджестов `internal/service.NewDigestService` и обработчик `internal/bot.NewHandler`.
  - Инициализирует Telegram Bot API, логирует аккаунт.
  - Запускает фоновые задачи `internal/scheduler.CronJobs.Start()`, прокидывая функцию `BotSend` для рассылки сообщений пользователям.
  - Включает режим webhook или long polling по `USE_WEBHOOK`. В цикле обрабатывает апдейты через `handler.HandleUpdate` и обеспечивает graceful shutdown по сигналу.

- `cmd/bot_original/main.go`, `cmd/bot_test/main.go`
  - Облегчённые точки входа, вызывают `bot.Run(token, label)` с токеном из окружения.

- `cmd/meetctl/*`
  - `main.go`: CLI-утилита: `backup` (zip-файл с БД и логами), `export:csv` (выгрузка таблицы в CSV), `adminstats` (сводка по БД), `trigger` (вызов произвольной задачи).
  - `backup.go`: реализация `CreateBackup(outputPath)` — архивирует содержимое `data/` и `logs/` в ZIP.
  - `export.go`: `ExportCSV(db, table)` — пишет CSV в stdout.
  - `adminstats.go`: читает SQLite и печатает агрегаты по таблицам.

---

## Конфигурация и инфраструктура

- `internal/config/config.go`
  - Загружает переменные окружения (`TELEGRAM_TOKEN`, `DATABASE_URL`, `BOT_TOKEN`, `LOG_FILE`, `ADMIN_ID`, `ENV`). Проверяет обязательные поля, предоставляет `Config`.

- `internal/logger/logger.go`
  - Два варианта инициализации логгера на базе `zap`: комбинированный вывод (консоль debug+ и файл info+) с ротацией через `lumberjack`; и упрощённый `InitLogger`.

- `internal/db/db.go`
  - `InitDB(dsn string)` — открывает SQLite, включает `PRAGMA foreign_keys = ON`.

- `internal/infra/infra.go`
  - Пустой заглушечный файл для будущей инфраструктуры.

---

## Доменная модель и репозиторий (SQLite)

- `internal/repo/models.go`
  - Структуры: `User`, `Event`, `Feedback`, `Action`.

- `internal/repo/repository.go`
  - Хранилище `Repository{DB *sql.DB}` и фабрика `NewRepository`.
  - Пользователи: `SaveUser` (upsert по `telegram_id`), `GetUserByTelegramID`.
  - Взаимодействия: `ToggleLike` (вставка/удаление), `ToggleRSVP` (транзакция: RSVP и гарантированный like).
  - Обратная связь: `SaveFeedback`.
  - События: `SaveEvent` (upsert с логами), `GetEventByID`.
  - Журнал действий: `LogUserAction`.
  - Выборки: `GetUsersByDigestTime`, `InsertFakeScore` (в таблицу `event_score_fake`), `GetPrimaryCityID`, `GetActiveEvents`, `GetUpcomingRSVPs`, `GetPastRSVPsWithoutFeedback`, `GetUserByID`.
  - Настройки пользователя: `EnsureCity`, `SetPrimaryCity`, `EnsureInterest`, `SetUserInterests`, `GetPrimaryCityName`, `GetUserInterestNames`.

- `internal/repository/*`
  - Альтернативная/историческая реализация репозитория и инициализации БД, операции лайков/RSVP, интересов и городов; утилита `LogUserAction`. Присутствует дублирование с `internal/repo/*` (вероятно, эволюционный слой).

---

## Сервисный слой

- `internal/service/digest.go`
  - `DigestService` с `GetDigestForUser(userID, cityID)` — собирает события пользователя по городу, джойнит лайки/RSVP/фейковые бусты и рассчитывает метрику релевантности `Score` через `CalculateScore(likes, rsvps, fake)`.
  - `BuildDigest(events, city)` — форматирует текст дайджеста.

- `internal/service/score.go`
  - Простая формула рейтинга событий: `likes + 2*rsvps + fake`.

- `internal/service/handler.go`
  - Базовый обработчик команд `/start` и неизвестных команд (ответы в чат).

- `internal/service/fsm/fsm.go`
  - Лёгкая FSM для хранения состояния пользователя: `start`, `interest`, `city` с потокобезопасным доступом.

- `internal/service/interests/interests.go`
  - ИнMemory-хранилище интересов пользователей с добавлением/удалением и выборкой.

- `internal/service/likes/likes.go`, `internal/service/rsvp/rsvp.go`
  - ИнMemory-реализация лайков и RSVP по `userID -> eventID` с атомарными переключателями.

- `internal/service/interaction/*`
  - `handler.go`: обработка callback-дат из инлайн-кнопок: like/going/repeat_digest, связывает лайки и RSVP, триггерит повторную отправку дайджеста.
  - `inline.go`: построение инлайн-клавиатуры для событий.
  - `interest_menu.go`: построение меню интересов с inline-кнопками.

- `internal/service/digest/*`
  - `digest.go`: отправка короткого текстового дайджеста сообщением.
  - `repeat.go`: повторная отправка дайджеста по запросу.
  - `scoring.go`: альтернативные структуры и функции скоринга (в т.ч. имитация фейковой активности).

- `internal/service/admin/stats.go`
  - Утилита для генерации текстовой статистики (демо-значения).

---

## Слой бота (`internal/bot`)

- `fsm.go`
  - Потокобезопасная FSM: `Set/Get/Clear` состояния по `chatID`.

- `handler.go`
  - `BotHandler{Repo, FSM, Log}`; маршрутизация апдейтов: команды, callback, обычные сообщения.
  - Команды: `/start`, `/menu`, `/edit_city`, `/edit_interests`, `/edit_time` — изменяют состояние FSM и/или отправляют меню.
  - `showMenu` — сборка сообщения с текущими настройками пользователя (город, интересы, время дайджеста) и инлайн-кнопками.
  - Callback: `like`, `rsvp`, `edit_*` (переключение состояний), `show_sample_digest` — подмена клавиатуры, обновление меню, сохранение лайков/RSVP через репозиторий.

- `runner.go`
  - `Run(token, label)` — инициализация зависимостей (конфиг, логгер, БД, репозиторий, сервис дайджестов), запуск планировщика, выбор webhook/polling, цикл обработки апдейтов.

- `bot.go`
  - Старая/закомментированная версия `Start()` — исторический артефакт.

---

## Планировщик (`internal/scheduler`)

- `scheduler.go`
  - `CronJobs{Repo, Digests, BotSend}` и `Start()` — запускает горутины:
    - `runDigestLoop` — каждую минуту находит пользователей по их `digest_time`, собирает дайджест и отправляет.
    - `runFakeActivity` — раз в 5 минут добавляет «фейковые» очки событиям.
    - `runReminders` — каждые 5 минут ищет ближайшие RSVP и шлёт напоминания за 30 минут до начала.
    - `runFeedbackRequests` — каждые 10 минут просит фидбэк по завершённым событиям.

- `cron.go`
  - Инициализатор `robfig/cron`: каждые 5 минут имитирует активность; раз в день шлёт бэкап администратору.

- `backup.go`
  - `DailyBackupToAdmin(bot)` — создаёт ZIP-бэкап и отправляет администратору как документ, `createBackup` — заглушка (предполагается вызов CLI `CreateBackup`).

- `reminder.go`
  - Вспомогательная утилита `SendReminders` для напоминаний по списку событий (примерная логика).

- `fake_activity.go`
  - Логирует имитацию активности (рандомные лайки/going) — демонстрация.

---

## Поведение в чате (high-level)

1. Пользователь пишет боту — команды обрабатываются через `BotHandler.handleCommand`, состояния диалогов — через FSM; меню позволяет редактировать город/интересы/время.
2. Инлайн-кнопки генерируют callback-данные, которые обрабатываются `handleCallback`: лайки/RSVP, редактирование настроек, просмотр примера дайджеста.
3. Периодически планировщик формирует персональные дайджесты и отправляет их, шлёт напоминания и запросы фидбэка.
4. Все персистентные изменения (профили, события, лайки/RSVP, интересы) проходят через `internal/repo.Repository` (SQLite).

---

## Заметки по архитектуре

- Используется стандартая библиотека Go и сторонние пакеты: `go-telegram-bot-api`, `zap`, `lumberjack`, `goose`, `robfig/cron`, `mattn/go-sqlite3`.
- Существуют параллельные «исторические» части (`internal/repository/*`, `internal/service/digest/*`), которые частично дублируют функциональность — при восстановлении желательно унифицировать.
- FSM реализована дважды: лёгкая по `chatID` в `internal/bot` и по `userID` в `internal/service/fsm` — следует выбрать одну.

---

Далее можно безопасно удалить исходные `.go` файлы, так как логика заархивирована в этом документе.
