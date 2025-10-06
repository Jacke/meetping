package scheduler

import (
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"github.com/robfig/cron/v3"
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
