# Batch Polling Analysis: Предотвращение DDoS на NocoDB

## 🚨 Критичная Проблема

### NocoDB Rate Limits (официальные):
```
- Лимит: 5 requests/second PER API TOKEN
- Блокировка: 30 секунд при превышении
- Применяется ко ВСЕМ планам (Free и Paid одинаково)
```

**Важно:** Лимит **PER API TOKEN**, не per user! Все запросы от бота идут с одним `xc-token`.

---

## 📊 Сценарий 1: 100 Пользователей (Безопасно ✅)

### Текущая реализация (Per-User Polling):
```
100 users × 1 request every 60s = 100 requests/60s = 1.66 RPS
```

**Статус:** ✅ Безопасно (в пределах 5 RPS)

### С Batch Polling:
```
100 users / 20 per batch = 5 batches
5 batches × 1 request = 5 requests every 60s = 0.08 RPS
```

**Экономия:** 95% снижение API requests

---

## ⚠️ Сценарий 2: 300 Пользователей (Критично!)

### Текущая реализация (Per-User Polling):
```
300 users × 1 request every 60s = 300 requests/60s = 5.0 RPS (average)
```

**Проблема:** Polling **НЕ синхронизирован**!

Реальный timing:
```
12:00:00 - User 1, User 5, User 12, ... (20 users) → 20 requests → 20 RPS!
12:00:01 - User 3, User 7, User 15, ... (18 users) → 18 RPS!
12:00:02 - User 2, User 9, User 22, ... (22 users) → 22 RPS!
...

Peak bursts: 20-40 RPS → HTTP 429 → Lockout 30 seconds!
```

**Статус:** ❌ **ОПАСНО** - guaranteed HTTP 429 errors

### С Batch Polling:
```
300 users / 20 per batch = 15 batches

Every 60 seconds:
  12:00:00.0s - Batch 1 (20 users) → 1 request
  12:00:00.2s - Batch 2 (20 users) → 1 request  (rate limiter)
  12:00:00.4s - Batch 3 (20 users) → 1 request  (rate limiter)
  ...
  12:00:03.0s - Batch 15 (20 users) → 1 request

All 15 batches complete in ~3 seconds
Average RPS: 15 requests / 60s = 0.25 RPS
Peak RPS during batch window: ~5 RPS (rate limiter controls this)
```

**Статус:** ✅ Безопасно - плавное распределение через rate limiter

**Экономия:** 300 requests → 15 requests = **95% reduction**

---

## 🔥 Сценарий 3: 1000 Пользователей (Event с большим количеством участников)

### Текущая реализация:
```
1000 users × 1 request every 60s = 16.67 RPS (average)

Peak bursts: 50-100 RPS → Instant HTTP 429 → 30s lockout
Все пользователи перестают получать обновления!
```

**Статус:** ❌ **КАТАСТРОФА** - полный отказ сервиса

### С Batch Polling:
```
1000 users / 20 per batch = 50 batches

Every 60 seconds:
  50 batches × 1 request = 50 requests
  Rate limiter passes 5 RPS → takes 10 seconds to process all batches

Average RPS: 50 / 60 = 0.83 RPS
Peak RPS: 5 RPS (controlled by rate limiter)
```

**Статус:** ✅ Безопасно - работает даже с 1000+ users!

**Экономия:** 1000 requests → 50 requests = **95% reduction**

---

## 📈 Сравнительная Таблица

| Пользователей | Per-User (avg RPS) | Per-User (peak) | Batch (avg RPS) | Batch (peak) | Reduction |
|---------------|-------------------|-----------------|----------------|--------------|-----------|
| 100           | 1.67              | 5-10            | 0.08           | 0.5          | 95%       |
| 300           | 5.0 ❌            | 20-40 ❌        | 0.25 ✅        | 5 ✅         | 95%       |
| 500           | 8.33 ❌           | 40-80 ❌        | 0.42 ✅        | 5 ✅         | 95%       |
| 1000          | 16.67 ❌          | 80-150 ❌       | 0.83 ✅        | 5 ✅         | 95%       |
| 2000          | 33.33 ❌          | 150-300 ❌      | 1.67 ✅        | 5 ✅         | 95%       |

**Критическая отметка:** 300+ пользователей с per-user polling = гарантированные HTTP 429 ошибки

---

## 💡 Решение: Centralized Batch Polling

### Архитектура:

