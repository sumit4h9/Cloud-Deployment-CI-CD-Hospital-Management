.PHONY: help install test build run docker-build docker-up

help:
	@echo "Available commands:"
	@echo "  make install       Install backend & frontend dependencies"
	@echo "  make test          Run full automated pytest test suite"
	@echo "  make build         Build production frontend bundle"
	@echo "  make run           Run server locally at http://localhost:8000"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start services via Docker Compose"

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	python -m pytest backend/tests -v

build:
	cd frontend && npm run build

run: build
	uvicorn backend.app.main:app --port 8000 --reload

docker-build:
	docker build -t doctor-appointment-api .

docker-up:
	docker compose up --build

