#!/bin/bash

docker info >/dev/null 2>&1 || {
  echo "❌ Docker is not running or not accessible"
  exit 1
}


set -e

echo "⚠️  FIRST-TIME DEPLOYMENT ⚠️"
echo "This script should be used ONLY on a new server"
echo "Project: url-shortner-project"
echo ""

read -p "❓ Are you SURE this is the FIRST TIME deploying this project on this server? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "❌ Aborted. Use the update script instead."
  exit 1
fi

echo ""
echo "📦 Pulling required images (frontend & backend)..."
docker compose pull

echo ""
echo "🏗️  Building local services (if any) and starting containers..."
docker compose up --build -d

echo ""
echo "✅ First-time deployment completed successfully!"
echo "🌐 Application should now be accessible via the server IP/domain."
