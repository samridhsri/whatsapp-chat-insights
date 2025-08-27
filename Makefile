.PHONY: help install install-dev test test-cov lint format clean build run run-ui run-cli docker-build docker-run docker-stop

# Default target
help:
	@echo "WhatsApp Chat Analyzer - Development Commands"
	@echo "============================================="
	@echo ""
	@echo "Installation:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with Black"
	@echo "  clean        Clean build artifacts"
	@echo ""
	@echo "Running:"
	@echo "  run          Run with auto-detection"
	@echo "  run-ui       Run Streamlit UI"
	@echo "  run-cli      Run CLI with help"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"
	@echo "  docker-stop  Stop Docker services"
	@echo ""
	@echo "Build:"
	@echo "  build        Build package"
	@echo "  install-pkg  Install package in development mode"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt[dev]

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=whatsapp_analyzer --cov-report=html --cov-report=term

# Code Quality
lint:
	flake8 whatsapp_analyzer/ tests/
	mypy whatsapp_analyzer/

format:
	black whatsapp_analyzer/ tests/
	isort whatsapp_analyzer/ tests/

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Building
build:
	python setup.py sdist bdist_wheel

install-pkg:
	pip install -e .

# Running
run:
	python main.py

run-ui:
	python main.py --ui

run-cli:
	python main.py --cli --help

# Docker
docker-build:
	docker build -t whatsapp-analyzer .

docker-run:
	docker-compose up --build

docker-stop:
	docker-compose down

# Development workflow
dev-setup: install-dev install-pkg
	@echo "Development environment setup complete!"

check: lint test
	@echo "All checks passed!"

pre-commit: format lint test
	@echo "Pre-commit checks complete!"

# Utility
logs:
	tail -f logs/app.log

shell:
	python -c "import whatsapp_analyzer; print('Package imported successfully!')"

# Documentation
docs:
	@echo "Building documentation..."
	# Add documentation building commands here when implemented

# Deployment
deploy: clean build
	@echo "Package built successfully!"
	@echo "Ready for deployment!"

# Help for specific targets
install-help:
	@echo "Installation Options:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make install-pkg  - Install package in development mode"

test-help:
	@echo "Testing Options:"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make test tests/test_parser.py - Run specific test file"

docker-help:
	@echo "Docker Options:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run with Docker Compose"
	@echo "  make docker-stop  - Stop Docker services" 