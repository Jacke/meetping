package main

import (
	"log"
	"meetping/internal/bot"
	"meetping/internal/config"
	"meetping/internal/scheduler"
)

func main() {
	cfg := config.Load()
	log.Println("Запуск основного бота...")
	botInstance, err := bot.Start()
	if err != nil {
		log.Fatalf("Ошибка запуска бота: %v", err)
	}
	scheduler.StartScheduler()
	select {}
}
