# Graceful Shutdown Guide

## Обзор

Все боты в проекте поддерживают корректное завершение работы (graceful shutdown) при получении сигналов `SIGINT` (Ctrl+C) и `SIGTERM`.

## Что происходит при graceful shutdown

1. **Перехват сигнала** - Обработчик получает SIGINT/SIGTERM
2. **Установка флага** - Выставляется `shutdown_event` для остановки фоновых задач
3. **Отмена задач** - Все активные polling/background задачи отменяются
4. **Ожидание завершения** - Бот ждёт корректного завершения задач
5. **Остановка приложения** - Telegram application останавливается и закрывается
6. **Чистый выход** - Процесс завершается без ошибок

## Реализации

### bot_flow/core/executor.py

**Ключевые компоненты:**

```python
class FlowExecutor:
    def __init__(self, flow: Flow, bot_token: str):
        # Tracking polling tasks
        self.polling_tasks: Dict[int, asyncio.Task] = {}
        self._shutdown_requested = False

    async def _cleanup(self) -> None:
        """Cleanup resources on shutdown"""
        print("\n🛑 Shutting down gracefully...")

        # Отмена всех polling задач
        if self.polling_tasks:
            print(f"⏹️  Cancelling {len(self.polling_tasks)} polling tasks...")
            for task in self.polling_tasks.values():
                if not task.done():
                    task.cancel()

            # Ждём завершения
            await asyncio.gather(*self.polling_tasks.values(), return_exceptions=True)
            print("✅ All polling tasks cancelled")

        # Остановка application
        if self.application:
            await self.application.stop()
            await self.application.shutdown()

        print("👋 Goodbye!")

    def _signal_handler(self, signum, _frame):
        """Handle termination signals"""
        self._shutdown_requested = True
        print(f"\n⚠️  Received signal {signum}, initiating shutdown...")
```

## Тестирование

### Простой тест

Запустите тестовый скрипт:

```bash
python test_graceful_shutdown.py
```

Вывод:
```
Starting background tasks...
Task 0 started
Task 1 started
Task 2 started
Press Ctrl+C to stop gracefully
Task 0 is working...
Task 1 is working...
Task 2 is working...
^C
⚠️  Received signal 2

🛑 Shutting down gracefully...
Cancelling 3 tasks...
Task 0 received shutdown signal, cleaning up...
Task 1 received shutdown signal, cleaning up...
Task 2 received shutdown signal, cleaning up...
Task 0 finished
Task 1 finished
Task 2 finished
✅ All tasks completed
👋 Goodbye!
```

### Тест payment bot

```bash
# Запустите бота
python main.py payment

# Нажмите Ctrl+C
# Вывод:
# ^C
# ⚠️  Received signal 2, initiating shutdown...
# 🛑 Shutting down gracefully...
# ⏹️  Stopping bot application...
# ✅ Bot stopped cleanly
# 👋 Goodbye!
```

## Best Practices

### 1. Всегда проверяйте shutdown_event в циклах

```python
# ✅ Правильно
while condition and not shutdown_event.is_set():
    await asyncio.sleep(1)

# ❌ Неправильно
while condition:
    await asyncio.sleep(1)
```

### 2. Обрабатывайте CancelledError

```python
try:
    while True:
        await asyncio.sleep(1)
except asyncio.CancelledError:
    print("Task cancelled, cleaning up...")
    # Cleanup code here
    raise  # Важно: re-raise exception
```

### 3. Используйте finally для гарантированной очистки

```python
try:
    application.run_polling()
except KeyboardInterrupt:
    pass
finally:
    # Cleanup всегда выполнится
    loop.run_until_complete(cleanup())
```

### 4. Не блокируйте shutdown

```python
# ✅ Правильно - быстрая проверка
if shutdown_event.is_set():
    return

# ❌ Неправильно - долгая блокирующая операция
time.sleep(60)  # Shutdown будет ждать 60 секунд
```

## Сигналы

### SIGINT (2)
- Генерируется при нажатии Ctrl+C
- Используется для интерактивного завершения

### SIGTERM (15)
- Генерируется системой или менеджером процессов
- Используется в production (systemd, docker, kubernetes)

### Пример с docker

```bash
# Отправка SIGTERM контейнеру
docker stop <container_id>

# Бот корректно завершится с cleanup
```

### Пример с systemd

```ini
[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/main.py payment-flow
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
```

## Отладка

Если shutdown не работает корректно:

1. **Проверьте регистрацию signal handlers:**
   ```python
   signal.signal(signal.SIGINT, signal_handler)
   signal.signal(signal.SIGTERM, signal_handler)
   ```

2. **Убедитесь, что задачи проверяют shutdown_event:**
   ```python
   while not shutdown_event.is_set():
       # работа
   ```

3. **Проверьте, что cleanup вызывается:**
   ```python
   finally:
       loop.run_until_complete(cleanup())
   ```

4. **Логируйте все этапы shutdown:**
   ```python
   print("Starting shutdown...")
   print("Cancelling tasks...")
   print("Stopping application...")
   print("Done!")
   ```

## Часто задаваемые вопросы

**Q: Почему используется `close_loop=False`?**

A: Чтобы самим управлять event loop и выполнить cleanup в `finally` блоке.

**Q: Что если задача не завершается?**

A: `asyncio.gather(..., return_exceptions=True)` не будет ждать вечно, а соберёт все результаты включая исключения.

**Q: Нужно ли обрабатывать SIGKILL?**

A: Нет, SIGKILL (9) нельзя перехватить. Он убивает процесс мгновенно без cleanup.

**Q: Как протестировать в production?**

A: Отправьте SIGTERM процессу:
```bash
kill -TERM <pid>
```
