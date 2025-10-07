# План очистки репозитория MeetPing-Pay

## 🗑️ Файлы для удаления

### Устаревшие Go-файлы и артефакты (старый проект MeetPing)

```bash
# Бинарник Go (7.4 MB)
rm meetping

# База данных старого Go проекта (102 KB)
rm meetping.db

# Конфигурация Air (Go hot reload)
rm .air.toml

# Makefile для Go проекта
rm Makefile

# Docker файлы (если не используются)
rm docker-compose.yml
rm docker-compose.override.yml
rm Dockerfile

# SQL миграции для старого проекта
rm init.sql
rm -rf migrations/

# Директории старого Go проекта
rm -rf config/
rm -rf data/  # Если там нет важных данных
```

### Документация старого проекта

```bash
# Устаревшая документация Go-версии
rm BOT_OLD.md           # 12 KB - архив логики Go-кода
rm meetping_full_chat.md # 512 KB - старая переписка
rm README_DEV.md        # 32 bytes - практически пустой
rm CHANGELOG.md         # 383 bytes - устарел
rm DEPLOY.md            # 756 bytes - для старого проекта

# Старый README (заменить на новый)
# rm README.md  # Обновим вместо удаления
```

### Тестовые файлы (опционально, если не нужны)

```bash
# Старые тесты для NocoDB структуры
rm test_nocodb_real_structure.py  # 8.6 KB

# Или оставить test_payment_bot.py и test_integration_nocodb.py
```

### Временные файлы

```bash
# Скрипт сравнения (если не нужен)
rm compare_files.sh

# Кеш
rm -rf __pycache__/
rm -rf .pytest_cache/

# IDE файлы
rm -rf .cursor/
rm -rf .vscode/  # Если не используете VS Code
rm .DS_Store
```

## ✅ Файлы для сохранения

### Основные Python боты

```
✓ payment_bot.py              # Оригинальный императивный бот
✓ agent.py                    # Anthropic Agents SDK example
✓ mcp-test.py                 # LangChain + OpenAI integration
```

### Bot Flow фреймворк

```
✓ bot_flow/                   # Весь фреймворк
  ├── core/                   # Ядро
  ├── flows/                  # Примеры flow
  ├── examples/               # Демо боты
  └── README.md               # Документация
```

### Документация

```
✓ CLAUDE.md                   # Инструкции для Claude (обновлён)
✓ docs/
  ├── FLOW_BUILDER_GUIDE.md   # Руководство по FlowBuilder
  ├── DECLARATIVE_BOT_APPROACHES.md  # Сравнение подходов
  └── payment_flow.md         # Визуализация
```

### Скрипты и утилиты

```
✓ visualize_payment_flow.py   # Генерация диаграмм
✓ run_bot.sh                  # NEW! Скрипт запуска
```

### Тесты

```
✓ test_payment_bot.py         # Unit тесты
✓ test_integration_nocodb.py  # Integration тесты
```

### Конфигурация

```
✓ .env                        # Основная конфигурация
✓ .env.example                # Пример
✓ .env.test                   # Для integration тестов
✓ requirements.txt            # Python зависимости
✓ .gitignore                  # Git ignore
```

## 🔄 Файлы для обновления

### README.md - создать новый

Заменить старый README.md на новый с описанием:
- MeetPing-Pay проекта (Python)
- Bot Flow фреймворка
- Инструкции по запуску
- Примеры использования

## 📋 Команды для очистки

### Вариант 1: Удалить все устаревшее (агрессивная очистка)

```bash
# Создать бэкап перед удалением
tar -czf meetping-old-backup.tar.gz \
    meetping meetping.db BOT_OLD.md meetping_full_chat.md \
    config/ migrations/ data/ Makefile docker-compose.yml \
    Dockerfile init.sql .air.toml

# Удалить Go артефакты
rm meetping meetping.db .air.toml Makefile
rm docker-compose.yml docker-compose.override.yml Dockerfile init.sql
rm -rf migrations/ config/

# Удалить старую документацию
rm BOT_OLD.md meetping_full_chat.md README_DEV.md CHANGELOG.md DEPLOY.md

# Удалить временные файлы
rm compare_files.sh
rm -rf __pycache__/ .pytest_cache/

# Опционально: удалить IDE конфиги
rm -rf .cursor/ .vscode/ .DS_Store

# Удалить старый тест структуры
rm test_nocodb_real_structure.py

# Очистить logs (опционально)
rm -rf logs/*
```

### Вариант 2: Безопасная очистка (переместить в архив)

```bash
# Создать директорию архива
mkdir -p archive/

# Переместить старые файлы
mv meetping meetping.db archive/
mv BOT_OLD.md meetping_full_chat.md archive/
mv config/ migrations/ data/ archive/
mv Makefile docker-compose.yml Dockerfile init.sql archive/
mv .air.toml compare_files.sh archive/

# Очистить временные
rm -rf __pycache__/ .pytest_cache/
```

## 📊 Экономия места

```
Общая экономия: ~8.5 MB

Детализация:
- meetping (binary):        7.4 MB
- meetping_full_chat.md:    512 KB
- meetping.db:              102 KB
- BOT_OLD.md:                12 KB
- Прочие конфиги/скрипты:   ~500 KB
```

## ✨ Структура после очистки

```
meetping-pay/
├── bot_flow/                   # Declarative bot framework
│   ├── core/
│   ├── flows/
│   ├── examples/
│   └── README.md
├── docs/                       # Documentation
│   ├── FLOW_BUILDER_GUIDE.md
│   ├── DECLARATIVE_BOT_APPROACHES.md
│   └── payment_flow.md
├── logs/                       # Bot logs
├── payment_bot.py              # Original imperative bot
├── agent.py                    # Anthropic agent example
├── mcp-test.py                 # MCP test
├── visualize_payment_flow.py   # Flow visualization script
├── run_bot.sh                  # Bot runner script (NEW!)
├── test_payment_bot.py         # Tests
├── test_integration_nocodb.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── CLAUDE.md                   # Project guide for Claude
└── README.md                   # Project README (updated)
```

## 🚀 После очистки

1. **Обновить README.md** с актуальной информацией
2. **Протестировать** что боты запускаются:
   ```bash
   ./run_bot.sh original
   ./run_bot.sh flow
   ./run_bot.sh visualize
   ```
3. **Закоммитить** изменения:
   ```bash
   git add -A
   git commit -m "chore: clean up repository, remove old Go artifacts"
   ```

## ⚠️ Внимание

Перед удалением убедитесь что:
- [ ] Создан бэкап важных файлов
- [ ] Проверено что не используются Docker конфиги
- [ ] Проверено что в `data/` и `logs/` нет нужных данных
- [ ] Протестированы основные скрипты после удаления
