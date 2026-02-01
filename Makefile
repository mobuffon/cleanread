.PHONY: help install dev up down clean test lint format

help:
	@echo "CleanRead - Available Commands:"
	@echo "  make install    - Install all dependencies"
	@echo "  make dev        - Start development servers"
	@echo "  make up         - Start Docker containers"
	@echo "  make down       - Stop Docker containers"
	@echo "  make clean      - Clean up generated files"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"

install:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Installation complete!"

dev:
	@echo "Starting development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:5173"
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload &
	cd frontend && npm run dev

up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Containers started!"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped!"

clean:
	@echo "Cleaning up..."
	cd backend && rm -rf __pycache__ .pytest_cache storage/*.pdf storage/*.epub
	cd frontend && rm -rf dist node_modules/.cache
	@echo "✅ Cleanup complete!"

test:
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test

lint:
	@echo "Linting backend..."
	cd backend && . venv/bin/activate && ruff check .
	@echo "Linting frontend..."
	cd frontend && npm run lint

format:
	@echo "Formatting backend..."
	cd backend && . venv/bin/activate && black .
	@echo "Formatting frontend..."
	cd frontend && npm run lint --fix
	@echo "✅ Code formatted!"
