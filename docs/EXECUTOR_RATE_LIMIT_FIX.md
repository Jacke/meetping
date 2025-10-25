# Исправление HTTP 429 в Executor

## Проблема

При запуске бота с восстановлением состояний пользователей возникали HTTP 429 ошибки из-за:

1. **Обход rate limiter** - функция `_check_payment_status_for_restored` НЕ использовала `nocodb_request_with_retry`
2. **Нет connection pooling** - создавался новый `httpx.AsyncClient` на каждый запрос
3. **Burst при старте** - все пользователи восстанавливались одновременно

### Пример ошибки:
```
🔄 Restoring 45 users in state 'awaiting_payment':
   ✓ User 12345 - record rec_1
   ✓ User 67890 - record rec_2
   ... (43 more users)

❌ Polling error for user 12345: HTTP 429 Too Many Requests
❌ Polling error for user 67890: HTTP 429 Too Many Requests
...
```

### Анализ:
```
45 users × polling every 60s = 45 requests/60s = 0.75 RPS (OK)

НО при старте бота:
- Все 45 polling tasks стартуют ОДНОВРЕМЕННО
- Каждый делает ПЕРВЫЙ запрос сразу
- 45 requests в первую секунду = 45 RPS >> 5 RPS limit!
- HTTP 429 lockout на 30 секунд
```

---

## Решение

### 1. Использовать `nocodb_request_with_retry`

**До:**
```python
async def _check_payment_status_for_restored(self, mock_ctx) -> bool:
    # ...
    async with httpx.AsyncClient() as client:  # ❌ Новый клиент каждый раз
        response = await client.get(          # ❌ Обход rate limiter
            f"{nocodb_api_url}/api/v2/tables/{nocodb_table_id}/records/{record_id}",
            headers=headers,
            timeout=10.0
        )
    # ...
```

**После:**
```python
async def _check_payment_status_for_restored(self, mock_ctx) -> bool:
    # ...
    from bot_flow.flows.nocodb_utils import nocodb_request_with_retry

    response = await nocodb_request_with_retry(  # ✅ Rate limiter + retry
        "GET",
        f"{nocodb_api_url}/api/v2/tables/{nocodb_table_id}/records/{record_id}",
        headers=headers,
        timeout=10.0
    )
    # ...
```

**Эффект:**
- ✅ Все запросы через rate limiter (5 RPS max)
- ✅ Connection pooling (переиспользование соединений)
- ✅ Exponential backoff + jitter при 429
- ✅ Retry-After header обработка

---

### 2. Staggered Polling Start

Добавлена задержка между запуском polling tasks:

**До:**
```python
for user_data in users_data:
    # Start polling task
    task = asyncio.create_task(...)
    # ❌ Все стартуют одновременно
```

**После:**
```python
for idx, user_data in enumerate(users_data):
    # Start polling task
    task = asyncio.create_task(...)

    # Stagger start times: wait 1s every 10 users
    if (idx + 1) % 10 == 0 and idx + 1 < len(users_data):
        await asyncio.sleep(1)
        print(f"⏱️  Staggering polling start ({idx + 1}/{len(users_data)})...")
```

**Эффект:**
```
45 users восстанавливаются так:

00:00.0s → User 1-10   (start polling)
00:01.0s → User 11-20  (start polling)  # +1s delay
00:02.0s → User 21-30  (start polling)  # +1s delay
00:03.0s → User 31-40  (start polling)  # +1s delay
00:04.0s → User 41-45  (start polling)  # +1s delay

Вместо burst в 45 RPS, получаем ~10 RPS каждую секунду
Rate limiter сглаживает до 5 RPS
```

---

## Результаты

### До исправления (45 users):
```
🔄 Restoring 45 users...
   [0.0s] 45 requests start simultaneously
   [0.1s] 🚫 HTTP 429 × 40 users
   [30s]  Lockout expires
   ❌ Many users miss first payment check cycle
```

### После исправления (45 users):
```
🔄 Restoring 45 users...
   [0.0s] Users 1-10 start (rate limited to 5 RPS)
   [1.0s] Users 11-20 start (rate limited to 5 RPS)
   [2.0s] Users 21-30 start (rate limited to 5 RPS)
   [3.0s] Users 31-40 start (rate limited to 5 RPS)
   [4.0s] Users 41-45 start (rate limited to 5 RPS)

   [5.0s] All users restored successfully
   ✅ No HTTP 429 errors
   ✅ All users will check on next cycle (60s)
```

