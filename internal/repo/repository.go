package repo

import (
	"database/sql"
	"fmt"
	"time"
)

type Repository struct {
	DB *sql.DB
}

func NewRepository(db *sql.DB) *Repository {
	return &Repository{DB: db}
}

func (r *Repository) SaveUser(user User) error {
	_, err := r.DB.Exec(`
		INSERT INTO users (telegram_id, username, digest_time)
		VALUES (?, ?, ?)
		ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username
	`, user.TelegramID, user.Username, user.DigestTime)
	return err
}

func (r *Repository) GetUserByTelegramID(tgID int64) (*User, error) {
	row := r.DB.QueryRow("SELECT id, telegram_id, username, digest_time FROM users WHERE telegram_id = ?", tgID)
	var u User
	err := row.Scan(&u.ID, &u.TelegramID, &u.Username, &u.DigestTime)
	if err != nil {
		return nil, err
	}
	return &u, nil
}

func (r *Repository) ToggleLike(userID, eventID int) error {
	_, err := r.DB.Exec(`
		INSERT INTO likes (user_id, event_id) VALUES (?, ?)
		ON CONFLICT(user_id, event_id) DO DELETE
	`, userID, eventID)
	return err
}

func (r *Repository) ToggleRSVP(userID, eventID int) error {
	// RSVP implies like
	tx, err := r.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	_, err = tx.Exec(`
		INSERT INTO rsvps (user_id, event_id) VALUES (?, ?)
		ON CONFLICT(user_id, event_id) DO DELETE
	`, userID, eventID)
	if err != nil {
		return err
	}

	_, err = tx.Exec(`
		INSERT OR IGNORE INTO likes (user_id, event_id) VALUES (?, ?)
	`, userID, eventID)
	if err != nil {
		return err
	}

	return tx.Commit()
}

func (r *Repository) SaveFeedback(f Feedback) error {
	_, err := r.DB.Exec(`
		INSERT INTO event_feedback (user_id, event_id, feedback)
		VALUES (?, ?, ?)
	`, f.UserID, f.EventID, f.Feedback)
	return err
}

func (r *Repository) SaveEvent(e Event) error {
	query := `
		INSERT INTO events (id, title, description, city_id, likes, date)
		VALUES (?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			title = excluded.title,
			description = excluded.description,
			city_id = excluded.city_id,
			likes = excluded.likes,
			date = excluded.date
	`

	// лог: входные данные
	fmt.Printf("[SaveEvent] ID=%d Title=%q CityID=%d Likes=%d Date=%s\n",
		e.ID, e.Title, e.CityID, e.Likes, e.Date.Format(time.RFC3339))

	// лог: SQL-запрос
	fmt.Println("[SaveEvent] SQL Query:")
	fmt.Println(query)

	// выполнение запроса
	_, err := r.DB.Exec(query,
		e.ID, e.Title, e.Description, e.CityID, e.Likes, e.Date)

	// лог: результат
	if err != nil {
		fmt.Printf("[SaveEvent] ERROR: %v\n", err)
	} else {
		fmt.Println("[SaveEvent] SUCCESS")
	}

	return err
}

func (r *Repository) LogUserAction(a Action) error {
	_, err := r.DB.Exec(`
		INSERT INTO user_actions (user_id, action, meta)
		VALUES (?, ?, ?)
	`, a.UserID, a.Action, a.Meta)
	return err
}

func (r *Repository) GetUsersByDigestTime(t string) ([]User, error) {
	rows, _ := r.DB.Query("SELECT id, telegram_id, username, digest_time FROM users WHERE digest_time = ?", t)
	defer rows.Close()
	var result []User
	for rows.Next() {
		var u User
		rows.Scan(&u.ID, &u.TelegramID, &u.Username, &u.DigestTime)
		result = append(result, u)
	}
	return result, nil
}

func (r *Repository) InsertFakeScore(eventID int, scoreType string) error {
	_, err := r.DB.Exec(`
		INSERT INTO event_score_fake (event_id, user_id, score_type)
		VALUES (?, 0, ?)
	`, eventID, scoreType)
	return err
}

func (r *Repository) GetPrimaryCityID(userID int) int {
	var cityID int
	_ = r.DB.QueryRow("SELECT city_id FROM user_cities WHERE user_id = ? AND is_primary = 1", userID).Scan(&cityID)
	return cityID
}

func (r *Repository) GetActiveEvents() []int {
	rows, _ := r.DB.Query("SELECT id FROM events WHERE date > datetime('now')")
	defer rows.Close()

	var ids []int
	for rows.Next() {
		var id int
		rows.Scan(&id)
		ids = append(ids, id)
	}
	return ids
}

