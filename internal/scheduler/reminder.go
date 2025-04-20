package scheduler

import (
	"fmt"
	"log"
	"time"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

type Event struct {
	ID     int64
	Title  string
	Start  time.Time
	UserID int64
}

func SendReminders(bot *tgbotapi.BotAPI, upcoming []Event) {
	now := time.Now()
	for _, e := range upcoming {
		if e.Start.Sub(now) < 30*time.Minute && e.Start.Sub(now) > 0 {
			msg := tgbotapi.NewMessage(e.UserID, fmt.Sprintf("Напоминание: %s начнётся в %s", e.Title, e.Start.Format("15:04")))
			bot.Send(msg)
			log.Printf("Напомнили пользователю %d о событии %d", e.UserID, e.ID)
		}
	}
}
