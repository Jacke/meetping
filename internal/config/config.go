package config

import (
	"log"
	"os"
)

type Config struct {
	BotToken   string
	LogFile    string
}

func Load() Config {
	return Config{
		BotToken: os.Getenv("BOT_TOKEN"),
		LogFile:  getEnv("LOG_FILE", "logs/bot.log"),
	}
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	log.Printf("Using default for %s: %s", key, fallback)
	return fallback
}
package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	TelegramToken string
	Env           string
	DatabaseURL   string
}

func Load() Config {
	_ = godotenv.Load(".env")

	cfg := Config{
		TelegramToken: os.Getenv("TELEGRAM_TOKEN"),
		Env:           os.Getenv("ENV"),
		DatabaseURL:   os.Getenv("DATABASE_URL"),
	}

	if cfg.TelegramToken == "" || cfg.DatabaseURL == "" {
		log.Fatal("Missing required environment variables")
	}
	return cfg
}

