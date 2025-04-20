package admin

import (
	"fmt"
)

func GenerateStats() string {
	return fmt.Sprintf("Пользователей: %d\nСобытий: %d", 123, 42)
}
