package service

import (
	"database/sql"
	"fmt"
	"strings"
	"time"
)

type Event struct {
	ID          int64
	Title       string
	Description string
	City        string
	Datetime    string
	Link        string
	Score       float64
}

type DigestItem struct {
	EventID     int
	Title       string
	Date        time.Time
	Description string
	Score       int
}

type DigestService struct {
	DB *sql.DB
}

func NewDigestService(db *sql.DB) *DigestService {
	return &DigestService{DB: db}
}

func (s *DigestService) GetDigestForUser(userID int, cityID int) ([]DigestItem, error) {
	rows, err := s.DB.Query(`
		SELECT e.id, e.title, e.description, e.date,
			IFNULL(l.like_count, 0),
			IFNULL(r.rsvp_count, 0),
			IFNULL(f.fake_boost, 0)
		FROM events e
		LEFT JOIN (
			SELECT event_id, COUNT(*) AS like_count
			FROM likes
			GROUP BY event_id
		) l ON e.id = l.event_id
		LEFT JOIN (
			SELECT event_id, COUNT(*) AS rsvp_count
			FROM rsvps
			GROUP BY event_id
		) r ON e.id = r.event_id
		LEFT JOIN (
			SELECT event_id, COUNT(*) AS fake_boost
			FROM event_score_fake
			GROUP BY event_id
		) f ON e.id = f.event_id
		WHERE e.city_id = ?
		ORDER BY e.date ASC
	`, cityID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []DigestItem
	for rows.Next() {
		var item DigestItem
		var likes, rsvps, fake int
		if err := rows.Scan(&item.EventID, &item.Title, &item.Description, &item.Date, &likes, &rsvps, &fake); err != nil {
			return nil, err
		}
		item.Score = CalculateScore(likes, rsvps, fake)
		items = append(items, item)
	}
	return items, nil
}

func BuildDigest(events []Event, city string) string {
	var sb strings.Builder
	if len(events) == 0 {
		return fmt.Sprintf("В городе %s пока нет новых мероприятий.", city)
	}
	sb.WriteString(fmt.Sprintf("Вот что происходит в %s:\n\n", city))
	for _, e := range events {
		sb.WriteString(fmt.Sprintf("• *%s* (%s)\n%s\n[Открыть](%s)\n\n", e.Title, e.Datetime, e.Description, e.Link))
	}
	return sb.String()
}
