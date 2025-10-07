#!/usr/bin/env python3
"""
Тест с реальной структурой таблицы NocoDB
Использует существующие поля: TG, TG ID, Price
"""
import asyncio
import httpx
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Загрузка тестового окружения
load_dotenv(".env.test")

NOCODB_API_URL = os.getenv("NOCODB_API_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.getenv("NOCODB_API_TOKEN")
NOCODB_TABLE_ID = os.getenv("NOCODB_TABLE_ID")


async def get_table_structure():
    """Получить структуру таблицы"""
    print("📋 Получаем структуру таблицы...")

    headers = {"xc-token": NOCODB_API_TOKEN}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records?limit=1",
            headers=headers,
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            records = data.get("list", [])
            if records:
                print("✅ Структура таблицы:")
                for key, value in records[0].items():
                    print(f"   - {key}: {type(value).__name__}")
                return records[0].keys()
            else:
                print("⚠️ Таблица пустая, не можем определить структуру")
                return []
        else:
            print(f"❌ Ошибка: {response.status_code} - {response.text}")
            return []


async def create_test_payment():
    """Создать тестовую запись платежа"""
    print("\n1️⃣ Создаём тестовую запись платежа...")

    headers = {
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }

    test_user_id = int(time.time())
    test_username = f"test_user_{test_user_id}"

    # Используем реальные поля таблицы
    data = {
        "TG": test_username,
        "TG ID": test_user_id,
        "Price": 1000
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
            headers=headers,
            json=data,
            timeout=10.0
        )

        if response.status_code in [200, 201]:
            result = response.json()
            record_id = str(result.get("Id") or result.get("id"))
            print(f"✅ Запись создана: ID={record_id}")
            print(f"   TG: {test_username}")
            print(f"   TG ID: {test_user_id}")
            print(f"   Price: 1000")
            return record_id, test_user_id
        else:
            print(f"❌ Ошибка создания: {response.status_code}")
            print(f"   {response.text}")
            return None, None


async def read_payment(record_id):
    """Прочитать запись платежа"""
    print(f"\n2️⃣ Читаем запись с ID={record_id}...")

    headers = {"xc-token": NOCODB_API_TOKEN}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
            headers=headers,
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Запись прочитана:")
            print(f"   Id: {data.get('Id')}")
            print(f"   TG: {data.get('TG')}")
            print(f"   TG ID: {data.get('TG ID')}")
            print(f"   Price: {data.get('Price')}")
            print(f"   CreatedAt: {data.get('CreatedAt')}")
            return data
        else:
            print(f"❌ Ошибка чтения: {response.status_code}")
            print(f"   {response.text}")
            return None


async def update_payment_price(record_id, new_price):
    """Обновить цену платежа"""
    print(f"\n3️⃣ Обновляем цену на {new_price}...")

    headers = {
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }

    update_data = {
        "Price": new_price
    }

    async with httpx.AsyncClient() as client:
        # Пробуем PATCH
        response = await client.patch(
            f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
            headers=headers,
            json={"Id": record_id, **update_data},
            timeout=10.0
        )

        if response.status_code == 200:
            print(f"✅ Цена обновлена (PATCH)")
            return True
        else:
            print(f"⚠️ PATCH не работает: {response.status_code}")
            print(f"   Пробуем альтернативный метод...")

            # Альтернатива: PUT
            response = await client.put(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=[{"Id": record_id, **update_data}],
                timeout=10.0
            )

            if response.status_code == 200:
                print(f"✅ Цена обновлена (PUT)")
                return True
            else:
                print(f"❌ Обновление не удалось: {response.status_code}")
                print(f"   {response.text}")
                return False


async def list_all_payments():
    """Получить список всех платежей"""
    print(f"\n4️⃣ Получаем список всех записей...")

    headers = {"xc-token": NOCODB_API_TOKEN}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records?limit=10",
            headers=headers,
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            records = data.get("list", [])
            print(f"✅ Найдено записей: {len(records)}")
            for record in records[:3]:  # Показываем первые 3
                print(f"   - ID={record.get('Id')}, TG={record.get('TG')}, Price={record.get('Price')}")
            if len(records) > 3:
                print(f"   ... и ещё {len(records) - 3} записей")
            return records
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return []


async def delete_payment(record_id):
    """Удалить запись платежа"""
    print(f"\n5️⃣ Удаляем тестовую запись ID={record_id}...")

    headers = {"xc-token": NOCODB_API_TOKEN}

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
            headers=headers,
            timeout=10.0
        )

        if response.status_code in [200, 204]:
            print(f"✅ Запись удалена")
            return True
        else:
            print(f"❌ Ошибка удаления: {response.status_code}")
            print(f"   {response.text}")
            return False


async def main():
    print("="*60)
    print("🧪 Тест реальной структуры таблицы NocoDB")
    print("="*60)

    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        print("❌ Не настроены переменные окружения!")
        return

    print(f"\n📍 API URL: {NOCODB_API_URL}")
    print(f"📍 Table ID: {NOCODB_TABLE_ID}")
    print(f"📍 Token: {'*' * 10}{NOCODB_API_TOKEN[-5:]}")

    # Шаг 0: Получить структуру таблицы
    await get_table_structure()

    # Шаг 1: Создать запись
    record_id, test_user_id = await create_test_payment()
    if not record_id:
        return

    # Шаг 2: Прочитать запись
    await read_payment(record_id)

    # Шаг 3: Обновить запись
    await update_payment_price(record_id, 2000)

    # Проверить обновление
    await read_payment(record_id)

    # Шаг 4: Получить список
    await list_all_payments()

    # Шаг 5: Удалить тестовую запись
    await delete_payment(record_id)

    print("\n" + "="*60)
    print("✅ Тест завершён успешно!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
