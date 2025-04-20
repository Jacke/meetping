package interests

import (
	"fmt"
	"sync"
)

var userInterests = make(map[int64]map[string]bool)
var mu sync.Mutex

func SaveUserInterest(userID int64, interest string) {
	mu.Lock()
	defer mu.Unlock()
	if userInterests[userID] == nil {
		userInterests[userID] = make(map[string]bool)
	}
	userInterests[userID][interest] = true
	fmt.Printf("User %d added interest %s\n", userID, interest)
}

func RemoveUserInterest(userID int64, interest string) {
	mu.Lock()
	defer mu.Unlock()
	if userInterests[userID] != nil {
		delete(userInterests[userID], interest)
		fmt.Printf("User %d removed interest %s\n", userID, interest)
	}
}

func GetUserInterests(userID int64) []string {
	mu.Lock()
	defer mu.Unlock()
	var result []string
	for i := range userInterests[userID] {
		result = append(result, i)
	}
	return result
}
