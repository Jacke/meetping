package interaction

import (
	"meetping/internal/service/interests"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func ShowInterestMenu(bot *tgbotapi.BotAPI, userID int64) {
	interestsList := interests.GetUserInterests(userID)
	var rows [][]tgbotapi.InlineKeyboardButton
	for _, i := range interestsList {
		rows = append(rows, tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("Удалить: "+i, "remove_interest_"+i),
		))
	}
	rows = append(rows, tgbotapi.NewInlineKeyboardRow(
		tgbotapi.NewInlineKeyboardButtonData("Закрыть", "close_menu"),
	))
	keyboard := tgbotapi.NewInlineKeyboardMarkup(rows...)
	msg := tgbotapi.NewMessage(userID, "Выберите интерес для удаления:")
	msg.ReplyMarkup = keyboard
	bot.Send(msg)
}
