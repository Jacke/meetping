# State Restoration for Awaiting Payment Users

## Обзор

При запуске бота автоматически восстанавливаются состояния всех пользователей, которые находятся в статусе **awaiting_payment** (ожидают оплаты).

Это критически важно, чтобы после перезапуска бота продолжать отслеживать оплаты пользователей.

## Как это работает

### 1. Загрузка пользователей из NocoDB

При запуске `python main.py payment`:

```
📥 Loading users in awaiting_payment state from NocoDB...
📊 Found 2 users awaiting payment:
   • User 53170594 (@stansob) - record 35
   • User 7497755872 (@stanisob) - record 36
```

Бот делает запрос к NocoDB API:
```
GET /api/v2/tables/{table_id}/records?where=(Paid,eq,false)&limit=1000
```

Фильтр: `Paid = false` - загружаются только неоплаченные заявки.

### 2. Восстановление состояний

После инициализации бота (в `post_init` hook):

```
🔄 Restoring 2 users in state 'awaiting_payment':
   ✓ User 53170594 (@stansob) - record 35
   ✓ User 7497755872 (@stanisob) - record 36
✅ Started polling for 2 users
```

Для каждого пользователя:
1. Устанавливается состояние `awaiting_payment` в `user_states`
2. Создается контекст с `record_id` для проверки оплаты
3. Запускается polling задача (проверка каждые 10 секунд)

### 3. Polling оплат

Каждые 10 секунд бот проверяет статус оплаты в NocoDB:

```
GET /api/v2/tables/{table_id}/records/{record_id}
```

Когда `Paid = true`:
```
✅ Payment confirmed for user 53170594
```

Пользователь автоматически переводится в состояние `success`.

## Технические детали

### Код восстановления

**Файл**: [bot_flow/flows/payment_flow.py:464-472](../bot_flow/flows/payment_flow.py#L464-L472)

```python
# Load users awaiting payment from NocoDB
print("\n📥 Loading users in awaiting_payment state from NocoDB...")
awaiting_users = asyncio.run(load_awaiting_payment_users())
if awaiting_users:
    print(f"📊 Found {len(awaiting_users)} users awaiting payment:")
    for user in awaiting_users:
        print(f"   • User {user['tg_id']} (@{user['username'] or user['first_name']}) - record {user['record_id']}")
else:
    print("✓ No users awaiting payment")
```

### Функция загрузки

**Файл**: [bot_flow/flows/payment_flow.py:90-132](../bot_flow/flows/payment_flow.py#L90-L132)

```python
async def load_awaiting_payment_users() -> list:
    """
    Load all users from NocoDB who are awaiting payment (Paid = false).
    Returns list of dicts with user data: [{tg_id, record_id, username, first_name}, ...]
    """
    # GET /api/v2/tables/{table_id}/records?where=(Paid,eq,false)&limit=1000
    # Returns: [{tg_id, record_id, username, first_name}, ...]
```

### Метод восстановления

**Файл**: [bot_flow/core/executor.py:368-438](../bot_flow/core/executor.py#L368-L438)

```python
async def restore_user_states(self, users_data: list, state_name: str = "awaiting_payment") -> None:
    """
    Restore user states and start polling for users from database.
    """
    # For each user:
    # 1. Set user state to 'awaiting_payment'
    # 2. Create MockContext with record_id
    # 3. Start polling task (_poll_state_restored)
```

### Polling для восстановленных пользователей

**Файл**: [bot_flow/core/executor.py:440-470](../bot_flow/core/executor.py#L440-L470)

```python
async def _poll_state_restored(self, user_id: int, state: StateNode, mock_ctx) -> None:
    """
    Poll state for restored users (simplified version without full FlowContext).

    Checks payment status every 10 seconds via NocoDB API.
    When Paid = true -> user transitions to 'success' state.
    """
```

## Преимущества

1. **Надёжность** - после перезапуска бота пользователи не теряются
2. **Автоматизация** - не нужно вручную отслеживать состояния
3. **Масштабируемость** - загружаются все пользователи (limit: 1000)
4. **Прозрачность** - все действия логируются в консоль

## Логи при запуске

### Пример успешного запуска

```
📥 Loading users in awaiting_payment state from NocoDB...
📊 Found 2 users awaiting payment:
   • User 53170594 (@stansob) - record 35
   • User 7497755872 (@stanisob) - record 36
🤖 Starting bot with flow: payment_bot
📊 States: 9
🎯 Initial state: welcome
...
🔄 Restoring 2 users in state 'awaiting_payment':
   ✓ User 53170594 (@stansob) - record 35
   ✓ User 7497755872 (@stanisob) - record 36
✅ Started polling for 2 users
```

### Если пользователей нет

```
📥 Loading users in awaiting_payment state from NocoDB...
✓ No users awaiting payment
```

### При ошибке NocoDB

```
📥 Loading users in awaiting_payment state from NocoDB...
❌ Error loading awaiting payment users: HTTP 401 Unauthorized
⚠️ NocoDB not configured, skipping user state restoration
```

## Требования

- ✅ `NOCODB_API_TOKEN` настроен в `.env`
- ✅ `NOCODB_TABLE_ID` настроен в `.env`
- ✅ Таблица имеет поля: `TG ID`, `Paid`, `Id`
- ✅ Состояние `awaiting_payment` имеет polling конфигурацию

## Troubleshooting

### Пользователи не восстанавливаются

**Проблема**: "ℹ️ No users to restore" но в NocoDB есть неоплаченные заявки

**Решение**:
1. Проверьте фильтр в NocoDB: поле должно называться именно `Paid`
2. Убедитесь что `Paid = false` (не `null`)
3. Проверьте что `TG ID` заполнен

### Polling не работает

**Проблема**: Пользователи восстановлены, но оплата не подтверждается

**Решение**:
1. Проверьте логи: должны быть сообщения о проверке каждые 10 секунд
2. Убедитесь что `record_id` корректный
3. Проверьте доступ к NocoDB API

### Ошибки при восстановлении

**Проблема**: "❌ Error loading awaiting payment users: ..."

**Решение**:
1. Проверьте `NOCODB_API_TOKEN` в `.env`
2. Проверьте `NOCODB_TABLE_ID` в `.env`
3. Убедитесь что таблица существует и доступна

## Связанные файлы

- [bot_flow/flows/payment_flow.py](../bot_flow/flows/payment_flow.py) - загрузка пользователей
- [bot_flow/core/executor.py](../bot_flow/core/executor.py) - восстановление состояний и polling
- [CLAUDE.md](../CLAUDE.md) - общая документация проекта
- [ADMIN_STATS_COMMAND.md](ADMIN_STATS_COMMAND.md) - admin команды
