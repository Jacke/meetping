package digest

import (
	"math/rand"
)

type EventScore struct {
	EventID int64
	Likes   int
	Going   int
	Fake    int
}

func CalculateScore(e EventScore) float64 {
	// Базовая формула: лайки + 2 * going + 0.5 * fake
	return float64(e.Likes) + 2*float64(e.Going) + 0.5*float64(e.Fake)
}

func SimulateFakeActivity(eventIDs []int64) map[int64]int {
	result := make(map[int64]int)
	for _, id := range eventIDs {
		result[id] = rand.Intn(4) // 0–3 фейковых лайка/going
	}
	return result
}
