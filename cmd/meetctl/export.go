package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"log"
	"os"
)

func ExportCSV(db *sql.DB, table string) {
	rows, err := db.Query("SELECT * FROM " + table)
	if err != nil {
		log.Fatalf("Ошибка запроса: %v", err)
	}
	defer rows.Close()

	cols, _ := rows.Columns()
	csvWriter := csv.NewWriter(os.Stdout)
	_ = csvWriter.Write(cols)

	values := make([]interface{}, len(cols))
	ptrs := make([]interface{}, len(cols))

	for i := range values {
		ptrs[i] = &values[i]
	}

	for rows.Next() {
		_ = rows.Scan(ptrs...)
		record := make([]string, len(values))
		for i, val := range values {
			if val != nil {
				record[i] = fmt.Sprintf("%v", val)
			}
		}
		csvWriter.Write(record)
	}
	csvWriter.Flush()
}
