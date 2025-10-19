#!/usr/bin/env python3
"""
Тестовый скрипт для проверки graceful shutdown
"""
import asyncio
import signal
import sys


# Симуляция работающих задач
tasks = []
shutdown_event = asyncio.Event()


async def background_task(task_id: int):
    """Фоновая задача, которая проверяет shutdown_event"""
    try:
        print(f"Task {task_id} started")
        while not shutdown_event.is_set():
            print(f"Task {task_id} is working...")
            await asyncio.sleep(2)
        print(f"Task {task_id} received shutdown signal, cleaning up...")
    except asyncio.CancelledError:
        print(f"Task {task_id} was cancelled")
        raise
    finally:
        print(f"Task {task_id} finished")


def signal_handler(signum, _frame):
    """Обработчик сигналов завершения"""
    print(f"\n⚠️  Received signal {signum}")
    shutdown_event.set()


async def main():
    """Главная функция"""
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Запускаем фоновые задачи
    print("Starting background tasks...")
    for i in range(3):
        task = asyncio.create_task(background_task(i))
        tasks.append(task)

    print("Press Ctrl+C to stop gracefully")

    # Ждём сигнала завершения
    await shutdown_event.wait()

    # Graceful shutdown
    print("\n🛑 Shutting down gracefully...")
    print(f"Cancelling {len(tasks)} tasks...")

    # Отменяем все задачи
    for task in tasks:
        if not task.done():
            task.cancel()

    # Ждём завершения всех задач
    await asyncio.gather(*tasks, return_exceptions=True)

    print("✅ All tasks completed")
    print("👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)
