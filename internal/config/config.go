package config

import (
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	BotToken      string
	LogFile       string
	TelegramToken string
	Env           string
	DatabaseURL   string
	AdminID       int64
}

func Load() Config {
	_ = godotenv.Load(".env")

	cfg := Config{
		TelegramToken: os.Getenv("TELEGRAM_TOKEN"),
		Env:           os.Getenv("ENV"),
		DatabaseURL:   os.Getenv("DATABASE_URL"),
		BotToken:      os.Getenv("BOT_TOKEN"),
		LogFile:       getEnv("LOG_FILE", "logs/bot.log"),
	}

	if admin := os.Getenv("ADMIN_ID"); admin != "" {
		cfg.AdminID, _ = strconv.ParseInt(admin, 10, 64)
	}

	if cfg.TelegramToken == "" || cfg.DatabaseURL == "" {
		log.Fatal("Missing required environment variables")
	}
	return cfg

}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	log.Printf("Using default for %s: %s", key, fallback)
	return fallback
}
