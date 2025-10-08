# Getting Started - MeetPing-Pay

Быстрый старт для работы с проектом.

## 📋 Требования

- Python 3.8+
- pip

## 🚀 Установка

### 1. Установить зависимости

```bash
# Вариант 1: Через скрипт (рекомендуется)
./run_bot.sh install

# Вариант 2: Напрямую через pip
pip install -r requirements.txt
```

**Устанавливаются:**
- `python-telegram-bot` >= 20.0 - для работы с Telegram Bot API
- `python-dotenv` >= 1.0.0 - для загрузки .env переменных
- `httpx` >= 0.25.0 - для HTTP запросов к NocoDB
- `pytest` >= 7.0.0 - для тестирования
- `pytest-asyncio` >= 0.21.0 - для async тестов

### 2. Настроить .env

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать .env и добавить:
nano .env  # или любой другой редактор
```

**Обязательные переменные:**
```bash
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=your_telegram_bot_token_here
```

**Опциональные переменные для NocoDB:**
```bash
# NocoDB Configuration
NOCODB_API_URL=https://app.nocodb.com
NOCODB_API_TOKEN=your_nocodb_api_token
NOCODB_TABLE_ID=your_table_id
```

> **Важно:** Настройки платежей и тексты бота хранятся в NocoDB таблицах:
> - **Bot Config** (`mguawvnumqrb5k7`) - PAYMENT_PHONE, PAYMENT_AMOUNT, TELEGRAM_GROUP_LINK
> - **Bot Texts** (`pwt37o18yvtfeh6`) - все текстовые сообщения бота
>
> Загрузите начальные данные:
> ```bash
> python upload_config_to_nocodb.py
> python upload_texts_to_nocodb.py
> ```

---

## 🎯 Быстрый тест

### 1. Проверить что всё работает

```bash
# Сгенерировать визуализации (не требует BOT_TOKEN)
./run_bot.sh visualize
```

Должно создать:
- ✅ `docs/payment_flow.md` - Mermaid диаграмма
- ✅ `docs/payment_flow.dot` - GraphViz файл
- ✅ `docs/payment_flow.txt` - ASCII диаграмма

### 2. Запустить тесты (опционально)

```bash
# Unit тесты (мокированные, быстрые)
./run_bot.sh test

# Или напрямую через pytest
pytest test_payment_bot.py -v
```

---

## 🤖 Запуск ботов

### Вариант 1: Оригинальный payment_bot.py

```bash
./run_bot.sh original
```

### Вариант 2: Декларативный bot_flow версия

```bash
./run_bot.sh flow
```

### Вариант 3: Примеры bot_flow

```bash
# Welcome bot
./run_bot.sh demo welcome

# Menu bot
./run_bot.sh demo menu

# Timer bot (с polling)
./run_bot.sh demo timer

# Survey bot
./run_bot.sh demo survey

# Age gate bot (условия)
./run_bot.sh demo age_gate
```

---

## 📊 Визуализация Flow

```bash
# Генерация всех диаграмм
./run_bot.sh visualize
```

Результаты:
- `docs/payment_flow.md` - для GitHub/документации
- `docs/payment_flow.dot` - для генерации PNG (требует GraphViz)
- `docs/payment_flow.txt` - текстовая версия

**Чтобы создать PNG из DOT:**
```bash
# Установить GraphViz
brew install graphviz  # macOS
# или
sudo apt-get install graphviz  # Linux

# Сгенерировать PNG
dot -Tpng docs/payment_flow.dot -o docs/payment_flow.png
```

---

## 🧪 Тестирование

### Unit тесты (быстрые, мокированные)

```bash
./run_bot.sh test

# Или с покрытием
pytest test_payment_bot.py --cov=payment_bot --cov-report=html
```

### Integration тесты (требуют NocoDB)

1. Создать `.env.test`:
```bash
cp .env.example .env.test
```

2. Добавить NocoDB credentials в `.env.test`:
```bash
NOCODB_API_TOKEN=your_token
NOCODB_TABLE_ID=your_table_id
```

3. Запустить:
```bash
pytest test_integration_nocodb.py -v -s
```

---

## 🔧 Разработка нового бота с Bot Flow

### Минимальный пример

```python
from bot_flow.core import FlowBuilder, FlowExecutor
import os

# Описать flow
flow = (
    FlowBuilder("my_bot")

    .state("start")
        .on_command("/start")
        .reply("Привет, {user.first_name}!")
        .button("Далее", goto="next")

    .state("next")
        .reply("Готово!")
        .final()

    .build()
)

# Визуализировать
from bot_flow.core import visualize
visualize(flow).export_mermaid("my_bot_flow.md")

# Запустить
executor = FlowExecutor(flow, os.getenv("BOT_TOKEN"))
executor.run()
```

### Больше примеров

См. [bot_flow/examples/demo.py](bot_flow/examples/demo.py) - 5 готовых примеров.

---

## 📚 Документация

- **README.md** - главная страница проекта
- **bot_flow/README.md** - API reference для Bot Flow
- **docs/FLOW_BUILDER_GUIDE.md** - полное руководство
- **docs/DECLARATIVE_BOT_APPROACHES.md** - сравнение подходов
- **docs/PROJECT_SUMMARY.md** - итоговая сводка

---

## ❓ Troubleshooting

### ModuleNotFoundError: No module named 'telegram'

**Решение:**
```bash
./run_bot.sh install
# или
pip install python-telegram-bot
```

### ModuleNotFoundError: No module named 'bot_flow'

**Решение:** Используйте `./run_bot.sh` вместо прямого вызова Python:
```bash
# ❌ Не работает
python3 bot_flow/flows/payment_flow.py

# ✅ Работает
./run_bot.sh flow
```

Или используйте `PYTHONPATH`:
```bash
PYTHONPATH=. python3 bot_flow/flows/payment_flow.py
```

### .env file not found

**Решение:**
```bash
cp .env.example .env
# Отредактировать .env и добавить BOT_TOKEN
```

### NocoDB not configured

Это warning, не ошибка. Бот работает в локальном режиме без NocoDB. Для полной функциональности добавьте в `.env`:
```bash
NOCODB_API_TOKEN=your_token
NOCODB_TABLE_ID=your_table_id
```

---

## 🎉 Готово!

Теперь вы можете:
- ✅ Запускать payment bot (оригинальный и декларативный)
- ✅ Создавать свои боты с Bot Flow
- ✅ Визуализировать user flow автоматически
- ✅ Тестировать код

**Следующие шаги:**
1. Изучите [docs/FLOW_BUILDER_GUIDE.md](docs/FLOW_BUILDER_GUIDE.md)
2. Посмотрите примеры в [bot_flow/examples/demo.py](bot_flow/examples/demo.py)
3. Создайте свой первый бот!

---

**Вопросы?** См. [README.md](README.md) или создайте issue.
