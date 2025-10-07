#!/usr/bin/env python3
"""
Интеграционные тесты для работы с реальным NocoDB API
Требует настройки переменных окружения в .env.test

Запуск:
  export TEST_ENV=test && pytest test_integration_nocodb.py -v -s

Переменные в .env.test:
  NOCODB_API_URL=https://app.nocodb.com
  NOCODB_API_TOKEN=your_real_token
  NOCODB_TABLE_ID=your_real_table_id
"""
import pytest
import asyncio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv
import time

# Загрузка тестового окружения
test_env_path = Path(__file__).parent / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)
else:
    print("⚠️ Файл .env.test не найден, используем основной .env")
    load_dotenv(Path(__file__).parent / ".env")

NOCODB_API_URL = os.getenv("NOCODB_API_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.getenv("NOCODB_API_TOKEN")
NOCODB_TABLE_ID = os.getenv("NOCODB_TABLE_ID")

# Пропускаем тесты если нет конфигурации
pytestmark = pytest.mark.skipif(
    not NOCODB_API_TOKEN or not NOCODB_TABLE_ID,
    reason="NocoDB не настроен. Установите NOCODB_API_TOKEN и NOCODB_TABLE_ID"
)


class TestNocoDBIntegration:
    """Интеграционные тесты с реальным NocoDB API"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Подготовка перед каждым тестом"""
        self.test_records = []  # Список созданных записей для очистки
        yield
        # Очистка после теста
        asyncio.run(self.cleanup_test_records())

    async def cleanup_test_records(self):
        """Удаление тестовых записей из NocoDB"""
        headers = {
            "xc-token": NOCODB_API_TOKEN,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            for record_id in self.test_records:
                try:
                    await client.delete(
                        f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
                        headers=headers,
                        timeout=10.0
                    )
                    print(f"✅ Удалена тестовая запись: {record_id}")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить запись {record_id}: {e}")

    @pytest.mark.asyncio
    async def test_create_payment_record(self):
        """Тест создания записи в реальной NocoDB"""
        headers = {
            "xc-token": NOCODB_API_TOKEN,
            "Content-Type": "application/json"
        }

        test_user_id = int(time.time())  # Уникальный ID
        data = {
            "TG ID": test_user_id,
            "TG": "test_integration_user",
            "Price": 1000,
            "Paid": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=data,
                timeout=10.0
            )

            assert response.status_code in [200, 201], f"Ошибка создания: {response.text}"

            result = response.json()
            record_id = str(result.get("Id") or result.get("id"))

            assert record_id is not None, "Не получен ID записи"
            self.test_records.append(record_id)

            print(f"✅ Создана запись с ID: {record_id}")
            return record_id

    @pytest.mark.asyncio
    async def test_read_payment_record(self):
        """Тест чтения записи из NocoDB"""
        # Сначала создаем запись
        record_id = await self.test_create_payment_record()

        headers = {
            "xc-token": NOCODB_API_TOKEN
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
                headers=headers,
                timeout=10.0
            )

            assert response.status_code == 200, f"Ошибка чтения: {response.text}"

            data = response.json()
            assert data.get("Paid") is False, "Поле Paid должно быть False"
            assert data.get("TG") == "test_integration_user"

            print(f"✅ Прочитана запись: {data}")

    @pytest.mark.asyncio
    async def test_update_payment_status(self):
        """Тест обновления статуса оплаты"""
        # Создаем запись
        record_id = await self.test_create_payment_record()

        headers = {
            "xc-token": NOCODB_API_TOKEN,
            "Content-Type": "application/json"
        }

        # Обновляем статус на "оплачено"
        update_data = {
            "Id": int(record_id),
            "Paid": True
        }

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=update_data,
                timeout=10.0
            )

            assert response.status_code == 200, f"Ошибка обновления: {response.text}"

            # Проверяем обновление
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
                headers=headers,
                timeout=10.0
            )

            data = response.json()
            assert data.get("Paid") is True, "Статус не обновился на True"

            print(f"✅ Статус обновлен: {data}")

    @pytest.mark.asyncio
    async def test_list_payment_records(self):
        """Тест получения списка записей"""
        # Создаем несколько записей
        record_id_1 = await self.test_create_payment_record()
        await asyncio.sleep(0.5)  # Небольшая задержка

        headers = {
            "xc-token": NOCODB_API_TOKEN,
            "Content-Type": "application/json"
        }

        test_user_id = int(time.time())
        data = {
            "TG ID": test_user_id,
            "TG": "test_user_2",
            "Price": 1000,
            "Paid": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=data,
                timeout=10.0
            )
            result = response.json()
            record_id_2 = str(result.get("Id") or result.get("id"))
            self.test_records.append(record_id_2)

            # Получаем список
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                timeout=10.0
            )

            assert response.status_code == 200, f"Ошибка получения списка: {response.text}"

            data = response.json()
            records = data.get("list") or data.get("data") or []

            assert len(records) >= 2, "Должно быть минимум 2 записи"

            print(f"✅ Получен список из {len(records)} записей")

    @pytest.mark.asyncio
    async def test_payment_workflow(self):
        """Тест полного цикла работы с платежом"""
        print("\n🔄 Тестируем полный цикл платежа:")

        # 1. Создание записи о платеже
        print("1️⃣ Создаем запись о платеже...")
        headers = {
            "xc-token": NOCODB_API_TOKEN,
            "Content-Type": "application/json"
        }

        test_user_id = int(time.time())
        data = {
            "TG ID": test_user_id,
            "TG": f"workflow_test_{test_user_id}",
            "Price": 1000,
            "Paid": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=data,
                timeout=10.0
            )

            assert response.status_code in [200, 201]
            result = response.json()
            record_id = str(result.get("Id") or result.get("id"))
            self.test_records.append(record_id)
            print(f"   ✅ Создана запись: {record_id}")

            # 2. Проверка статуса (не оплачено)
            print("2️⃣ Проверяем статус (должно быть не оплачено)...")
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
                headers=headers,
                timeout=10.0
            )
            data = response.json()
            assert data.get("Paid") is False
            print("   ✅ Статус: не оплачено")

            # 3. Симуляция ожидания (как в боте)
            print("3️⃣ Симулируем ожидание платежа...")
            await asyncio.sleep(1)

            # 4. Админ переключает статус
            print("4️⃣ Админ подтверждает платеж...")
            update_data = {"Id": int(record_id), "Paid": True}
            response = await client.patch(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=update_data,
                timeout=10.0
            )
            assert response.status_code == 200
            print("   ✅ Статус обновлен")

            # 5. Проверка обновленного статуса
            print("5️⃣ Проверяем обновленный статус...")
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
                headers=headers,
                timeout=10.0
            )
            data = response.json()
            assert data.get("Paid") is True
            print("   ✅ Платеж подтвержден!")

            print("\n✅ Полный цикл успешно завершен!")

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Тест обработки ошибок API"""
        headers = {
            "xc-token": "invalid_token",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            with pytest.raises(httpx.HTTPStatusError):
                response = await client.get(
                    f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/999999",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()

        print("✅ Ошибки API корректно обрабатываются")


class TestNocoDBConnection:
    """Тесты подключения к NocoDB"""

    @pytest.mark.asyncio
    async def test_nocodb_connection(self):
        """Проверка подключения к NocoDB"""
        if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
            pytest.skip("NocoDB не настроен")

        headers = {
            "xc-token": NOCODB_API_TOKEN
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records?limit=1",
                headers=headers,
                timeout=10.0
            )

            assert response.status_code == 200, f"Не удалось подключиться: {response.text}"
            print(f"✅ Подключение к NocoDB успешно: {NOCODB_API_URL}")

    def test_environment_variables(self):
        """Проверка переменных окружения"""
        assert NOCODB_API_URL, "NOCODB_API_URL не установлен"
        assert NOCODB_API_TOKEN, "NOCODB_API_TOKEN не установлен"
        assert NOCODB_TABLE_ID, "NOCODB_TABLE_ID не установлен"

        print(f"✅ API URL: {NOCODB_API_URL}")
        print(f"✅ Table ID: {NOCODB_TABLE_ID}")
        print(f"✅ Token: {'*' * 10}{NOCODB_API_TOKEN[-5:]}")


if __name__ == "__main__":
    print("🧪 Запуск интеграционных тестов NocoDB\n")
    print(f"API URL: {NOCODB_API_URL}")
    print(f"Table ID: {NOCODB_TABLE_ID}")
    print(f"Token: {'Установлен' if NOCODB_API_TOKEN else 'НЕ установлен'}\n")

    pytest.main([__file__, "-v", "-s", "--tb=short"])
