run:
	go run ./cmd/bot/main.go

build:
	go build -o bin/meetping ./cmd/bot

lint:
	golangci-lint run

test:
	go test ./...

migrate-up:
	goose -dir ./migrations sqlite3 meetping.db up

migrate-down:
	goose -dir ./migrations sqlite3 meetping.db down

logs:
	tail -f ./logs/meetping.log

run-original:
	go run ./cmd/bot_original

run-test:
	go run ./cmd/bot_test

dev:
  air