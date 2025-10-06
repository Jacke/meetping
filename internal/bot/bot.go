package bot

/*
import (
	"log"
	//	"os"

	"meetping/internal/config"
	"meetping/internal/logger"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func Start() error {
	cfg := config.Load()
	logger.InitLogger() //cfg.LogFile)
	bot, err := tgbotapi.NewBotAPI(cfg.BotToken)
	if err != nil {
		return err
	}
	log.Printf("Authorized on account %s", bot.Self.UserName)
	updates := bot.GetUpdatesChan(tgbotapi.UpdateConfig{Timeout: 60})

	for update := range updates {
		// go service.HandleUpdate(bot, update)
		go handler.HandleUpdate(botApi, update)
	}
	return nil
}*/
