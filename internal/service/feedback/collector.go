package feedback

import (
	"fmt"
)

type Feedback struct {
	UserID  int64
	EventID int64
	Text    string
}

var stored []Feedback

func SaveFeedback(f Feedback) {
	stored = append(stored, f)
	fmt.Printf("Feedback from user %d on event %d: %s\n", f.UserID, f.EventID, f.Text)
}
