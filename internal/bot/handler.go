package bot

import (
	"fmt"
	"strconv"
	"strings"

	"meetping/internal/repo"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"go.uber.org/zap"
)

type BotHandler struct {
	Repo *repo.Repository
	FSM  *FSM
	Log  *zap.SugaredLogger
}

func NewHandler(repo *repo.Repository, log *zap.SugaredLogger) *BotHandler {
	return &BotHandler{
		Repo: repo,
		FSM:  NewFSM(),
		Log:  log,
	}
}

func (h *BotHandler) HandleUpdate(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	if update.CallbackQuery != nil {
		h.handleCallback(bot, update.CallbackQuery)
		return
	}

	if update.Message != nil && update.Message.IsCommand() {
		h.Log.Infof("[CMD] %s", update.Message.Text)
		h.handleCommand(bot, update.Message)
		return
	}

	if update.Message != nil {
		chatID := update.Message.Chat.ID
		userID := int64(update.Message.From.ID)
		text := strings.TrimSpace(update.Message.Text)

		state := h.FSM.Get(chatID)
		h.Log.Infof("[FSM] chat=%d state=%s text=%q", chatID, state, text)

		if state == "" {
			return
		}

		user, err := h.Repo.GetUserByTelegramID(userID)
		if err != nil {
			bot.Send(tgbotapi.NewMessage(chatID, "❌ Ошибка доступа к профилю."))
			return
		}

		successText := ""

		switch state {
		case "awaiting_city":
			cityID := h.Repo.EnsureCity(text)
			h.Repo.SetPrimaryCity(user.ID, cityID)
			successText = "🏙 Город обновлён"

		case "awaiting_interests":
			raw := strings.Split(text, ",")
			var interestIDs []int
			for _, name := range raw {
				id := h.Repo.EnsureInterest(strings.TrimSpace(name))
				interestIDs = append(interestIDs, id)
			}
			h.Repo.SetUserInterests(user.ID, interestIDs)
			successText = "🎯 Интересы обновлены"

		case "awaiting_digest_time":
			_, _ = h.Repo.DB.Exec("UPDATE users SET digest_time = ? WHERE id = ?", text, user.ID)
			successText = "⏰ Время дайджеста обновлено"

		default:
			h.Log.Warnf("[FSM] Неизвестное состояние %q для chat=%d", state, chatID)
		}

		h.FSM.Clear(chatID)

		// Ответ + возврат в меню
		if successText != "" {
			bot.Send(tgbotapi.NewMessage(chatID, successText))
			h.showMenu(bot, chatID, user.TelegramID)
		}
	}
}

func (h *BotHandler) handleCommand(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	chatID := msg.Chat.ID
	tgID := msg.From.ID
	username := msg.From.UserName

	user := repo.User{
		TelegramID: int64(tgID),
		Username:   username,
		DigestTime: "10:00",
	}

	h.Log.Infof("Регистрация пользователя: %+v", user)

	err := h.Repo.SaveUser(user)
	if err != nil {
		h.Log.Errorf("Ошибка при сохранении пользователя: %v", err)
	}

	if msg.Command() == "adminstats" && username != "stansob" {
		bot.Send(tgbotapi.NewMessage(chatID, "🚫 Нет доступа"))
		return
	}

	switch msg.Command() {
	case "start":
		bot.Send(tgbotapi.NewMessage(chatID, "👋 Добро пожаловать в MeetPing!"))
	case "menu":
		h.showMenu(bot, chatID, tgID)
	case "edit_city":
		bot.Send(tgbotapi.NewMessage(chatID, "Введите новый город:"))
		h.FSM.Set(chatID, "awaiting_city")
	case "edit_interests":
		bot.Send(tgbotapi.NewMessage(chatID, "Введите интересы через запятую:"))
		h.FSM.Set(chatID, "awaiting_interests")
	case "edit_time":
		bot.Send(tgbotapi.NewMessage(chatID, "Введите время получения дайджеста (например, 10:00):"))
		h.FSM.Set(chatID, "awaiting_digest_time")
	}
}

func (h *BotHandler) showMenu(bot *tgbotapi.BotAPI, chatID int64, tgID int64) {
	h.Log.Errorf("[showMenu] chatId: %v user: %v", chatID, tgID)
	user, err := h.Repo.GetUserByTelegramID(tgID)
	if err != nil {
		bot.Send(tgbotapi.NewMessage(chatID, "Ошибка загрузки профиля."))
		return
	}

	city := h.Repo.GetPrimaryCityName(user.ID)
	interests := h.Repo.GetUserInterestNames(user.ID)

	text := fmt.Sprintf(
		"Ваши настройки:\n\n"+
			"🏙 Город: %s\n"+
			"🎯 Интересы: %s\n"+
			"⏰ Время дайджеста: %s\n\n"+
			"Что хотите изменить?",
		city,
		strings.Join(interests, ", "),
		user.DigestTime,
	)

	msg := tgbotapi.NewMessage(chatID, text)
	msg.ReplyMarkup = tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("✏ Изменить город", "edit_city"),
			tgbotapi.NewInlineKeyboardButtonData("✏ Изменить интересы", "edit_interests"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("✏ Изменить время", "edit_time"),
			tgbotapi.NewInlineKeyboardButtonData("👁 Показать пример", "show_sample_digest"),
		),
	)
	bot.Send(msg)
}

