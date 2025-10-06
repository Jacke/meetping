package main

import (
	"log"
	"meetping/internal/bot"

	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load()
	if err := bot.Start(); err != nil {
		log.Fatalf("Bot exited with error: %v", err)
	}
}
