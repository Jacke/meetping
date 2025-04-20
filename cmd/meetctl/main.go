package main

import (
	"database/sql"
	"os"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	switch {
	case len(os.Args) == 3 && os.Args[1] == "export:csv":
		db, _ := sql.Open("sqlite3", "data/meetping.sqlite")
		ExportCSV(db, os.Args[2])

	case len(os.Args) == 2 && os.Args[1] == "backup":
		CreateBackup("meetping_backup.zip")

	default:
		println("Usage:")
		println("  meetctl export:csv <table>")
		println("  meetctl backup")
	}
}
