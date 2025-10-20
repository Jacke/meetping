#!/bin/bash

# Quick upload script
# Usage: ./upload.sh

SERVER="root@84.22.150.92"
ARCHIVE="meetping-pay-deploy.tar.gz"

echo "Uploading $ARCHIVE to server..."
scp $ARCHIVE $SERVER:/root/

echo ""
echo "✅ Upload complete!"
echo ""
echo "Now SSH to server and extract:"
echo "  ssh $SERVER"
echo "  cd /root"
echo "  mkdir -p meetping-pay"
echo "  tar -xzf meetping-pay-deploy.tar.gz -C meetping-pay"
echo "  cd meetping-pay"
echo "  python3 -m pip install -r requirements.txt"
echo ""
