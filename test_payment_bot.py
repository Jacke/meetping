#!/usr/bin/env python3
"""
Тесты для payment_bot.py
Запуск: pytest test_payment_bot.py -v
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Добавляем путь к модулю
sys.path.insert(0, str(Path(__file__).parent))

# Mock окружения перед импортом
with patch.dict('os.environ', {
    'BOT_TOKEN': 'test_token',
    'NOCODB_API_TOKEN': 'test_nocodb_token',
    'NOCODB_TABLE_ID': 'test_table_id',
    'PAYMENT_PHONE': '+7 (999) 111-22-33',
    'PAYMENT_AMOUNT': '500 рублей',
    'TELEGRAM_GROUP_LINK': 'https://t.me/test_group'
}):
    import payment_bot


class TestPaymentBot:
    """Тесты для payment_bot"""

    @pytest.mark.asyncio
    async def test_create_payment_record_success(self):
        """Тест успешного создания записи в NocoDB"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "123", "Id": "123"}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await payment_bot.create_payment_record(12345, "testuser", "Test")

            assert result == "123"

    @pytest.mark.asyncio
    async def test_create_payment_record_no_config(self):
        """Тест создания записи без конфигурации NocoDB"""
        with patch.dict('os.environ', {'NOCODB_API_TOKEN': '', 'NOCODB_TABLE_ID': ''}):
            # Переинициализируем переменные
            original_token = payment_bot.NOCODB_API_TOKEN
            original_table = payment_bot.NOCODB_TABLE_ID

            payment_bot.NOCODB_API_TOKEN = None
            payment_bot.NOCODB_TABLE_ID = None

            result = await payment_bot.create_payment_record(12345, "testuser", "Test")

            # Восстанавливаем
            payment_bot.NOCODB_API_TOKEN = original_token
            payment_bot.NOCODB_TABLE_ID = original_table

            assert result is None

    @pytest.mark.asyncio
    async def test_create_payment_record_api_error(self):
        """Тест обработки ошибки API при создании записи"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("API Error")
            )

            result = await payment_bot.create_payment_record(12345, "testuser", "Test")

            assert result is None

    @pytest.mark.asyncio
    async def test_check_payment_in_nocodb_paid(self):
        """Тест проверки оплаченного платежа"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"paid": True}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await payment_bot.check_payment_in_nocodb("123")

            assert result is True

    @pytest.mark.asyncio
    async def test_check_payment_in_nocodb_not_paid(self):
        """Тест проверки неоплаченного платежа"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"paid": False}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await payment_bot.check_payment_in_nocodb("123")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_payment_in_nocodb_no_record(self):
        """Тест проверки несуществующей записи"""
        result = await payment_bot.check_payment_in_nocodb("")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_payment_in_nocodb_api_error(self):
        """Тест обработки ошибки API при проверке статуса"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("API Error")
            )

            result = await payment_bot.check_payment_in_nocodb("123")

            assert result is False

    @pytest.mark.asyncio
    async def test_start_command(self):
        """Тест команды /start"""
        update = MagicMock()
        context = MagicMock()

        update.effective_user.first_name = "TestUser"
        update.message.reply_text = AsyncMock()

        await payment_bot.start(update, context)

        # Проверяем, что сообщение было отправлено
        assert update.message.reply_text.called
        call_args = update.message.reply_text.call_args
        assert "Добро пожаловать" in call_args[0][0]
        assert "TestUser" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_payment_button_with_nocodb(self):
        """Тест нажатия кнопки оплаты с NocoDB"""
        query = MagicMock()
        update = MagicMock()
        context = MagicMock()

        update.callback_query = query
        query.from_user.id = 12345
        query.from_user.username = "testuser"
        query.from_user.first_name = "Test"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.message.chat_id = 67890

        with patch('payment_bot.create_payment_record', return_value="rec123"):
            with patch('asyncio.create_task'):
                await payment_bot.payment_button(update, context)

        # Проверяем, что пользователь добавлен в pending_payments
        assert 12345 in payment_bot.pending_payments
        assert payment_bot.pending_payments[12345] == "rec123"

        # Очищаем
        del payment_bot.pending_payments[12345]

    @pytest.mark.asyncio
    async def test_payment_button_without_nocodb(self):
        """Тест нажатия кнопки оплаты без NocoDB"""
        query = MagicMock()
        update = MagicMock()
        context = MagicMock()

        update.callback_query = query
        query.from_user.id = 54321
        query.from_user.username = "testuser2"
        query.from_user.first_name = "Test2"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.message.chat_id = 67890

        with patch('payment_bot.create_payment_record', return_value=None):
            with patch('asyncio.create_task'):
                await payment_bot.payment_button(update, context)

        # Проверяем, что пользователь добавлен в pending_payments с пустой строкой
        assert 54321 in payment_bot.pending_payments
        assert payment_bot.pending_payments[54321] == ""

        # Очищаем
        del payment_bot.pending_payments[54321]

    @pytest.mark.asyncio
    async def test_confirm_payment_command(self):
        """Тест команды /confirm"""
        update = MagicMock()
        context = MagicMock()

        update.message.reply_text = AsyncMock()
        context.args = ["12345"]

        # Добавляем пользователя в pending
        payment_bot.pending_payments[12345] = "rec123"

        await payment_bot.confirm_payment(update, context)

        # Проверяем, что сообщение было отправлено
        assert update.message.reply_text.called
        call_args = update.message.reply_text.call_args[0][0]
        assert "12345" in call_args
        assert "rec123" in call_args

        # Очищаем
        del payment_bot.pending_payments[12345]

    @pytest.mark.asyncio
    async def test_confirm_payment_no_args(self):
        """Тест команды /confirm без аргументов"""
        update = MagicMock()
        context = MagicMock()

        update.message.reply_text = AsyncMock()
        context.args = []

        await payment_bot.confirm_payment(update, context)

        # Проверяем сообщение об ошибке
        call_args = update.message.reply_text.call_args[0][0]
        assert "Использование" in call_args

    @pytest.mark.asyncio
    async def test_confirm_payment_invalid_user(self):
        """Тест команды /confirm для несуществующего пользователя"""
        update = MagicMock()
        context = MagicMock()

        update.message.reply_text = AsyncMock()
        context.args = ["99999"]

        await payment_bot.confirm_payment(update, context)

        # Проверяем сообщение об ошибке
        call_args = update.message.reply_text.call_args[0][0]
        assert "не ожидает оплаты" in call_args

    @pytest.mark.asyncio
    async def test_list_pending_empty(self):
        """Тест команды /pending с пустым списком"""
        update = MagicMock()
        context = MagicMock()

        update.message.reply_text = AsyncMock()

        # Очищаем pending_payments
        payment_bot.pending_payments.clear()

        await payment_bot.list_pending(update, context)

        # Проверяем сообщение
        call_args = update.message.reply_text.call_args[0][0]
        assert "Нет пользователей" in call_args

    @pytest.mark.asyncio
    async def test_list_pending_with_users(self):
        """Тест команды /pending со списком пользователей"""
        update = MagicMock()
        context = MagicMock()

        update.message.reply_text = AsyncMock()

        # Добавляем пользователей
        payment_bot.pending_payments[12345] = "rec123"
        payment_bot.pending_payments[67890] = "rec456"

        await payment_bot.list_pending(update, context)

        # Проверяем сообщение
        call_args = update.message.reply_text.call_args[0][0]
        assert "12345" in call_args
        assert "67890" in call_args
        assert "rec123" in call_args
        assert "rec456" in call_args

        # Очищаем
        payment_bot.pending_payments.clear()

    @pytest.mark.asyncio
    async def test_check_payment_status_paid(self):
        """Тест проверки статуса с подтверждением оплаты"""
        context = MagicMock()
        context.bot.send_message = AsyncMock()

        user_id = 12345
        chat_id = 67890

        # Добавляем пользователя
        payment_bot.pending_payments[user_id] = "rec123"

        # Мокаем проверку - сразу возвращаем True
        with patch('payment_bot.check_payment_in_nocodb', return_value=True):
            # Запускаем проверку
            await payment_bot.check_payment_status(context, user_id, chat_id)

        # Проверяем, что сообщение отправлено
        assert context.bot.send_message.called
        call_args = context.bot.send_message.call_args
        assert "Оплата подтверждена" in call_args[1]['text']

        # Проверяем, что пользователь удален из pending
        assert user_id not in payment_bot.pending_payments


class TestEnvironmentVariables:
    """Тесты для переменных окружения"""

    def test_bot_token_loaded(self):
        """Проверка загрузки BOT_TOKEN"""
        assert payment_bot.BOT_TOKEN is not None

    def test_nocodb_variables(self):
        """Проверка переменных NocoDB"""
        assert payment_bot.NOCODB_API_URL is not None
        assert payment_bot.NOCODB_API_TOKEN is not None
        assert payment_bot.NOCODB_TABLE_ID is not None

    def test_payment_settings(self):
        """Проверка настроек оплаты"""
        assert payment_bot.PAYMENT_PHONE is not None
        assert payment_bot.PAYMENT_AMOUNT is not None
        assert payment_bot.TELEGRAM_GROUP_LINK is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
