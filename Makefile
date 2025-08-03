.PHONY: help install run test clean migrate superuser seed-data daphne redis docker-build docker-run

help:
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

install:
	pip install -r requirements.txt

run:
	python manage.py runserver

daphne:
	daphne -b 0.0.0.0 -p 8000 config.asgi:application

redis:
	redis-server

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

superuser:
	python manage.py createsuperuser

seed-data:
	python manage.py seed_data

test:
	python manage.py test

shell:
	python manage.py shell

collectstatic:
	python manage.py collectstatic --noinput

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

format:
	black apps/ config/

lint:
	flake8 apps/ config/

sort-imports:
	isort apps/ config/

docker-build:
	docker build -f deployments/Dockerfile -t bugtracker .

docker-run:
	docker run -p 8000:8000 bugtracker

docker-compose-up:
	docker compose -f deployments/docker-compose.yml up -d

docker-compose-down:
	docker compose -f deployments/docker-compose.yml down

docker-compose-logs:
	docker compose -f deployments/docker-compose.yml logs -f

docker-prod-up:
	docker compose -f deployments/docker-compose.prod.yml up -d

docker-prod-down:
	docker compose -f deployments/docker-compose.prod.yml down

setup: install migrate seed-data

dev: run

prod: daphne