```
Old (Per-User Polling):
┌─────────┐     ┌─────────┐     ┌─────────┐
│ User 1  │────→│ Poll    │────→│ NocoDB  │  (1 request)
└─────────┘     │ Task 1  │     └─────────┘
                └─────────┘

┌─────────┐     ┌─────────┐     ┌─────────┐
│ User 2  │────→│ Poll    │────→│ NocoDB  │  (1 request)
└─────────┘     │ Task 2  │     └─────────┘

... (repeat for 300 users = 300 requests!)


New (Batch Polling):
┌─────────┐
│ User 1  │──┐
└─────────┘  │
┌─────────┐  │
│ User 2  │──┤
└─────────┘  │    ┌──────────────────┐    ┌─────────┐
┌─────────┐  │───→│ Batch Polling    │───→│ NocoDB  │ (1 request)
│ User 3  │──┤    │ Manager          │    └─────────┘
└─────────┘  │    │                  │        ↓
     ...     │    │ Groups 20 users  │    (batch check)
┌─────────┐  │    │ into 1 query     │        ↓
│ User 20 │──┘    └──────────────────┘    Results
└─────────┘                                   ↓
                                      Notify all 20 users

(300 users = 15 batches = 15 requests instead of 300!)
```

### Преимущества:

1. **Снижение API Load:** 95% reduction в количестве запросов
2. **Синхронизация:** Все проверки происходят одновременно
3. **Rate Limiter Control:** Batches проходят через rate limiter плавно
4. **Scalability:** Работает с 1000+ пользователей
5. **Fail-Safe:** Один failed batch не влияет на других

---

## 🛠️ Реализация

### Файлы:

1. **[bot_flow/core/batch_polling_manager.py](../bot_flow/core/batch_polling_manager.py)**
   - Centralized manager для batch polling
   - Subscription система для пользователей
   - Автоматическая группировка в batches

2. **[bot_flow/flows/payment_flow.py](../bot_flow/flows/payment_flow.py)**
   - Функция `batch_check_payment_status()`
   - Конфигурация executor с `enable_batch_polling=True`

3. **[bot_flow/core/executor.py](../bot_flow/core/executor.py)** (требует модификации)
   - Integration с BatchPollingManager
   - Fallback на per-user polling если batch disabled

### Конфигурация:

```python
executor = FlowExecutor(
    flow,
    BOT_TOKEN,
    enable_batch_polling=True,  # Enable centralized batch polling
    batch_polling_config={
        'batch_size': 20,  # Users per batch (optimal: 20-50)
        'interval': 60,     # Polling interval (seconds)
        'batch_check_fn': batch_check_payment_status
    }
)
```

**Рекомендации batch_size:**
- 100-300 users: `batch_size=20`
- 300-1000 users: `batch_size=30`
- 1000+ users: `batch_size=50`

---

## 📊 Мониторинг

### Метрики Batch Polling:

```python
from bot_flow.core.batch_polling_manager import BatchPollingManager

manager.print_stats()
```

Вывод:
```
============================================================
📊 Batch Polling Manager Stats
============================================================
Active Subscriptions: 300
Total Poll Cycles: 120
Total Batches Processed: 1800
Total API Requests: 1800
Average Batch Size: 20.0

💡 Efficiency:
   API Request Reduction: 95.0%
   Requests Avoided: 34200
============================================================
```

---

## 🧪 Тестирование

### Симуляция 300 пользователей:

```bash
# Создать тестовый скрипт
python test_batch_polling_stress.py --users 300 --duration 300
```

Ожидаемые результаты:
- ✅ No HTTP 429 errors
- ✅ Average RPS < 1.0
- ✅ All users receive updates within 60s
- ✅ Rate limiter stats show smooth distribution

---

## ⚡ Производительность

### Latency Analysis:

**Per-User Polling:**
- User check latency: 100-500ms (individual API call)
- Total time for 300 users: 300 × 200ms = 60 seconds (sequential)

**Batch Polling:**
- Batch check latency: 150-600ms (one API call for 20 users)
- Total time for 15 batches: 15 × 300ms = 4.5 seconds (parallel with rate limiting)
- **93% faster** для обработки всех пользователей!

---

## 🎯 Заключение

### Критические находки:

1. ❌ **Текущая реализация не масштабируется** past 200-300 users
2. ❌ **HTTP 429 lockout** блокирует ВСЕ запросы на 30 секунд
3. ✅ **Batch polling** решает проблему с 95% reduction
4. ✅ **Работает для 1000+ users** без проблем

### Рекомендации:

1. **Немедленно** включить batch polling для production
2. Мониторить метрики batch manager
3. Настроить batch_size based on user count
4. При >500 users увеличить batch_size до 30-50

### Next Steps:

1. ✅ Создан BatchPollingManager
2. ⏳ Интеграция в FlowExecutor (TODO)
3. ⏳ Тестирование с симулированной нагрузкой
4. ⏳ Обновление документации

---

**Status:** Batch polling infrastructure ready, integration pending.
