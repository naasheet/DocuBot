PHONY: help setup dev stop clean migrate seed test logs

help:
	@echo "DocuBot MVP - Available Commands:"
	@echo "  make setup    - Initial project setup"
	@echo "  make dev      - Start development environment"
	@echo "  make stop     - Stop all containers"
	@echo "  make clean    - Stop and remove containers + volumes"
	@echo "  make migrate  - Run database migrations"
	@echo "  make seed     - Seed database with test data"
	@echo "  make test     - Run all tests"
	@echo "  make logs     - Follow logs"

setup:
	@echo "🚀 Setting up DocuBot MVP..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; fi
	@if [ ! -f frontend/.env.local ]; then cp frontend/.env.example frontend/.env.local; fi
	@echo "📦 Building containers..."
	docker-compose build
	@echo "✅ Setup complete! Run 'make dev' to start"

dev:
	@echo "🔥 Starting development environment..."
	docker-compose up

stop:
	@echo "⏸️  Stopping containers..."
	docker-compose stop

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v

migrate:
	@echo "📦 Running database migrations..."
	docker-compose exec backend alembic upgrade head

seed:
	@echo "🌱 Seeding database..."
	docker-compose exec backend python scripts/seed_db.py

test:
	@echo "🧪 Running tests..."
	docker-compose exec backend pytest -v
	@cd frontend && npm test

logs:
	docker-compose logs -f
