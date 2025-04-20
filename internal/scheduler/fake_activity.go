package scheduler

import (
	"log"
	"math/rand"
	"time"
)

func SimulateFakeReactions() {
	log.Println("[fake] фейковая активность активирована")

	eventIDs := []int64{101, 102, 103, 104}
	for _, id := range eventIDs {
		fakeLikes := rand.Intn(5)
		fakeGoing := rand.Intn(2)
		log.Printf("[fake] +%d ❤️ / +%d 🚶 к событию %d", fakeLikes, fakeGoing, id)
	}
}
