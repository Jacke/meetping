package repo

import "time"

type User struct {
	ID         int
	TelegramID int64
	Username   string
	DigestTime string
}

type Event struct {
	ID          int
	Title       string
	Description string
	CityID      int
	Likes       int
	Date        time.Time
}

type Feedback struct {
	UserID   int
	EventID  int
	Feedback string
}

type Action struct {
	UserID int
	Action string
	Meta   string
}
