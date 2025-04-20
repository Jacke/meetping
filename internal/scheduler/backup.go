package scheduler

import (
	"log"
	"os"
	"time"
	"meetping/internal/config"

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

	doc := tgbotapi.NewDocument(config.AdminID, tgbotapi.FileReader{
		Name:   path,
		Reader: file,
		Size:   -1,
	})
	bot.Send(doc)
	log.Printf("[backup] отправлен %s", path)
}

func createBackup(outputPath string) error {
	// Переиспользует CLI CreateBackup
	return nil // placeholder, будет использовать cmd/meetctl/backup.go в будущем
}
