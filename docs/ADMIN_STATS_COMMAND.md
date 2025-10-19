# Admin Features Guide

## Обзор

Бот предоставляет специальные возможности для администраторов:

1. **Команда `/stats`** - просмотр статистики регистраций
2. **Ссылка на NocoDB в уведомлениях** - быстрый доступ к базе данных при переходе пользователя в состояние ожидания оплаты

---

## 1. Команда `/stats`

Команда `/stats` доступна **только администраторам** и показывает статистику регистраций из NocoDB.

## Что показывает

```
📊 Статистика регистраций

📝 Всего заявок: 42
✅ Оплачено: 28
⏳ Ожидают оплаты: 14

🔗 Открыть NocoDB
```

### Данные

- **Всего заявок** - общее количество записей в NocoDB
- **Оплачено** - количество записей с `Paid = true`
- **Ожидают оплаты** - количество записей с `Paid = false`
- **Ссылка на NocoDB** - прямая ссылка для открытия таблицы

## Как это работает

### Видимость команды

**Обычные пользователи:**
```
/start   Начать регистрацию на мероприятие
```

**Администраторы:**
```
/start   Начать регистрацию на мероприятие
/stats   Статистика регистраций (только для админов)
```

Команда `/stats` **НЕ ВИДНА** обычным пользователям в меню!

### Технология

Используется **BotCommandScopeChat** из Telegram Bot API для установки команд только для определённых chat_id.

## Настройка

### 1. Убедитесь, что Chat ID админов настроены

В [bot_flow/flows/payment_flow.py](../bot_flow/flows/payment_flow.py:358):

```python
admin_chat_ids = [
    123456789,    # Ваш Chat ID
    987654321,    # Chat ID второго админа
]
```

Если список пустой, команда `/stats` не будет добавлена в меню.

### 2. Запустите бота

```bash
python main.py payment
```

При запуске вы увидите:

```
✅ Set 1 public commands in menu
✅ Set 2 commands for admin 123456789
✅ Set 2 commands for admin 987654321
```

### 3. Проверьте меню команд

Откройте бота в Telegram и нажмите кнопку "☰":

- Если вы **админ** - увидите `/start` и `/stats`
- Если вы **обычный пользователь** - увидите только `/start`

## Использование

### Как админ

1. Откройте бота в Telegram
2. Нажмите "☰" → выберите `/stats`
3. Или просто напишите `/stats`
4. Получите статистику

### Пример ответа

```
📊 Статистика регистраций

📝 Всего заявок: 150
✅ Оплачено: 120
⏳ Ожидают оплаты: 30

🔗 Открыть NocoDB
```

Кликните на "Открыть NocoDB" для перехода в таблицу.

---

## 2. NocoDB Link в уведомлениях о переходах

Когда пользователь переходит в состояние `awaiting_payment` (ожидание оплаты), администраторы получают уведомление **с прямой ссылкой на NocoDB**.

### Пример уведомления

```text
🔔 State Change

User: @username (ID: 123456789)
State: payment_info → awaiting_payment

🔗 Открыть NocoDB
```

### Когда отправляется

Уведомления с ссылкой на NocoDB отправляются админам при переходах:

- **`payment_info → awaiting_payment`** - пользователь создал заявку и ожидает оплаты (❗ **с ссылкой на NocoDB**)
- **`awaiting_payment → success`** - оплата подтверждена (без ссылки)

### Настройка

Ссылка на NocoDB автоматически добавляется если в `payment_flow.py` переданы параметры:

```python
executor = FlowExecutor(
    flow,
    BOT_TOKEN,
    admin_chat_ids=admin_chat_ids,
    nocodb_url=NOCODB_API_URL,          # ✅ Обязательно
    nocodb_table_id=NOCODB_TABLE_ID     # ✅ Обязательно
)
```

Если параметры не переданы, уведомления всё равно будут отправляться, но **без ссылки**.

### Преимущества

- **Быстрый доступ** - кликните на ссылку и сразу окажетесь в NocoDB
- **Удобно на мобильном** - не нужно искать таблицу вручную
- **Контекстуально** - ссылка появляется только когда это важно (при ожидании оплаты)

---

## Добавление других admin команд

### 1. Создайте функцию

```python
async def admin_action(ctx: FlowContext) -> None:
    """Do something only admins can do"""
    await ctx.update.message.reply_text(
        "Admin action executed!",
        parse_mode="HTML"
    )
```

### 2. Добавьте состояние в flow

```python
.state("admin_command")
    .on_command("/admin")
    .action(admin_action)
    .final()
```

### 3. Добавьте в список admin команд

В [executor.py:315](../bot_flow/core/executor.py:315):

```python
# Admin-only commands
admin_commands = {'stats', 'admin'}  # Добавьте новую команду
```

### 4. Добавьте описание

В [executor.py:309-311](../bot_flow/core/executor.py:309-311):

