package main

import (
	"archive/zip"
	"database/sql"
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"

	_ "github.com/mattn/go-sqlite3"
)

var db *sql.DB

func main() {
	var dbPath string
	flag.StringVar(&dbPath, "db", "meetping.db", "Path to SQLite DB")
	flag.Parse()

	var err error
	db, err = sql.Open("sqlite3", dbPath)
	if err != nil {
		log.Fatal(err)
	}

	if len(flag.Args()) == 0 {
		log.Fatal("Usage: meetctl [backup|export:csv|adminstats|trigger]")
	}

	switch flag.Args()[0] {
	case "backup":
		backup()
	case "export:csv":
		table := getArg("--table")
		exportTable(table)
	case "adminstats":
		adminStats()
	case "trigger":
		task := getArg("")
		triggerTask(task)
	}
}

func getArg(name string) string {
	for i, arg := range os.Args {
		if arg == name && i+1 < len(os.Args) {
			return os.Args[i+1]
		}
	}
	if name == "" && len(os.Args) > 2 {
		return os.Args[2]
	}
	log.Fatalf("missing required argument: %s", name)
	return ""
}

func backup() {
	zipFile, err := os.Create("backup.zip")
	if err != nil {
		log.Fatal(err)
	}
	defer zipFile.Close()

	w := zip.NewWriter(zipFile)
	defer w.Close()

	files := []string{"meetping.db", "logs/meetping.log"}
	for _, file := range files {
		f, err := os.Open(file)
		if err != nil {
			continue
		}
		defer f.Close()

		wr, _ := w.Create(filepath.Base(file))
		_, _ = wr.ReadFrom(f)
	}
	fmt.Println("✔ Backup saved to backup.zip")
}

func exportTable(table string) {
	rows, err := db.Query(fmt.Sprintf("SELECT * FROM %s", table))
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	cols, _ := rows.Columns()
	writer := csv.NewWriter(os.Stdout)
	defer writer.Flush()
	writer.Write(cols)

	values := make([]interface{}, len(cols))
	pointers := make([]interface{}, len(cols))

	for i := range values {
		pointers[i] = &values[i]
	}

	for rows.Next() {
		rows.Scan(pointers...)
		record := make([]string, len(cols
