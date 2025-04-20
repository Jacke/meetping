package interaction

import (
	"strings"
	"strconv"
	"log"

	"meetping/internal/service/likes"
	"meetping/internal/service/rsvp"
	"meetping/internal/service/digest"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func HandleCallback(bot *tgbotapi.BotAPI, callback *tgbotapi.CallbackQuery) {
	data := callback.Data
	userID := callback.From.ID

	switch {
	case strings.HasPrefix(data, "like_"):
		eventID, _ := strconv.ParseInt(strings.TrimPrefix(data, "like_"), 10, 64)
		liked := likes.ToggleLike(userID, eventID)
		response := "Вы поставили ❤️"
		if !liked {
			response = "Вы убрали ❤️"
		}
		bot.AnswerCallbackQuery(tgbotapi.NewCallback(callback.ID, response))

	case strings.HasPrefix(data, "going_"):
		eventID, _ := strconv.ParseInt(strings.TrimPrefix(data, "going_"), 10, 64)
		going := rsvp.ToggleGoing(userID, eventID)
		if going {
			likes.ToggleLike(userID, eventID) // автолайк
		}
		response := "Вы отметились как идущий 🚶"
		if !going {
			response = "Вы отменили участие"
		}
		bot.AnswerCallbackQuery(tgbotapi.NewCallback(callback.ID, response))

	case data == "repeat_digest":
		digest.HandleRepeat(bot, userID)
		bot.AnswerCallbackQuery(tgbotapi.NewCallback(callback.ID, "Дайджест повторно отправлен"))

	default:
		log.Println("Unknown callback:", data)
	}
}
