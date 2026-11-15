.PHONY: help install test build run docker-build docker-up

help:
	@echo "Available commands:"
	@echo "  make install       Install backend & frontend dependencies"
	@echo "  make test          Run full automated pytest test suite"
	@echo "  make build         Build production frontend bundle"
	@echo "  make run           Run server locally at http://localhost:8000"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start services via Docker Compose"
	@echo "  make scan          Run Trivy security scan on containers"

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
	docker build -t ghcr.io/sumit4h9/hospital-backend:v1.0.0 ./backend
	docker build -f ./backend/Dockerfile.worker -t ghcr.io/sumit4h9/hospital-worker:v1.0.0 ./backend
	docker build -t ghcr.io/sumit4h9/hospital-frontend:v1.0.0 ./frontend

docker-up:
	docker compose up --build

scan:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $(PWD):/root/.cache/ aquasec/trivy:latest fs --severity CRITICAL,HIGH .


