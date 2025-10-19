# Admin Notifications Guide

## Обзор

Бот отправляет уведомления администраторам при каждом изменении состояния пользователя. Это позволяет отслеживать путь пользователя через flow в реальном времени.

## Настройка

### Конфигурация админов

Список администраторов настраивается в [bot_flow/flows/payment_flow.py](../bot_flow/flows/payment_flow.py:358):

```python
# Admin Chat IDs for notifications
admin_chat_ids = [
    123456789,    # @stansob
    987654321,    # @Haleecolemax2
]

# Create and run executor
executor = FlowExecutor(flow, BOT_TOKEN, admin_chat_ids=admin_chat_ids)
```

**Важно:** Используйте **Chat ID** (числа), а не username!

### Как получить Chat ID

**Метод 1: Через @userinfobot (Рекомендуется)**

1. Найдите бота @userinfobot в Telegram
2. Отправьте `/start`
3. Скопируйте ваш ID из ответа

**Метод 2: Подробная инструкция**

См. полное руководство: [HOW_TO_GET_CHAT_ID.md](HOW_TO_GET_CHAT_ID.md)

### Требования

Для получения уведомлений:

1. **Получите ваш Chat ID** (см. выше)
2. **Добавьте Chat ID** в `admin_chat_ids`
3. **Напишите боту `/start`** хотя бы раз (чтобы бот мог отправлять сообщения)

## Формат уведомлений

### Пример уведомления

```
🔔 State Change

User: @stansob (ID: 123456789)
State: START → welcome
```

### Информация в уведомлении

- **User:** Username (или имя) и Telegram ID
- **State:** Переход `from_state → to_state`

## Примеры уведомлений

### Новый пользователь начал оплату

```
🔔 State Change

User: @john_doe (ID: 987654321)
State: payment_info → awaiting_payment
```

Это означает: **пользователь начал процесс оплаты, нужно подтвердить в NocoDB**

### Оплата подтверждена

```
🔔 State Change

User: @john_doe (ID: 987654321)
State: awaiting_payment → success
```

Это означает: **оплата подтверждена, пользователь получил доступ к группе**

## Отслеживаемые события

Уведомления отправляются только для **важных состояний**:

1. **awaiting_payment** - Пользователь начал процесс оплаты (нужно подтвердить в NocoDB)
2. **success** - Оплата подтверждена ✅

**Не отслеживаются** (чтобы не спамить):

- welcome, route_user, show_welcome, payment_pending, already_paid, payment_info

## Flow пользователя с уведомлениями

### Сценарий 1: Новый пользователь

| Действие | State Transition | Уведомление |
|----------|------------------|-------------|
| /start | START → welcome | ❌ |
| Проверка регистрации | welcome → show_welcome | ❌ |
| Нажал "Оплатить" | show_welcome → payment_info | ❌ |
| Создана запись | payment_info → awaiting_payment | ✅ |
| Админ подтвердил | awaiting_payment → success | ✅ |

**Итого:** 2 уведомления (только важные)

### Сценарий 2: Повторный /start (не оплатил)

| Действие | State Transition | Уведомление |
|----------|------------------|-------------|
| /start | START → welcome | ❌ |
| Проверка регистрации | welcome → route_user | ❌ |
| Проверка оплаты | route_user → payment_pending | ❌ |
| Продолжение | payment_pending → awaiting_payment | ✅ |
| Админ подтвердил | awaiting_payment → success | ✅ |

**Итого:** 2 уведомления (только важные)

### Сценарий 3: Уже оплатил

| Действие | State Transition | Уведомление |
|----------|------------------|-------------|
| /start | START → welcome | ❌ |
| Проверка регистрации | welcome → route_user | ❌ |
| Проверка оплаты | route_user → already_paid | ❌ |

**Итого:** 0 уведомлений (пользователь уже оплатил)

## Отключение уведомлений

Чтобы отключить уведомления, передайте пустой список:

