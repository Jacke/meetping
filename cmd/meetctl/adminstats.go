package main

import (
	"fmt"
	"database/sql"
	_ "github.com/mattn/go-sqlite3"
)

func adminStats() {
	db, _ := sql.Open("sqlite3", "data/meetping.sqlite")
	defer db.Close()

	var users, events, actions int
	db.QueryRow("SELECT COUNT(*) FROM users").Scan(&users)
	db.QueryRow("SELECT COUNT(*) FROM events").Scan(&events)
	db.QueryRow("SELECT COUNT(*) FROM user_actions").Scan(&actions)

	fmt.Printf("Users: %d\nEvents: %d\nActions: %d\n", users, events, actions)
}
