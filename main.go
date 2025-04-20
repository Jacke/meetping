package main

import (
	"log"
	"github.com/joho/godotenv"
	"meetping/internal/bot"
)

func main() {
	_ = godotenv.Load()
	if err := bot.Start(); err != nil {
		log.Fatalf("Bot exited with error: %v", err)
	}
}
