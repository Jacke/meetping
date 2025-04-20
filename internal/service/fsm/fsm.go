package fsm

import "sync"

type State string

const (
	StateStart    State = "start"
	StateInterest State = "interest"
	StateCity     State = "city"
)

var userStates = struct {
	m map[int64]State
	sync.RWMutex
}{m: make(map[int64]State)}

func Set(userID int64, state State) {
	userStates.Lock()
	defer userStates.Unlock()
	userStates.m[userID] = state
}

func Get(userID int64) State {
	userStates.RLock()
	defer userStates.RUnlock()
	return userStates.m[userID]
}
