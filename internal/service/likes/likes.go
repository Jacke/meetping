package likes

import (
	"fmt"
	"sync"
)

var likes = make(map[int64]map[int64]bool) // userID -> eventID
var mu sync.Mutex

func ToggleLike(userID, eventID int64) bool {
	mu.Lock()
	defer mu.Unlock()

	if likes[userID] == nil {
		likes[userID] = make(map[int64]bool)
	}

	if likes[userID][eventID] {
		delete(likes[userID], eventID)
		fmt.Printf("User %d unliked event %d\n", userID, eventID)
		return false
	} else {
		likes[userID][eventID] = true
		fmt.Printf("User %d liked event %d\n", userID, eventID)
		return true
	}
}
