package repository

import (
	"database/sql"
	"log"
)

func LogUserAction(db *sql.DB, userID int64, action, meta string) {
	_, err := db.Exec(`INSERT INTO user_actions (user_id, action, meta) VALUES (?, ?, ?)`, userID, action, meta)
	if err != nil {
		log.Printf("Failed to log user action: %v", err)
	}
}
