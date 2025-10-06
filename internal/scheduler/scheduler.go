package scheduler

import (
	"time"

	"meetping/internal/repo"
	"meetping/internal/service"
)

type CronJobs struct {
	Repo    *repo.Repository
	Digests *service.DigestService
	BotSend func(user repo.User, items []service.DigestItem) // passed from bot
}

func (c *CronJobs) Start() {
	go c.runDigestLoop()
	go c.runFakeActivity()
	go c.runReminders()
	go c.runFeedbackRequests()
}

// 📨 Рассылка дайджестов по digest_time
func (c *CronJobs) runDigestLoop() {
	ticker := time.NewTicker(1 * time.Minute)
	for range ticker.C {
		now := time.Now().Format("15:04")
		users, _ := c.Repo.GetUsersByDigestTime(now)
		for _, u := range users {
			cityID := c.Repo.GetPrimaryCityID(u.ID)
			events, _ := c.Digests.GetDigestForUser(u.ID, cityID)
			if len(events) > 0 {
				c.BotSend(u, events)
			}
		}
	}
}

// 🤖 Фейковая активность (раз в 5 мин)
func (c *CronJobs) runFakeActivity() {
	ticker := time.NewTicker(5 * time.Minute)
	for range ticker.C {
		eventIDs := c.Repo.GetActiveEvents()
		for _, eid := range eventIDs {
			_ = c.Repo.InsertFakeScore(eid, "like")
		}
	}
}

// 🔔 Напоминание за 30 мин до события
func (c *CronJobs) runReminders() {
	ticker := time.NewTicker(5 * time.Minute)
	for range ticker.C {
		upcoming := c.Repo.GetUpcomingRSVPs(30 * time.Minute)
		for _, pair := range upcoming {
			user := c.Repo.GetUserByID(pair.UserID)
			event := c.Repo.GetEventByID(pair.EventID)
			msg := service.DigestItem{
				EventID:     event.ID,
				Title:       "⏰ Напоминание: " + event.Title,
				Description: event.Description,
				Date:        event.Date,
			}
			c.BotSend(user, []service.DigestItem{msg})
		}
	}
}

// 📝 Фидбэк после окончания событий
func (c *CronJobs) runFeedbackRequests() {
	ticker := time.NewTicker(10 * time.Minute)
	for range ticker.C {
		ended := c.Repo.GetPastRSVPsWithoutFeedback()
		for _, pair := range ended {
			user := c.Repo.GetUserByID(pair.UserID)
			msg := service.DigestItem{
				EventID:     pair.EventID,
				Title:       "🙏 Поделитесь впечатлением",
				Description: "Как вам мероприятие?",
			}
			c.BotSend(user, []service.DigestItem{msg})
		}
	}
}