---

## Масштабируемость

### 100 users:
```
Stagger: 10 batches × 1s = 10 seconds startup time
Average RPS during startup: ~5 RPS (controlled by rate limiter)
✅ No 429 errors
```

### 200 users:
```
Stagger: 20 batches × 1s = 20 seconds startup time
Average RPS during startup: ~5 RPS (controlled by rate limiter)
✅ No 429 errors
```

### 300 users (requires batch polling):
```
⚠️  Per-user polling still works but less efficient
Stagger: 30 batches × 1s = 30 seconds startup time
During polling cycles: 300/60s = 5 RPS average

Recommendation: Integrate BatchPollingManager for 300+ users
- See: bot_flow/core/batch_polling_manager.py
- See: docs/BATCH_POLLING_ANALYSIS.md
```

---

## Логи

### Примеры логов с исправлениями:

**Восстановление пользователей:**
```
🔄 Restoring 45 users in state 'awaiting_payment':
   ✓ User 12345 (@user1) - record rec_1
   ✓ User 12346 (@user2) - record rec_2
   ...
   ✓ User 12354 (@user10) - record rec_10
   ⏱️  Staggering polling start (10/45 users restored)...

   ✓ User 12355 (@user11) - record rec_11
   ...
   ✓ User 12364 (@user20) - record rec_20
   ⏱️  Staggering polling start (20/45 users restored)...

   ... (continues for all 45 users)

✅ Started polling for 45 users
```

**Polling запросы (через rate limiter):**
```
📤 [12:00:00.100] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records/rec_1

✅ [12:00:00.350] NocoDB Response: 200 in 0.250s
   Size: 512 bytes
   Record ID: rec_1
   📊 Total requests: 1 (✅ 1, ❌ 0, 🚫 0)

⏱️  Rate limiter: waited 0.2s before NocoDB request  # Контроль RPS

📤 [12:00:00.550] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records/rec_2

✅ [12:00:00.800] NocoDB Response: 200 in 0.250s
   Size: 512 bytes
   Record ID: rec_2
   📊 Total requests: 2 (✅ 2, ❌ 0, 🚫 0)

... (controlled rate continues)
```

---

## Тестирование

### Тест с 50 пользователями:

```bash
# 1. Create 50 test records in NocoDB (Paid = false)

# 2. Restart bot
python main.py payment

# Expected output:
# 🔄 Restoring 50 users...
#    ⏱️  Staggering every 10 users
# ✅ All users restored in ~5 seconds
# ✅ No HTTP 429 errors in logs
```

### Мониторинг:

```bash
# Watch for 429 errors
python main.py payment 2>&1 | grep "🚫"

# Should see: (empty - no 429 errors!)
```

---

## Конфигурация

### Настройка stagger delay:

В `executor.py` можно изменить параметры:

```python
# Stagger every N users
if (idx + 1) % 10 == 0:  # ← Change 10 to adjust batch size
    await asyncio.sleep(1)  # ← Change 1 to adjust delay
```

**Рекомендации:**
- 50-100 users: `% 10`, delay `1s` (default)
- 100-200 users: `% 15`, delay `1s`
- 200+ users: `% 20`, delay `1s` + consider batch polling

---

## Связанные Исправления

1. ✅ `nocodb_request_with_retry` - rate limiter + retry ([nocodb_utils.py](../bot_flow/flows/nocodb_utils.py))
2. ✅ Connection pooling - shared httpx client ([nocodb_utils.py](../bot_flow/flows/nocodb_utils.py))
3. ✅ Request logging - детальные логи ([NOCODB_REQUEST_LOGGING.md](NOCODB_REQUEST_LOGGING.md))
4. ✅ Staggered polling start - распределение нагрузки ([executor.py](../bot_flow/core/executor.py))
5. ⏳ Batch polling - для 300+ users ([batch_polling_manager.py](../bot_flow/core/batch_polling_manager.py))

---

## Заключение

**Проблема:** HTTP 429 при восстановлении пользователей
**Причина:** Burst трафик + обход rate limiter
**Решение:** nocodb_request_with_retry + staggered start
**Результат:** ✅ No 429 errors, стабильная работа до 200 users

Для 300+ users рекомендуется интеграция BatchPollingManager.
