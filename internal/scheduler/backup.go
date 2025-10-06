package scheduler

import (
	"log"
	"meetping/internal/config"
	"os"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func DailyBackupToAdmin(bot *tgbotapi.BotAPI) {
	path := "logs/meetping_backup_" + time.Now().Format("2006_01_02") + ".zip"
	err := createBackup(path)
	if err != nil {
		log.Printf("[backup] ошибка: %v", err)
		return
	}
	file, _ := os.Open(path)
	defer file.Close()

	cfg := config.Load()
	doc := tgbotapi.NewDocument(cfg.AdminID, tgbotapi.FileReader{
		Name:   path,
		Reader: file,
	})
	bot.Send(doc)
	log.Printf("[backup] отправлен %s", path)
}

func createBackup(outputPath string) error {
	// Переиспользует CLI CreateBackup
	return nil // placeholder, будет использовать cmd/meetctl/backup.go в будущем
}
