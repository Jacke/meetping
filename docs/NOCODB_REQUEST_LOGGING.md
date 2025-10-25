# NocoDB Request Logging

Все запросы к NocoDB API теперь логируются в детальном формате для мониторинга и отладки.

## Формат Логов

### Исходящий запрос:
```
📤 [14:23:45.123] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(TG ID,eq,12345), limit=1
```

### Ответ:
```
✅ [14:23:45.456] NocoDB Response: 200 in 0.333s
   Size: 1245 bytes
   Records: 1
   📊 Total requests: 15 (✅ 14, ❌ 0, 🚫 1)
```

## Статусные Emoji

| Emoji | Статус | Описание |
|-------|--------|----------|
| ✅ | 200-299 | Успешный запрос |
| ⚠️ | 400-499 | Ошибка клиента (кроме 429) |
| 🚫 | 429 | Rate limit exceeded |
| ❌ | 500+ | Ошибка сервера |

## Примеры Логов

### 1. Загрузка текстов (с кешем)

**Первый запрос (cache miss):**
```
📤 [12:00:00.100] NocoDB Request:
   Method: GET
   Endpoint: tables/mguawvnumqrb5k7/records
✅ [12:00:00.350] NocoDB Response: 200 in 0.250s
   Size: 3420 bytes
   Records: 8
   📊 Total requests: 1 (✅ 1, ❌ 0, 🚫 0)
✅ Loaded 8 texts from NocoDB (cache: False)
```

**Второй запрос через 10 секунд (cache hit):**
```
✅ Loaded 8 texts from NocoDB (cache: True)
```
*(No API request - served from cache!)*

---

### 2. Проверка регистрации пользователя

```
📤 [12:01:15.200] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(TG ID,eq,123456789), limit=1
✅ [12:01:15.450] NocoDB Response: 200 in 0.250s
   Size: 512 bytes
   Records: 1
   📊 Total requests: 2 (✅ 2, ❌ 0, 🚫 0)
✅ Found existing registration for user 123456789, record: rec_abc123, paid: True
```

---

### 3. Создание payment record

```
📤 [12:02:30.100] NocoDB Request:
   Method: POST
   Endpoint: tables/mfaob33z2nnrxve/records
   Body: {'TG': 'username', 'TG ID': 123456789, 'FullName': 'John Doe', 'Price': 1000, 'Paid': False}
✅ [12:02:30.500] NocoDB Response: 200 in 0.400s
   Size: 256 bytes
   Record ID: rec_xyz789
   📊 Total requests: 3 (✅ 3, ❌ 0, 🚫 0)
✅ Created NocoDB record: rec_xyz789 for user 123456789 (John Doe)
```

---

### 4. Batch проверка статусов (300 пользователей)

**Batch 1:**
```
📤 [12:03:00.000] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(Id,in,rec1,rec2,rec3,...,rec20), limit=20, fields=Id,Paid
✅ [12:03:00.280] NocoDB Response: 200 in 0.280s
   Size: 890 bytes
   Records: 20
   📊 Total requests: 4 (✅ 4, ❌ 0, 🚫 0)
   ✅ Batch 1/15: 3 paid, 17 pending
```

**Batch 2 (rate limited):**
```
⏱️  Rate limiter: waited 0.2s before NocoDB request

📤 [12:03:00.480] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(Id,in,rec21,rec22,...,rec40), limit=20, fields=Id,Paid
✅ [12:03:00.750] NocoDB Response: 200 in 0.270s
   Size: 905 bytes
   Records: 20
   📊 Total requests: 5 (✅ 5, ❌ 0, 🚫 0)
   ✅ Batch 2/15: 5 paid, 15 pending
```

... (batches 3-15)

**Summary:**
```
✅ Batch polling completed. Next check in 60s

📊 Batch Polling Stats:
   300 users checked in 15 batches
   Total time: 3.2 seconds
   API requests: 15 (instead of 300!)
   Reduction: 95%
```

---

### 5. Rate Limit (429) с retry

```
📤 [12:05:00.100] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
🚫 [12:05:00.200] NocoDB Response: 429 in 0.100s
   Size: 128 bytes
   📊 Total requests: 50 (✅ 48, ❌ 0, 🚫 2)
⚠️  Rate limit (429) from NocoDB, retrying in 3.2s (attempt 1/5)

📤 [12:05:03.400] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
✅ [12:05:03.650] NocoDB Response: 200 in 0.250s
   Size: 512 bytes
   Records: 1
   📊 Total requests: 51 (✅ 49, ❌ 0, 🚫 2)
```

---

## Счетчики Запросов

