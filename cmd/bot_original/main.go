package main

import (
	"meetping/internal/bot"
	"os"
)

func main() {
	token := os.Getenv("TELEGRAM_TOKEN_ORIGINAL")
	bot.Run(token, "original")
}
