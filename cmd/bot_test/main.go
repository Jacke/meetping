package main

import (
	"meetping/internal/bot"
	"os"
)

func main() {
	token := os.Getenv("TELEGRAM_TOKEN_TEST")
	bot.Run(token, "test")
}