### Глобальные счетчики:
```python
from bot_flow.flows.nocodb_utils import get_request_stats

stats = get_request_stats()
# {
#     'total': 156,
#     'success': 150,
#     'failed': 3,
#     'rate_limited': 3
# }
```

### Интерпретация:
- **total**: Общее количество запросов с момента старта
- **success**: Успешные запросы (200-299)
- **failed**: Ошибки клиента/сервера (400+, кроме 429)
- **rate_limited**: Количество HTTP 429 ответов

### Мониторинг в реальном времени:
Счетчики показываются после **каждого** запроса:
```
📊 Total requests: 156 (✅ 150, ❌ 3, 🚫 3)
```

---

## Анализ Логов

### Признаки проблем:

**1. Высокий rate_limited count:**
```
📊 Total requests: 100 (✅ 70, ❌ 0, 🚫 30)
```
→ **Проблема:** Слишком много 429 ошибок (30%)
→ **Решение:** Увеличить `interval` в polling или снизить `requests_per_second` в rate limiter

**2. Частые retry:**
```
⚠️  Rate limit (429) from NocoDB, retrying in 3.2s (attempt 1/5)
⚠️  Rate limit (429) from NocoDB, retrying in 6.5s (attempt 2/5)
⚠️  Rate limit (429) from NocoDB, retrying in 12.8s (attempt 3/5)
```
→ **Проблема:** Burst трафик превышает лимиты
→ **Решение:** Включить batch polling (`enable_batch_polling=True`)

**3. Низкий cache hit rate:**
```
📤 [12:00:00.100] NocoDB Request: GET tables/mguawvnumqrb5k7/records
✅ Loaded 8 texts from NocoDB (cache: False)

📤 [12:00:15.200] NocoDB Request: GET tables/mguawvnumqrb5k7/records
✅ Loaded 8 texts from NocoDB (cache: False)

📤 [12:00:30.300] NocoDB Request: GET tables/mguawvnumqrb5k7/records
✅ Loaded 8 texts from NocoDB (cache: False)
```
→ **Проблема:** Кеш не работает (каждый запрос идет в API)
→ **Решение:** Проверить `use_cache=True` в load_texts/config

**4. Долгие response times:**
```
✅ NocoDB Response: 200 in 2.500s  # Медленно!
```
→ **Проблема:** NocoDB API slow
→ **Решение:** Проверить network, возможно rate limiting на NocoDB стороне

---

## Фильтрация Логов

### Показать только ошибки:
```bash
python main.py payment 2>&1 | grep -E "(❌|🚫|⚠️)"
```

### Показать только NocoDB запросы:
```bash
python main.py payment 2>&1 | grep -E "(📤|✅|❌|🚫) \[.*\] NocoDB"
```

### Подсчитать total requests за сессию:
```bash
python main.py payment 2>&1 | grep "📊 Total requests" | tail -1
```

### Отследить rate limiting:
```bash
python main.py payment 2>&1 | grep "429"
```

---

## Best Practices

### 1. Мониторить логи в production:

```bash
# Redirect logs to file
python main.py payment 2>&1 | tee logs/nocodb_requests.log
```

### 2. Анализировать после завершения:

```bash
# Подсчитать успешные запросы
grep "✅.*NocoDB Response" logs/nocodb_requests.log | wc -l

# Подсчитать 429 ошибки
grep "🚫.*NocoDB Response: 429" logs/nocodb_requests.log | wc -l

# Средний response time
grep "NocoDB Response" logs/nocodb_requests.log | \
  grep -oE "[0-9]+\.[0-9]+s" | \
  grep -oE "[0-9]+\.[0-9]+" | \
  awk '{sum+=$1; count++} END {print sum/count "s"}'
```

### 3. Alerts для production:

Если `rate_limited` > 10% от `total`:
```python
stats = get_request_stats()
rate_limit_percent = stats['rate_limited'] / stats['total'] * 100

if rate_limit_percent > 10:
    print("⚠️  WARNING: High rate limit errors! Consider enabling batch polling")
```

---

## Troubleshooting

### Логи не отображаются?

**Проверьте:**
1. Запущен ли бот через `python main.py payment` (не через другой runner)
2. Python buffering: добавьте `PYTHONUNBUFFERED=1`
   ```bash
   PYTHONUNBUFFERED=1 python main.py payment
   ```

### Слишком много логов?

**Отключите детальное логирование:**
Закомментируйте print statements в `nocodb_utils.py` (строки 93-167)

**Или перенаправьте в файл:**
```bash
python main.py payment > logs/output.log 2>&1
```