func (h *BotHandler) handleCallback(bot *tgbotapi.BotAPI, q *tgbotapi.CallbackQuery) {
	data := q.Data
	chatID := q.Message.Chat.ID

	parts := splitCallback(data)
	h.Log.Infof("[CALLBACK] split=%+v raw=%q", parts, data)

	action := parts[0]
	payload := parts[1] // может быть "", либо eventID

	user, err := h.Repo.GetUserByTelegramID(q.From.ID)
	if err != nil {
		h.Log.Errorf("[CALLBACK] GetUserByTelegramID error: %v", err)
		return
	}

	var eventID int
	if payload != "" {
		eventID, _ = strconv.Atoi(payload)
	}

	switch action {
	case "like":
		_ = h.Repo.ToggleLike(user.ID, eventID)
	case "rsvp":
		_ = h.Repo.ToggleRSVP(user.ID, eventID)
	case "edit":
		switch payload {
		case "city":
			bot.Send(tgbotapi.NewMessage(chatID, "Введите новый город:"))
			h.FSM.Set(chatID, "awaiting_city")
		case "interests":
			bot.Send(tgbotapi.NewMessage(chatID, "Введите интересы через запятую:"))
			h.FSM.Set(chatID, "awaiting_interests")
		case "time":
			bot.Send(tgbotapi.NewMessage(chatID, "Введите время получения дайджеста (например, 10:00):"))
			h.FSM.Set(chatID, "awaiting_digest_time")
		}
	case "show":
		if payload == "sample_digest" {
			h.sendSampleDigest(bot, chatID)
		}
	default:
		h.Log.Warnf("[CALLBACK] Unknown action=%q payload=%q", action, payload)
	}

	// Отправить "Готово!" только если это like/rsvp
	if action == "like" || action == "rsvp" {
		bot.Request(tgbotapi.NewCallback(q.ID, "Готово!"))

		if action == "like" {
			likedEvent := h.Repo.GetEventByID(eventID)
			likedEvent.Likes = likedEvent.Likes + 1
			err := h.Repo.SaveEvent(likedEvent)
			if err != nil {
				h.Log.Errorf("likedEvent err: %v", err)
			}
			h.Log.Errorf("likedEvent: %v", likedEvent.Likes)
			likedEvent2 := h.Repo.GetEventByID(eventID)
			h.Log.Errorf("likedEvent2: %v", likedEvent2.Likes)
		}
		newMarkup := actionButtons(eventID, h)
		edit := tgbotapi.NewEditMessageReplyMarkup(chatID, q.Message.MessageID, newMarkup)
		bot.Send(edit)
		h.showMenu(bot, chatID, user.TelegramID)
	}
}

func splitCallback(data string) []string {
	parts := strings.SplitN(data, "_", 2)
	if len(parts) != 2 {
		return nil
	}
	return parts
}

func actionButtons(eventID int, h *BotHandler) tgbotapi.InlineKeyboardMarkup {
	event := h.Repo.GetEventByID(eventID)
	h.Log.Errorf("actionButtons: %v", event.Likes)
	return tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData(fmt.Sprintf("❤️ %d", event.Likes), fmt.Sprintf("like_%d", event.ID)),
			tgbotapi.NewInlineKeyboardButtonData("✅ Я иду", fmt.Sprintf("rsvp_%d", event.ID)),
		),
	)
}

func sendEventCard(bot *tgbotapi.BotAPI, chatID int64, event repo.Event, h *BotHandler) {
	msg := tgbotapi.NewMessage(chatID, fmt.Sprintf("📅 *%s*\n%s", event.Title, event.Description))
	msg.ParseMode = "Markdown"
	msg.ReplyMarkup = actionButtons(event.ID, h)
	bot.Send(msg)
}

func (h *BotHandler) sendSampleDigest(bot *tgbotapi.BotAPI, chatID int64) {
	/*
		sample := repo.Event{
			ID:          999,
			Title:       "Митап по стартапам и AI",
			Likes:       1,
			Description: "Легендарная встреча основателей, инвесторов и инженеров.",
		}
		h.Repo.SaveEvent(sample)
	*/
	sample := h.Repo.GetEventByID(999)
	sendEventCard(bot, chatID, sample, h)
}
