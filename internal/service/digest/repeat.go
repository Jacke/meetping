package digest

import (
	"log"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func HandleRepeat(bot *tgbotapi.BotAPI, userID int64) {
	log.Printf("Повторная отправка дайджеста пользователю %d", userID)
	SendDigest(bot, userID)
}