---

## Пример Полной Сессии

```
🚀 Starting payment bot...

📥 Loading texts and config from NocoDB...

📤 [12:00:00.100] NocoDB Request:
   Method: GET
   Endpoint: tables/mguawvnumqrb5k7/records
✅ [12:00:00.350] NocoDB Response: 200 in 0.250s
   Size: 3420 bytes
   Records: 8
   📊 Total requests: 1 (✅ 1, ❌ 0, 🚫 0)
✅ Loaded 8 texts from NocoDB (cache: False)

📤 [12:00:00.400] NocoDB Request:
   Method: GET
   Endpoint: tables/mguawvnumqrb5k7/records
✅ [12:00:00.650] NocoDB Response: 200 in 0.250s
   Size: 1245 bytes
   Records: 3
   📊 Total requests: 2 (✅ 2, ❌ 0, 🚫 0)
✅ Loaded 3 config values from NocoDB (cache: False)

✅ Texts and config validated successfully

📥 Loading users in awaiting_payment state from NocoDB...

📤 [12:00:01.000] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(Paid,eq,false), limit=1000
✅ [12:00:01.300] NocoDB Response: 200 in 0.300s
   Size: 15600 bytes
   Records: 45
   📊 Total requests: 3 (✅ 3, ❌ 0, 🚫 0)

📊 Found 45 users awaiting payment
🚀 Centralized batch polling started (interval: 60s, batch_size: 20)

✅ Bot started successfully!

--- User interaction ---

📤 [12:00:15.100] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(TG ID,eq,123456789), limit=1
✅ [12:00:15.350] NocoDB Response: 200 in 0.250s
   Size: 512 bytes
   Records: 0
   📊 Total requests: 4 (✅ 4, ❌ 0, 🚫 0)
ℹ️ No existing registration for user 123456789

✅ Loaded 8 texts from NocoDB (cache: True)  # Cache hit!
✅ Loaded 3 config values from NocoDB (cache: True)  # Cache hit!

📤 [12:00:20.500] NocoDB Request:
   Method: POST
   Endpoint: tables/mfaob33z2nnrxve/records
   Body: {'TG': 'newuser', 'TG ID': 123456789, 'FullName': 'New User', 'Price': 1000, 'Paid': False}
✅ [12:00:20.850] NocoDB Response: 200 in 0.350s
   Size: 256 bytes
   Record ID: rec_new123
   📊 Total requests: 5 (✅ 5, ❌ 0, 🚫 0)
✅ Created NocoDB record: rec_new123 for user 123456789 (New User)
✅ User 123456789 subscribed to batch polling (record: rec_new123)
📊 Active subscriptions: 46

--- Batch polling cycle (60s) ---

🔍 Checking 46 payment records in batches of 20...
📦 Processing 3 batches...

   Batch 1/3: checking 20 records...
📤 [12:01:00.000] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(Id,in,rec1,rec2,...,rec20), limit=20, fields=Id,Paid
✅ [12:01:00.280] NocoDB Response: 200 in 0.280s
   Size: 890 bytes
   Records: 20
   📊 Total requests: 6 (✅ 6, ❌ 0, 🚫 0)
   ✅ Batch 1/3: 5 paid, 15 pending

⏱️  Rate limiter: waited 0.2s before NocoDB request

   Batch 2/3: checking 20 records...
📤 [12:01:00.480] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(Id,in,rec21,rec22,...,rec40), limit=20, fields=Id,Paid
✅ [12:01:00.750] NocoDB Response: 200 in 0.270s
   Size: 905 bytes
   Records: 20
   📊 Total requests: 7 (✅ 7, ❌ 0, 🚫 0)
   ✅ Batch 2/3: 8 paid, 12 pending

   Batch 3/3: checking 6 records...
📤 [12:01:00.950] NocoDB Request:
   Method: GET
   Endpoint: tables/mfaob33z2nnrxve/records
   Params: where=(Id,in,rec41,rec42,...,rec46), limit=6, fields=Id,Paid
✅ [12:01:01.180] NocoDB Response: 200 in 0.230s
   Size: 345 bytes
   Records: 6
   📊 Total requests: 8 (✅ 8, ❌ 0, 🚫 0)
   ✅ Batch 3/3: 2 paid, 4 pending

✅ Batch polling completed. Next check in 60s

🔕 User 12345 unsubscribed from batch polling
🔕 User 67890 unsubscribed from batch polling
... (15 users received payment confirmation)

📊 Active subscriptions: 31
```

---

**Теперь ты видишь каждый запрос к NocoDB в реальном времени!** 🎉
