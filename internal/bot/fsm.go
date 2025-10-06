package bot

import "sync"

type FSM struct {
	state map[int64]string
	mu    sync.RWMutex
}

func NewFSM() *FSM {
	return &FSM{
		state: make(map[int64]string),
	}
}

func (f *FSM) Set(chatID int64, s string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.state[chatID] = s
}

func (f *FSM) Get(chatID int64) string {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.state[chatID]
}

func (f *FSM) Clear(chatID int64) {
	f.mu.Lock()
	defer f.mu.Unlock()
	delete(f.state, chatID)
}
