package repository

import (
	"database/sql"

	_ "github.com/mattn/go-sqlite3"
)

type Repository struct {
	DB *sql.DB
}

func InitDB(path string) (*Repository, error) {
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, err
	}
	if _, err := db.Exec("PRAGMA foreign_keys = ON"); err != nil {
		return nil, err
	}
	return &Repository{DB: db}, nil
}

// EVENTS
func (r *Repository) SaveEvent(title, desc, link string, cityID int, datetime string) error {
	_, err := r.DB.Exec(`INSERT INTO events (title, description, link, city_id, datetime) VALUES (?, ?, ?, ?, ?)`,
		title, desc, link, cityID, datetime)
	return err
}

func (r *Repository) GetEventsByCity(cityID int) ([]Event, error) {
	rows, err := r.DB.Query(`SELECT id, title, description, link, datetime FROM events WHERE city_id = ? ORDER BY datetime ASC`, cityID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	events := []Event{}
	for rows.Next() {
		var e Event
		err := rows.Scan(&e.ID, &e.Title, &e.Description, &e.Link, &e.Datetime)
		if err != nil {
			return nil, err
		}
		events = append(events, e)
	}
	return events, nil
}

// LIKES
func (r *Repository) ToggleLike(userID, eventID int64) (bool, error) {
	var exists int
	err := r.DB.QueryRow(`SELECT COUNT(*) FROM likes WHERE user_id = ? AND event_id = ?`, userID, eventID).Scan(&exists)
	if err != nil {
		return false, err
	}
	if exists > 0 {
		_, err := r.DB.Exec(`DELETE FROM likes WHERE user_id = ? AND event_id = ?`, userID, eventID)
		return false, err
	}
	_, err = r.DB.Exec(`INSERT INTO likes (user_id, event_id) VALUES (?, ?)`, userID, eventID)
	return true, err
}

// RSVP
func (r *Repository) ToggleRSVP(userID, eventID int64) (bool, error) {
	var exists int
	err := r.DB.QueryRow(`SELECT COUNT(*) FROM rsvps WHERE user_id = ? AND event_id = ?`, userID, eventID).Scan(&exists)
	if err != nil {
		return false, err
	}
	if exists > 0 {
		_, err := r.DB.Exec(`DELETE FROM rsvps WHERE user_id = ? AND event_id = ?`, userID, eventID)
		return false, err
	}
	_, err = r.DB.Exec(`INSERT INTO rsvps (user_id, event_id) VALUES (?, ?)`, userID, eventID)
	return true, err
}

// FEEDBACK
func (r *Repository) SaveFeedback(userID, eventID int64, text string) error {
	_, err := r.DB.Exec(`INSERT INTO event_feedback (user_id, event_id, text) VALUES (?, ?, ?)`, userID, eventID, text)
	return err
}

// USER ACTIONS
func (r *Repository) LogUserAction(userID int64, action, meta string) error {
	_, err := r.DB.Exec(`INSERT INTO user_actions (user_id, action, meta) VALUES (?, ?, ?)`, userID, action, meta)
	return err
}

// INTERESTS
func (r *Repository) AddInterest(userID int64, interestID int) error {
	_, err := r.DB.Exec(`INSERT OR IGNORE INTO user_interests (user_id, interest_id) VALUES (?, ?)`, userID, interestID)
	return err
}

func (r *Repository) RemoveInterest(userID int64, interestID int) error {
	_, err := r.DB.Exec(`DELETE FROM user_interests WHERE user_id = ? AND interest_id = ?`, userID, interestID)
	return err
}

// CITIES
func (r *Repository) SetPrimaryCity(userID, cityID int64) error {
	_, err := r.DB.Exec(`UPDATE user_cities SET is_primary = 0 WHERE user_id = ?`, userID)
	if err != nil {
		return err
	}
	_, err = r.DB.Exec(`INSERT OR REPLACE INTO user_cities (user_id, city_id, is_primary) VALUES (?, ?, 1)`, userID, cityID)
	return err
}

func (r *Repository) GetPrimaryCity(userID int64) (int, error) {
	var cityID int
	err := r.DB.QueryRow(`SELECT city_id FROM user_cities WHERE user_id = ? AND is_primary = 1`, userID).Scan(&cityID)
	return cityID, err
}

// STRUCTS

type Event struct {
	ID          int64
	Title       string
	Description string
	Link        string
	Datetime    string
}
