package interaction

import (
	"strconv"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func BuildInlineKeyboard(eventID int64) tgbotapi.InlineKeyboardMarkup {
	buttons := [][]tgbotapi.InlineKeyboardButton{
		{
			tgbotapi.NewInlineKeyboardButtonData("❤️ Нравится", "like_"+strconv.FormatInt(eventID, 10)),
			tgbotapi.NewInlineKeyboardButtonData("🚶 Я иду", "going_"+strconv.FormatInt(eventID, 10)),
		},
	}
	return tgbotapi.NewInlineKeyboardMarkup(buttons...)
}
