#!/bin/bash

# Deployment script for meetping-pay bot
# Usage: ./deploy.sh

SERVER="root@84.22.150.92"
REMOTE_DIR="/root/meetping-pay"
LOCAL_DIR="."

echo "=========================================="
echo "Deploying meetping-pay bot to server"
echo "=========================================="

# Step 1: Create remote directory
echo ""
echo "[1/4] Creating remote directory..."
ssh $SERVER "mkdir -p $REMOTE_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create directory on server"
    exit 1
fi

echo "✅ Directory created successfully"

# Step 2: Upload project files via rsync (excludes unnecessary files)
echo ""
echo "[2/4] Uploading project files..."
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
    $LOCAL_DIR/ $SERVER:$REMOTE_DIR/

if [ $? -ne 0 ]; then
    echo "❌ Failed to upload files"
    exit 1
fi

echo "✅ Files uploaded successfully"

# Step 3: Install Python dependencies
echo ""
echo "[3/4] Installing Python dependencies on server..."
ssh $SERVER "cd $REMOTE_DIR && python3 -m pip install -r requirements.txt"

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Step 4: Check Python version and installed packages
echo ""
echo "[4/4] Verifying installation..."
ssh $SERVER "cd $REMOTE_DIR && python3 --version && python3 -m pip list | grep -E 'python-telegram-bot|requests|python-dotenv'"

echo ""
echo "=========================================="
echo "✅ Deployment completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy your .env file to server:"
echo "   scp .env $SERVER:$REMOTE_DIR/"
echo ""
echo "2. SSH to server and run the bot:"
echo "   ssh $SERVER"
echo "   cd $REMOTE_DIR"
echo "   python3 main.py"
echo ""
echo "3. To run bot in background (persistent):"
echo "   nohup python3 main.py > bot.log 2>&1 &"
echo ""
