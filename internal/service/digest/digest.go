package digest

import (
	"fmt"
	"time"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func SendDigest(bot *tgbotapi.BotAPI, userID int64) {
	text := fmt.Sprintf("Привет! Вот свежие события для тебя на %s", time.Now().Format("02 Jan"))
	msg := tgbotapi.NewMessage(userID, text)
	bot.Send(msg)
}
