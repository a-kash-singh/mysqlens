.PHONY: help build up down logs clean dev

help:
	@echo "OptiSchema-MySQL - Makefile Commands"
	@echo "===================================="
	@echo "make build      - Build Docker images"
	@echo "make up         - Start services in production mode"
	@echo "make down       - Stop services"
	@echo "make logs       - View logs"
	@echo "make clean      - Remove containers and volumes"
	@echo "make dev        - Start services in development mode"
	@echo "make restart    - Restart services"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

dev:
	docker-compose -f docker-compose.dev.yml up

restart:
	docker-compose restart

stop:
	docker-compose stop