type UserEventPair struct {
	UserID  int
	EventID int
}

func (r *Repository) GetUpcomingRSVPs(d time.Duration) []UserEventPair {
	rows, _ := r.DB.Query(`
		SELECT r.user_id, r.event_id
		FROM rsvps r
		JOIN events e ON e.id = r.event_id
		WHERE e.date BETWEEN datetime('now') AND datetime('now', '+30 minutes')
	`)
	defer rows.Close()

	var result []UserEventPair
	for rows.Next() {
		var p UserEventPair
		rows.Scan(&p.UserID, &p.EventID)
		result = append(result, p)
	}
	return result
}

func (r *Repository) GetPastRSVPsWithoutFeedback() []UserEventPair {
	rows, _ := r.DB.Query(`
		SELECT r.user_id, r.event_id
		FROM rsvps r
		JOIN events e ON e.id = r.event_id
		WHERE e.date < datetime('now')
		AND NOT EXISTS (
			SELECT 1 FROM event_feedback f
			WHERE f.user_id = r.user_id AND f.event_id = r.event_id
		)
	`)
	defer rows.Close()

	var result []UserEventPair
	for rows.Next() {
		var p UserEventPair
		rows.Scan(&p.UserID, &p.EventID)
		result = append(result, p)
	}
	return result
}

func (r *Repository) GetUserByID(userID int) User {
	var u User
	_ = r.DB.QueryRow(`
		SELECT id, telegram_id, username, digest_time
		FROM users
		WHERE id = ?
	`, userID).Scan(&u.ID, &u.TelegramID, &u.Username, &u.DigestTime)
	return u
}

func (r *Repository) GetEventByID(eventID int) Event {
	var e Event
	_ = r.DB.QueryRow(`
		SELECT id, title, description, city_id, likes, date
		FROM events
		WHERE id = ?
	`, eventID).Scan(&e.ID, &e.Title, &e.Description, &e.CityID, &e.Likes, &e.Date)
	return e
}

func (r *Repository) EnsureCity(name string) int {
	var id int
	err := r.DB.QueryRow("SELECT id FROM cities WHERE name = ?", name).Scan(&id)
	if err == sql.ErrNoRows {
		res, _ := r.DB.Exec("INSERT INTO cities (name) VALUES (?)", name)
		id64, _ := res.LastInsertId()
		id = int(id64)
	}
	return id
}

func (r *Repository) SetPrimaryCity(userID, cityID int) {
	_, _ = r.DB.Exec("UPDATE user_cities SET is_primary = 0 WHERE user_id = ?", userID)
	_, _ = r.DB.Exec(`
		INSERT INTO user_cities (user_id, city_id, is_primary)
		VALUES (?, ?, 1)
		ON CONFLICT(user_id, city_id) DO UPDATE SET is_primary = 1
	`, userID, cityID)
}

func (r *Repository) EnsureInterest(name string) int {
	var id int
	err := r.DB.QueryRow("SELECT id FROM interests WHERE name = ?", name).Scan(&id)
	if err == sql.ErrNoRows {
		res, _ := r.DB.Exec("INSERT INTO interests (name) VALUES (?)", name)
		id64, _ := res.LastInsertId()
		id = int(id64)
	}
	return id
}

func (r *Repository) SetUserInterests(userID int, interestIDs []int) {
	_, _ = r.DB.Exec("DELETE FROM user_interests WHERE user_id = ?", userID)
	for _, iid := range interestIDs {
		_, _ = r.DB.Exec("INSERT INTO user_interests (user_id, interest_id) VALUES (?, ?)", userID, iid)
	}
}

func (r *Repository) GetPrimaryCityName(userID int) string {
	var name string
	_ = r.DB.QueryRow(`
		SELECT c.name
		FROM cities c
		JOIN user_cities uc ON uc.city_id = c.id
		WHERE uc.user_id = ? AND uc.is_primary = 1
	`, userID).Scan(&name)
	return name
}

func (r *Repository) GetUserInterestNames(userID int) []string {
	rows, _ := r.DB.Query(`
		SELECT i.name
		FROM interests i
		JOIN user_interests ui ON ui.interest_id = i.id
		WHERE ui.user_id = ?
	`, userID)
	defer rows.Close()

	var names []string
	for rows.Next() {
		var name string
		rows.Scan(&name)
		names = append(names, name)
	}
	return names
}
