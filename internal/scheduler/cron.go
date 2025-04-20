package scheduler

import (
	"github.com/robfig/cron/v3"
	"meetping/internal/config"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func Init(bot *tgbotapi.BotAPI) *cron.Cron {
	c := cron.New()
	c.AddFunc("@every 5m", func() {
		SimulateFakeReactions()
	})
	c.AddFunc("@daily", func() {
		DailyBackupToAdmin(bot)
	})
	return c
}
