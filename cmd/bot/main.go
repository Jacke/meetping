package main

import (
	"os"
	"os/signal"
	"syscall"

	"meetping/internal/config"
	"meetping/internal/logger"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
	// Load config
	cfg := config.Load()

	// Init logger
	log := logger.New()

	// Init bot
	bot, err := tgbotapi.NewBotAPI(cfg.TelegramToken)
	if err != nil {
		log.Fatal("Bot init error", err)
	}
	log.Infof("Authorized on account %s", bot.Self.UserName)

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60
	updates := bot.GetUpdatesChan(u)

	// Graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	for {
		select {
		case update := <-updates:
			// TODO: handle updates
			log.Infof("Update received: %+v", update)
		case <-stop:
			log.Info("Shutting down bot...")
			return
		}
	}
}
