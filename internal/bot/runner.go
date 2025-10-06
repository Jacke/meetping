package bot

import (
	"meetping/internal/config"
	"meetping/internal/db"
	"meetping/internal/logger"
	"meetping/internal/repo"
	"meetping/internal/scheduler"
	"meetping/internal/service"
	"net/http"
	"os"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func Run(token string, label string) {
	cfg := config.Load()
	log := logger.New()
	database := db.InitDB(cfg.DatabaseURL)

	repository := repo.NewRepository(database)
	digests := service.NewDigestService(database)
	handler := NewHandler(repository, log)

	bot, err := tgbotapi.NewBotAPI(token)
	if err != nil {
		log.Fatalf("[%s] bot init failed: %v", label, err)
	}
	log.Infof("[%s] Bot authorized as %s", label, bot.Self.UserName)

	// Scheduler
	scheduler := scheduler.CronJobs{
		Repo:    repository,
		Digests: digests,
		BotSend: func(user repo.User, items []service.DigestItem) {
			// Simplified sending
			for _, e := range items {
				bot.Send(tgbotapi.NewMessage(user.TelegramID, "🎉 "+e.Title))
			}
		},
	}
	scheduler.Start()

	useWebhook := os.Getenv("USE_WEBHOOK") == "1"
	var updates tgbotapi.UpdatesChannel

	if useWebhook {
		webhookConfig, err := tgbotapi.NewWebhook("https://yourdomain.com/" + token)
		if err != nil {
			log.Fatalf("Webhook error: %v", err)
		}
		_, err = bot.Request(webhookConfig)
		if err != nil {
			log.Fatalf("Webhook error: %v", err)
		}
		updates = bot.ListenForWebhook("/" + token)
		go http.ListenAndServe(":8443", nil)
	} else {
		u := tgbotapi.NewUpdate(0)
		u.Timeout = 60
		updates = bot.GetUpdatesChan(u)
	}

	for update := range updates {
		handler.HandleUpdate(bot, update)
	}
}
