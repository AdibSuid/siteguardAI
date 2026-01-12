# Makefile for SiteGuard AI

.PHONY: help setup install test run-api run-web clean docker-build docker-up

help:
	@echo "SiteGuard AI - Makefile Commands"
	@echo "================================="
	@echo "setup        - Setup development environment"
	@echo "install      - Install dependencies"
	@echo "test         - Run tests"
	@echo "run-api      - Run FastAPI backend"
	@echo "run-web      - Run Streamlit web app"
	@echo "clean        - Clean temporary files"
	@echo "docker-build - Build Docker image"
	@echo "docker-up    - Start Docker containers"

setup:
	python scripts/setup_env.py

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run-api:
	python scripts/run_api.py

run-web:
	python scripts/run_web.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
