package main

import (
	"meetping/internal/bot"
	"meetping/internal/config"
	"meetping/internal/db"
	"meetping/internal/logger"
	"meetping/internal/repo"
	"meetping/internal/scheduler"
	"meetping/internal/service"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/common-nighthawk/go-figure"

	"github.com/pressly/goose/v3"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
	// Load config
	cfg := config.Load()
	figure.NewFigure("MeetPing", "", true).Print()

	// Init logger
	log := logger.New()

	if err := goose.SetDialect("sqlite3"); err != nil {
		log.Fatalf("Goose dialect error: %v", err)
	}

	// Init database
	database := db.InitDB(cfg.DatabaseURL)
	if err := goose.Up(database, "./migrations"); err != nil {
		log.Fatalf("Ошибка миграции: %v", err)
	}

	repository := repo.NewRepository(database)

	// Init services
	digestService := service.NewDigestService(database)
	handler := bot.NewHandler(repository, log)

	// Init bot
	botApi, err := tgbotapi.NewBotAPI(cfg.TelegramToken)
	if err != nil {
		log.Fatal("Bot init error", err)
	}
	log.Infof("Authorized on account %s", botApi.Self.UserName)

	// Start background cron jobs
	scheduler := scheduler.CronJobs{
		Repo:    repository,
		Digests: digestService,
		BotSend: func(user repo.User, events []service.DigestItem) {
			for _, e := range events {
				msg := tgbotapi.NewMessage(user.TelegramID, "📌 "+e.Title)
				msg.ParseMode = "Markdown"
				botApi.Send(msg)
			}
		},
	}
	scheduler.Start()

	// Handle webhook or long polling
	useWebhook := os.Getenv("USE_WEBHOOK") == "1"
	var updates tgbotapi.UpdatesChannel

	if useWebhook {
		hook, _ := tgbotapi.NewWebhook("https://yourdomain.com/" + cfg.TelegramToken)
		_, err = botApi.Request(hook)
		if err != nil {
			log.Fatalf("Webhook error: %v", err)
		}
		updates = botApi.ListenForWebhook("/" + cfg.TelegramToken)
		go http.ListenAndServe(":8443", nil)
	} else {
		u := tgbotapi.NewUpdate(0)
		u.Timeout = 60
		updates = botApi.GetUpdatesChan(u)
	}

	// Graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	log.Info("Bot is running...")
	for {
		select {
		case update := <-updates:
			log.Info("Handling updates")
			log.Info(update)
			go handler.HandleUpdate(botApi, update)
			// go service.HandleUpdate(botApi, update)
		case <-stop:
			log.Info("Shutting down bot...")
			return
		}
	}
}
