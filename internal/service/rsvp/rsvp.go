package rsvp

import (
	"fmt"
	"sync"
)

var rsvps = make(map[int64]map[int64]bool) // userID -> eventID
var mu sync.Mutex

func ToggleGoing(userID, eventID int64) bool {
	mu.Lock()
	defer mu.Unlock()

	if rsvps[userID] == nil {
		rsvps[userID] = make(map[int64]bool)
	}

	if rsvps[userID][eventID] {
		delete(rsvps[userID], eventID)
		fmt.Printf("User %d canceled RSVP to event %d\n", userID, eventID)
		return false
	} else {
		rsvps[userID][eventID] = true
		fmt.Printf("User %d is going to event %d\n", userID, eventID)
		return true
	}
}