```python
# Без уведомлений
executor = FlowExecutor(flow, BOT_TOKEN, admin_usernames=[])

# Или вообще не передавайте параметр
executor = FlowExecutor(flow, BOT_TOKEN)
```

## Добавление админов

Чтобы добавить нового администратора:

```python
admin_usernames = [
    "stansob",
    "Haleecolemax2",
    "new_admin"  # Добавьте новый username
]
```

## Troubleshooting

### Уведомления не приходят

**Проблема:** Бот не может отправить сообщение по username

**Решения:**

1. **Убедитесь, что username правильный** (без @)
2. **Пользователь должен начать диалог сботом:**
   - Найдите бота в Telegram
   - Отправьте `/start`
3. **Проверьте логи:**
   ```
   ⚠️ Failed to notify @username: Forbidden: bot can't initiate...
   ```

**Альтернатива:** Используйте Chat ID вместо username (см. выше)

### Получаю дубликаты уведомлений

**Причина:** Несколько экземпляров бота запущено

**Решение:**
```bash
# Проверьте запущенные процессы
ps aux | grep "main.py payment"

# Остановите дубликаты
kill <PID>
```

### Уведомления приходят с задержкой

**Причина:** Telegram API rate limits

**Решение:** Это нормально для большого количества пользователей. Уведомления будут доставлены, но с небольшой задержкой.

## Безопасность

**Важно:**

- Уведомления содержат Telegram ID пользователей
- Не публикуйте скриншоты уведомлений с ID
- Храните список админов в приватном репозитории

## Расширенная настройка

### Кастомный формат уведомлений

Отредактируйте метод `_notify_admins` в [bot_flow/core/executor.py](../bot_flow/core/executor.py:103-140):

```python
# Добавьте дополните��ьную информацию
message = f"""
🔔 <b>State Change</b>

User: {user_mention} (ID: {user_id})
State: {state_change}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
```

### Изменить список важных состояний

```python
# В executor.py, метод transition_to()
important_states = ['awaiting_payment', 'success']  # Текущие

# Добавить больше состояний
important_states = ['awaiting_payment', 'success', 'payment_info']

# Все состояния
important_states = None  # Удалите проверку if state_name in important_states
```

## API Reference

### FlowExecutor.__init__()

```python
def __init__(
    self,
    flow: Flow,
    bot_token: str,
    admin_usernames: Optional[list] = None
):
    """
    Args:
        flow: Bot flow definition
        bot_token: Telegram bot token
        admin_usernames: List of admin usernames (without @) for notifications
    """
```

### _notify_admins()

```python
async def _notify_admins(
    self,
    user_id: int,
    username: str,
    first_name: str,
    from_state: Optional[str],
    to_state: str
) -> None:
    """
    Send notification to admin users about state change.

    Args:
        user_id: Telegram user ID
        username: User's username
        first_name: User's first name
        from_state: Previous state (None if first interaction)
        to_state: New state
    """
```

## Примеры использования

### Мониторинг в реальном времени

Администраторы могут:

1. **Отслеживать активность** - видеть, когда пользователи начинают регистрацию
2. **Быстро реагировать** - подтверждать оплаты сразу после получения уведомления о `awaiting_payment`
3. **Анализировать flow** - понимать, где пользователи застревают

### Статистика

Подсчёт уведомлений даёт представление о:

- Количестве пользователей, начавших оплату (уведомления `→ awaiting_payment`)
- Проценте завершивших оплату (`awaiting_payment → success`)
- Скорости обработки оплат (время между двумя уведомлениями)

## Summary

✅ **Настроено:** Используется Chat ID (не username)

✅ **Отслеживается:** Только важные состояния (`awaiting_payment`, `success`)

✅ **Формат:** HTML-форматированные сообщения с emoji

✅ **Расширяемо:** Легко добавить новых админов или изменить список состояний

✅ **Минимум спама:** Только 2 уведомления на пользователя (начало оплаты + подтверждение)
