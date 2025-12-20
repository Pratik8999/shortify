#!/bin/bash

docker info >/dev/null 2>&1 || {
  echo "❌ Docker is not running or not accessible"
  exit 1
}

set -e

echo "🔄 UPDATE DEPLOYMENT"
echo "This will pull the latest images and restart services"
echo "Project: url-shortner-project"
echo ""

read -p "❓ Are you sure you want to UPDATE containers to the latest images? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "❌ Update cancelled."
  exit 1
fi

echo ""
echo "📦 Pulling latest images..."
docker compose pull

echo ""
echo "🚀 Restarting services with updated images..."
docker compose up -d

echo ""
echo "🧹 Cleaning unused images..."
docker image prune -f

echo ""
echo "✅ Update deployment completed successfully!"
