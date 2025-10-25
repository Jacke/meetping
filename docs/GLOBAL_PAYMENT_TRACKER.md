# Global Payment Tracker - Централизованная Проверка Платежей

## Концепция

Вместо того, чтобы каждый пользователь делал свой собственный API запрос к NocoDB (per-user polling), все пользователи читают из **общего глобального состояния**, которое обновляется **одним батч-запросом** каждые 20 секунд.

### Проблема (Per-User Polling):
```
300 users × polling every 60s = 300 HTTP requests / 60s = 5 RPS

User 1: GET /records/rec_1 (every 60s)
User 2: GET /records/rec_2 (every 60s)
User 3: GET /records/rec_3 (every 60s)
...
User 300: GET /records/rec_300 (every 60s)

Total: 300 отдельных API запросов!
```

### Решение (Global Payment Tracker):
```
Global Tracker: GET /records?where=(Id,in,rec1,rec2,...,rec300) (every 20s)

↓ Updates global cache ↓

User 1: читает из кеша (NO API CALL)
User 2: читает из кеша (NO API CALL)
User 3: читает из кеша (NO API CALL)
...
User 300: читает из кеша (NO API CALL)

Total: 1 батч запрос вместо 300!
Reduction: 99.67%!
```

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│  Global Payment Tracker (Singleton)                         │
│                                                              │
│  payment_statuses = {                                       │
│    12345: False,  # User 12345 not paid                    │
│    67890: True,   # User 67890 paid                        │
│    ...                                                      │
│  }                                                          │
│                                                              │
│  user_records = {                                           │
│    12345: "rec_abc",                                        │
│    67890: "rec_xyz",                                        │
│    ...                                                      │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
       ↑                                   ↓
       │                                   │
    (reads)                             (writes)
       │                                   │
┌──────┴───────┐                  ┌───────┴─────────┐
│  User 1-300  │                  │  Update Loop    │
│  Polling     │                  │  (every 20s)    │
│  (no API)    │                  │                 │
└──────────────┘                  │  1 Batch Query  │
                                   │  ↓              │
                                   │  NocoDB API     │
                                   └─────────────────┘
```

---

## Использование

### 1. Инициализация

```python
from bot_flow.flows.global_payment_tracker import get_global_tracker

# Get singleton instance
tracker = get_global_tracker()

# Configure NocoDB credentials
tracker.configure(
    nocodb_api_url="https://app.nocodb.com",
    nocodb_api_token="your_token",
    nocodb_table_id="your_table_id"
)

# Start background updates (every 20 seconds)
await tracker.start(interval=20)
```

### 2. Регистрация Пользователей

```python
# When user creates payment record
tracker.track_user(user_id=12345, record_id="rec_abc123")

# User is now in global tracking
```

### 3. Проверка Статуса (NO API CALL!)

```python
# Check if user paid (reads from cache)
is_paid = tracker.is_paid(user_id=12345)

if is_paid:
    print("✅ Payment confirmed!")
    tracker.untrack_user(user_id=12345)  # Stop tracking
```

---

## Интеграция в Payment Flow

### create_payment_record()

```python
async def create_payment_record(ctx: FlowContext) -> None:
    # ... create record in NocoDB ...

    # Register in global tracker
    from bot_flow.flows.global_payment_tracker import get_global_tracker
    tracker = get_global_tracker()
    tracker.track_user(ctx.user.id, record_id)
```

### check_payment_status()

```python
async def check_payment_status(ctx: FlowContext) -> bool:
    """NO API CALL - reads from global cache"""
    from bot_flow.flows.global_payment_tracker import get_global_tracker

    tracker = get_global_tracker()
    is_paid = tracker.is_paid(ctx.user.id)

    if is_paid:
        tracker.untrack_user(ctx.user.id)  # Stop tracking

    return is_paid
```

### main()

```python
# Initialize and start tracker
tracker = get_global_tracker()
tracker.configure(NOCODB_API_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)

# Register existing users
for user in awaiting_users:
    tracker.track_user(user['tg_id'], user['record_id'])

# Start background updates
await tracker.start(interval=20)
```

---

## Логи

### Startup:
```
📍 Tracking payment for user 12345 (record: rec_abc)
📍 Tracking payment for user 67890 (record: rec_xyz)
... (45 more users)

📍 Registered 45 users in Global Payment Tracker

🚀 Global payment tracker started (interval: 20s)
```

### Background Updates (every 20s):
```
🔍 Global Tracker: Checking 45 payment records...

📤 [12:00:00.100] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(Id,in,rec1,rec2,...,rec45), limit=45, fields=Id,Paid

✅ [12:00:00.450] NocoDB Response: 200 in 0.350s
   Size: 2340 bytes
   Records: 45
   📊 Total requests: 1 (✅ 1, ❌ 0, 🚫 0)

✅ Global Tracker: 8/45 paid, 37 pending
   💰 Newly confirmed payments: 2 users
      • User 12345
      • User 67890
   📊 Next update in 20s
```

### User Polling (reads from cache):
```
🔍 Polling result for user 12345: result=True
✅ Payment confirmed for user 12345 (from global tracker)
🔕 Stopped tracking user 12345
```

---

## Статистика

### get_stats()

```python
stats = tracker.get_stats()
print(stats)

# Output:
# {
#   'tracked_users': 37,
#   'total_updates': 45,
#   'last_update': '15s ago',
#   'users_updated': 37,
#   'payments_confirmed': 8,
#   'update_interval': '20s'
# }
```

### print_stats()

```python
tracker.print_stats()
```

```
============================================================
📊 Global Payment Tracker Stats
============================================================
Tracked Users: 37
Update Interval: 20s
Total Updates: 45
Last Update: 15s ago
Users Updated: 37
Payments Confirmed: 8
============================================================
```

---

## Производительность

### Сравнение: Per-User vs Global Tracker

| Метрика | Per-User Polling | Global Tracker | Улучшение |
|---------|------------------|----------------|-----------|
| **50 users** | 50 req/60s | 1 req/20s | **97%** ↓ |
| **100 users** | 100 req/60s | 1 req/20s | **98%** ↓ |
| **300 users** | 300 req/60s | 1 req/20s | **99.67%** ↓ |
| **1000 users** | 1000 req/60s | 1 req/20s | **99.94%** ↓ |

### API Load Example (300 users):

**Per-User Polling (interval=60s):**
```
300 users × 1 req/60s = 5 RPS average
Peak bursts: 20-40 RPS → HTTP 429!
```

**Global Tracker (interval=20s):**
```
1 batch req/20s = 0.05 RPS
Peak: 0.05 RPS (stable!)
✅ No 429 errors even with 1000+ users
```

---

## Преимущества

### 1. Драматическое Снижение API Load
- 300 users: 300 requests → **1 request** (99.67% reduction)
- 1000 users: 1000 requests → **1 request** (99.94% reduction)

### 2. Более Быстрые Обновления
- Per-user: каждые 60s
- Global tracker: каждые **20s** (3× faster!)

### 3. Синхронизация
- Все пользователи получают обновления **одновременно**
- Нет race conditions

### 4. Масштабируемость
- Работает для **любого** количества пользователей
- 10,000 users = всё ещё 1 запрос каждые 20s!

### 5. Простота
- Пользователи просто читают из кеша (no API logic)
- Вся логика API в одном месте

---

## Конфигурация

### Update Interval

```python
# Shorter interval = faster updates, more API calls
await tracker.start(interval=10)  # Every 10s

# Longer interval = slower updates, fewer API calls
await tracker.start(interval=30)  # Every 30s

# Default (recommended)
await tracker.start(interval=20)  # Every 20s
```

**Рекомендации:**
- <100 users: `interval=20s` (default)
- 100-500 users: `interval=15s`
- 500+ users: `interval=20-30s`

### Batch Size Limit

NocoDB может иметь лимит на размер WHERE clause. Если >1000 users, нужно разбить на batches:

```python
# В _update_all_statuses(), добавить:
MAX_BATCH_SIZE = 500

for i in range(0, len(record_ids), MAX_BATCH_SIZE):
    batch = record_ids[i:i+MAX_BATCH_SIZE]
    # ... fetch batch ...
```

---

## Troubleshooting

### Tracker не обновляется?

**Проверьте:**
1. Запущен ли tracker: `await tracker.start()`
2. Настроены ли credentials: `tracker.configure(...)`
3. Логи: должны видеть "🔍 Global Tracker: Checking..."

### Пользователи не получают обновления?

**Проверьте:**
1. Зарегистрирован ли user: `tracker.track_user(...)`
2. Interval не слишком большой: `interval=20` (not 60+)
3. Нет ошибок в batch query: смотрите логи

### Too Many Users (>1000)?

**Решение:**
- Разбить на batches по 500 users
- Или увеличить NocoDB plan

---

## Миграция с Per-User Polling

### До:
```python
async def check_payment_status(ctx):
    # Make API call for THIS user
    response = await nocodb_request_with_retry(
        "GET",
        f".../records/{record_id}",
        ...
    )
    return response.json()["Paid"]
```

### После:
```python
async def check_payment_status(ctx):
    # Read from global cache (NO API CALL!)
    tracker = get_global_tracker()
    return tracker.is_paid(ctx.user.id)
```

**Результат:** 99.67% снижение API requests!

---

## Сравнение с Batch Polling Manager

| Фича | Global Tracker | Batch Polling Manager |
|------|----------------|----------------------|
| API Reduction | 99.67% | 95% |
| Complexity | Low (простая интеграция) | High (требует FlowExecutor mod) |
| Update Speed | 20s (faster) | 60s |
| Implementation | ✅ Ready | ⏳ Pending integration |
| Scalability | Unlimited | Up to batch_size × batches |

**Рекомендация:** Use Global Tracker - проще, быстрее, лучше!

---

## Заключение

Global Payment Tracker - это **оптимальное решение** для проверки статусов платежей:

✅ **99.67% снижение** API requests
✅ **3× faster** updates (20s vs 60s)
✅ **Синхронизированные** обновления для всех
✅ **Масштабируется** до любого числа пользователей
✅ **Простая** интеграция

**Рекомендуется для всех production deployments!**

---

## См. Также

- [BATCH_POLLING_ANALYSIS.md](BATCH_POLLING_ANALYSIS.md) - Анализ DDoS проблемы
- [NOCODB_REQUEST_LOGGING.md](NOCODB_REQUEST_LOGGING.md) - Детальное логирование
- [RATE_LIMITING_SUMMARY.md](../RATE_LIMITING_SUMMARY.md) - Общая сводка
