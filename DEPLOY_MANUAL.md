# Manual Deployment Guide

Пошаговая инструкция для развертывания бота на сервере.

## Сервер
- **IP:** 84.22.150.92
- **User:** root
- **Password:** nf6CAFYHkZqp

## Шаг 1: Подключиться к серверу

```bash
ssh root@84.22.150.92
# Введите пароль: nf6CAFYHkZqp
```

## Шаг 2: Создать директорию проекта

```bash
mkdir -p /root/meetping-pay
cd /root/meetping-pay
```

## Шаг 3: Загрузить файлы проекта

### Вариант А: С локального компьютера (в новом терминале, НЕ на сервере)

```bash
# На вашем локальном компьютере
cd /Users/stan/Dev/_PROJ/meetping-pay

# Загрузить файлы через rsync
rsync -avz --progress \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs/*' \
    --exclude='*.tar.gz' \
    --exclude='.cursor' \
    --exclude='.vscode' \
    --exclude='*.old' \
    ./ root@84.22.150.92:/root/meetping-pay/

# Или используйте scp для отдельных файлов
scp -r bot_flow config.py main.py requirements.txt root@84.22.150.92:/root/meetping-pay/
```

### Вариант Б: Клонировать с GitHub (если есть репозиторий)

```bash
# На сервере
cd /root/meetping-pay
git clone <ваш-git-репозиторий> .
```

### Вариант В: Создать архив и загрузить

```bash
# На локальном компьютере
cd /Users/stan/Dev/_PROJ/meetping-pay
tar -czf meetping-pay.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='logs/*' \
    --exclude='*.tar.gz' \
    bot_flow/ config.py main.py requirements.txt CLAUDE.md README.md

# Загрузить архив
scp meetping-pay.tar.gz root@84.22.150.92:/root/

# На сервере
cd /root/meetping-pay
tar -xzf ../meetping-pay.tar.gz
```

## Шаг 4: Установить зависимости Python на сервере

```bash
# На сервере
cd /root/meetping-pay

# Проверить версию Python
python3 --version

# Установить pip если нет
# apt update && apt install -y python3-pip

# Установить зависимости
python3 -m pip install -r requirements.txt

# Проверить установку
python3 -m pip list | grep -E 'telegram|requests|dotenv'
```

## Шаг 5: Настроить переменные окружения

```bash
# На сервере
cd /root/meetping-pay

# Создать .env файл
nano .env
```

Вставить содержимое (скопируйте из локального `.env`):

```env
BOT_TOKEN=your_bot_token_here
NOCODB_API_TOKEN=your_nocodb_token_here
NOCODB_TABLE_ID=mfaob33z2nnrxve
NOCODB_API_URL=https://app.nocodb.com
ENV=production
```

Сохранить: `Ctrl+O`, `Enter`, `Ctrl+X`

### Или загрузить .env с локального компьютера

```bash
# На локальном компьютере
scp .env root@84.22.150.92:/root/meetping-pay/
```

## Шаг 6: Тестовый запуск

```bash
# На сервере
cd /root/meetping-pay

# Проверить конфигурацию
python3 main.py status

# Запустить бота в тестовом режиме
python3 main.py
```

Нажмите `Ctrl+C` для остановки.

## Шаг 7: Запуск в фоновом режиме

### Вариант А: Использовать nohup

```bash
# Запустить бота в фоне
nohup python3 main.py > bot.log 2>&1 &

# Проверить процесс
ps aux | grep main.py

# Проверить логи
tail -f bot.log

# Остановить бота
pkill -f "python3 main.py"
```

### Вариант Б: Использовать systemd (рекомендуется)

```bash
# Создать systemd service
nano /etc/systemd/system/meetping-pay.service
```

Вставить:

```ini
[Unit]
Description=MeetPing Payment Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/meetping-pay
ExecStart=/usr/bin/python3 /root/meetping-pay/main.py
Restart=always
RestartSec=10
StandardOutput=append:/root/meetping-pay/logs/bot.log
StandardError=append:/root/meetping-pay/logs/bot.log

[Install]
WantedBy=multi-user.target
```

Сохранить и активировать:

```bash
# Создать директорию для логов
mkdir -p /root/meetping-pay/logs

# Перезагрузить systemd
systemctl daemon-reload

# Включить автозапуск
systemctl enable meetping-pay

# Запустить бота
systemctl start meetping-pay

# Проверить статус
systemctl status meetping-pay

# Проверить логи
journalctl -u meetping-pay -f

# Остановить бота
systemctl stop meetping-pay

# Перезапустить бота
systemctl restart meetping-pay
```

## Команды для управления

```bash
# Проверить работает ли бот
ps aux | grep main.py

# Проверить логи (nohup)
tail -f bot.log

# Проверить логи (systemd)
journalctl -u meetping-pay -f

# Остановить бота (nohup)
pkill -f "python3 main.py"

# Остановить бота (systemd)
systemctl stop meetping-pay

# Перезапустить бота (systemd)
systemctl restart meetping-pay
```

## Обновление бота

```bash
# 1. Остановить бота
systemctl stop meetping-pay  # или pkill -f "python3 main.py"

# 2. Загрузить новые файлы (с локального компьютера)
cd /Users/stan/Dev/_PROJ/meetping-pay
rsync -avz --progress --exclude='.git' --exclude='.venv' \
    ./ root@84.22.150.92:/root/meetping-pay/

# 3. Установить новые зависимости (если есть)
ssh root@84.22.150.92 "cd /root/meetping-pay && python3 -m pip install -r requirements.txt"

# 4. Запустить бота
ssh root@84.22.150.92 "systemctl start meetping-pay"
```

## Troubleshooting

### Проблема: Bot token not found
```bash
# Проверить .env файл
cat /root/meetping-pay/.env

# Убедиться что BOT_TOKEN установлен
grep BOT_TOKEN /root/meetping-pay/.env
```

### Проблема: Module not found
```bash
# Переустановить зависимости
cd /root/meetping-pay
python3 -m pip install --upgrade -r requirements.txt
```

### Проблема: Permission denied
```bash
# Дать права на выполнение
chmod +x /root/meetping-pay/main.py
```

### Проверить подключение к NocoDB
```bash
python3 test_nocodb_direct.py
```
