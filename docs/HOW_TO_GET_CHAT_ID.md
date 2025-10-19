# Как получить Chat ID для уведомлений

## Зачем нужен Chat ID?

Telegram Bot API не позволяет отправлять сообщения пользователям по username (типа `@username`). Вместо этого нужно использовать **Chat ID** - уникальный числовой идентификатор.

## Метод 1: Через @userinfobot (Рекомендуется)

### Шаги:

1. **Откройте Telegram**

2. **Найдите бота @userinfobot**
   - В поиске введите: `@userinfobot`
   - Или перейдите по ссылке: https://t.me/userinfobot

3. **Отправьте команду `/start`**

4. **Скопируйте ваш ID**

   Бот ответит примерно так:
   ```
   👤 User Info

   ID: 123456789
   First: Stan
   Username: @stansob
   Language: en
   ```

5. **Скопируйте число из строки "ID:"**

   В примере выше это: `123456789`

## Метод 2: Через вашего бота

### Временно добавьте команду для получения Chat ID:

1. **Добавьте в payment_flow.py:**

```python
# В начало файла
async def get_chat_id(ctx: FlowContext) -> None:
    """Debug command to get user's chat ID"""
    chat_id = ctx.user.id
    await ctx.update.message.reply_text(
        f"Your Chat ID: <code>{chat_id}</code>",
        parse_mode="HTML"
    )

# В build_payment_flow():
.state("get_id")
    .on_command("/getid")
    .action(get_chat_id)
    .final()
```

2. **Запустите бота**

3. **Отправьте `/getid` в боте**

4. **Скопируйте Chat ID из ответа**

5. **Удалите временный код**

## Метод 3: Через веб-версию Telegram

1. **Откройте Web Telegram**: https://web.telegram.org

2. **Кликните на ваш аватар** (правый верхний угол)

3. **Посмотрите URL** в адресной строке:
   ```
   https://web.telegram.org/a/#123456789
   ```

4. **Число после `#`** - это ваш Chat ID: `123456789`

## Настройка уведомлений

### После получения Chat ID:

1. **Откройте файл** [bot_flow/flows/payment_flow.py](../bot_flow/flows/payment_flow.py)

2. **Найдите секцию:**
   ```python
   admin_chat_ids = [
       # 123456789,  # @stansob - Replace with actual Chat ID
       # 987654321,  # @Haleecolemax2 - Replace with actual Chat ID
   ]
   ```

3. **Раскомментируйте и замените** на ваши Chat ID:
   ```python
   admin_chat_ids = [
       123456789,    # @stansob
       987654321,    # @Haleecolemax2
   ]
   ```

4. **Сохраните файл**

5. **Перезапустите бота**

## Проверка

### Убедитесь, что уведомления работают:

1. **Запустите бота:**
   ```bash
   python main.py payment
   ```

2. **Отправьте `/start` боту** (с другого аккаунта или тестового)

3. **Проверьте, что админы получили уведомление:**
   ```
   🔔 State Change

   User: @testuser (ID: 111222333)
   State: START → welcome
   ```

## Troubleshooting

### Уведомления не приходят

**Проблема 1:** "Forbidden: bot can't initiate conversation"

**Решение:**
- Вам нужно **сначала написать боту**
- Откройте бота в Telegram
- Отправьте `/start`
- Теперь бот сможет отправлять вам сообщения

**Проблема 2:** "Chat not found"

**Решение:**
- Проверьте, что Chat ID указан **без кавычек**:
  ```python
  # ✅ Правильно
  admin_chat_ids = [123456789]

  # ❌ Неправильно
  admin_chat_ids = ["123456789"]
  ```

**Проблема 3:** "Invalid chat_id"

**Решение:**
- Убедитесь, что скопировали **правильное число**
- Chat ID должен быть **положительным целым числом**
- Без пробелов и специальных символов

## Пример конфигурации

```python
# bot_flow/flows/payment_flow.py

# Настройка для двух админов
admin_chat_ids = [
    123456789,    # @stansob
    987654321,    # @Haleecolemax2
]

# Только один админ
admin_chat_ids = [123456789]

# Без уведомлений
admin_chat_ids = []
```

## Безопасность

⚠️ **Важно:**

- **Не публикуйте Chat ID** в публичных репозиториях
- Храните `payment_flow.py` в приватном репозитории
- Или вынесите Chat ID в `.env`:

```python
# В config.py
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "").split(",")
ADMIN_CHAT_IDS = [int(x) for x in ADMIN_CHAT_IDS if x]

# В .env
ADMIN_CHAT_IDS=123456789,987654321

# В payment_flow.py
from config import config
admin_chat_ids = config.ADMIN_CHAT_IDS
```

## FAQ

**Q: Можно ли использовать username вместо Chat ID?**

A: Нет, Telegram Bot API не поддерживает отправку сообщений по username. Только по Chat ID.

**Q: Chat ID может измениться?**

A: Нет, Chat ID постоянный и не меняется.

**Q: Как добавить группу для уведомлений?**

A:
1. Добавьте бота в группу
2. Сделайте бота админом
3. Отправьте что-то в группу
4. Проверьте логи бота - там будет Chat ID группы (отрицательное число)
5. Используйте это число в `admin_chat_ids`

**Q: Почему Chat ID группы отрицательный?**

A: Telegram использует отрицательные числа для групп и каналов, положительные - для личных чатов.

## Summary

✅ **Получите Chat ID** через @userinfobot
✅ **Вставьте в payment_flow.py**
✅ **Напишите боту /start** перед тестированием
✅ **Проверьте уведомления**

Готово! Теперь вы будете получать уведомления о всех действиях пользователей! 🔔
