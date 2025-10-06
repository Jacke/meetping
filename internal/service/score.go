package service

type EventScore struct {
	EventID int
	Score   int
	Likes   int
	RSVPs   int
	Fake    int
}

func CalculateScore(likes, rsvps, fake int) int {
	return likes + 2*rsvps + fake
}