```python
command_descriptions = {
    'start': 'Начать регистрацию на мероприятие',
    'stats': 'Статистика регистраций (только для админов)',
    'admin': 'Административная панель',  # Новое описание
}
```

## Безопасность

### Команда доступна только админам в меню

✅ **Меню:** Команда `/stats` видна только админам

⚠️ **Прямой вызов:** Любой пользователь может написать `/stats` вручную!

### Добавление проверки прав

Если хотите заблокировать команду для не-админов:

```python
async def get_statistics(ctx: FlowContext) -> None:
    """Get statistics from NocoDB (admin only)"""
    # Check if user is admin
    admin_chat_ids = [123456789, 987654321]  # Можно передать через config

    if ctx.user.id not in admin_chat_ids:
        await ctx.update.message.reply_text(
            "⛔️ Эта команда доступна только администраторам",
            parse_mode="HTML"
        )
        return

    # ... rest of the code
```

## Кастомизация статистики

### Добавить больше данных

```python
# Calculate more statistics
total = len(records)
paid = sum(1 for r in records if r.get("Paid") is True)
unpaid = total - paid

# New: Calculate today's registrations
from datetime import datetime, timedelta
today = datetime.now().date()
today_records = [
    r for r in records
    if r.get("CreatedAt") and
    datetime.fromisoformat(r["CreatedAt"].replace('Z', '+00:00')).date() == today
]
today_count = len(today_records)

# Format message
message = f"""
📊 <b>Статистика регистраций</b>

📝 Всего заявок: <b>{total}</b>
✅ Оплачено: <b>{paid}</b>
⏳ Ожидают оплаты: <b>{unpaid}</b>
🆕 Сегодня: <b>{today_count}</b>

🔗 <a href="{NOCODB_API_URL}/#/nc/{NOCODB_TABLE_ID}">Открыть NocoDB</a>
"""
```

### Добавить график

```python
# Calculate conversion rate
conversion_rate = (paid / total * 100) if total > 0 else 0

message = f"""
📊 <b>Статистика регистраций</b>

📝 Всего заявок: <b>{total}</b>
✅ Оплачено: <b>{paid}</b> ({conversion_rate:.1f}%)
⏳ Ожидают оплаты: <b>{unpaid}</b>

Progress: {'█' * int(conversion_rate / 10)}{'░' * (10 - int(conversion_rate / 10))} {conversion_rate:.1f}%

🔗 <a href="{NOCODB_API_URL}/#/nc/{NOCODB_TABLE_ID}">Открыть NocoDB</a>
"""
```

## Troubleshooting

### Команда не видна админу

**Проблема:** Админ не видит `/stats` в меню

**Решения:**

1. **Проверьте Chat ID:**
   ```python
   # В payment_flow.py
   admin_chat_ids = [123456789]  # Убедитесь, что ваш ID здесь
   ```

2. **Проверьте логи при запуске:**
   ```
   ✅ Set 2 commands for admin 123456789
   ```

3. **Перезапустите бота:**
   ```bash
   # Остановите бота (Ctrl+C)
   python main.py payment
   ```

4. **Перезапустите Telegram:**
   - Закройте приложение Telegram
   - Откройте заново
   - Команды обновятся

### Ошибка "Chat not found"

**Проблема:**
```
⚠️ Failed to set admin commands for 123456789: Chat not found
```

**Решение:**

Админ должен **сначала написать боту** `/start`:

1. Откройте бота в Telegram
2. Отправьте `/start`
3. Перезапустите бота
4. Команды установятся

### Статистика не загружается

**Проблема:** При вызове `/stats` ошибка

**Решения:**

1. **Проверьте NocoDB конфигурацию:**
   ```bash
   # В .env
   NOCODB_API_TOKEN=your_token
   NOCODB_TABLE_ID=your_table_id
   ```

2. **Проверьте логи:**
   ```
   ❌ Error checking payment status: ...
   ```

3. **Проверьте доступ к NocoDB API:**
   ```bash
   curl -H "xc-token: YOUR_TOKEN" \
     "https://app.nocodb.com/api/v2/tables/TABLE_ID/records?limit=1"
   ```

## Файлы

- [bot_flow/flows/payment_flow.py](../bot_flow/flows/payment_flow.py:90-145) - Функция `get_statistics()`
- [bot_flow/flows/payment_flow.py](../bot_flow/flows/payment_flow.py:364-367) - Состояние `stats`
- [bot_flow/core/executor.py](../bot_flow/core/executor.py:304-349) - Установка команд с scope

## Summary

✅ **Команда /stats** видна только админам в меню

✅ **Статистика из NocoDB** - всего заявок, оплачено, ожидают

✅ **Ссылка на NocoDB** - прямой переход в таблицу

✅ **Легко расширяемо** - можно добавлять новые admin команды

✅ **Безопасно** - обычные пользователи не видят команду в меню

🎯 **Готово!** Админы могут быстро получить статистику одной командой!
