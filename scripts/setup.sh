#!/bin/bash
set -e

echo "🚀 Setting up DocuBot MVP..."

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

# Copy environment files
echo "📝 Setting up environment files..."
[ ! -f .env ] && cp .env.example .env
[ ! -f backend/.env ] && cp backend/.env.example backend/.env
[ ! -f frontend/.env.local ] && cp frontend/.env.example frontend/.env.local

# Build containers
echo "🐳 Building Docker containers..."
docker-compose build

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env files with your API keys"
echo "  2. Run: make dev"
echo "  3. Visit: http://localhost:3000"
