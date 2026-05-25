.PHONY: run migrate makemigrations setup test lint clean backup preflight db-up db-down db-wait deploy loadtest loadtest-headless loadtest-seed loadtest-cleanup smoke-test

# Development
run:
	python manage.py runserver

run-asgi:
	daphne a_core.asgi:application --bind 0.0.0.0 --port 8000

# Database
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

seed:
	python manage.py seed_roles

# Setup
setup:
	pip install -r requirements.txt
	python manage.py migrate
	python manage.py setup_project --create-admin
	python manage.py collectstatic --noinput

seed-test:
	python manage.py seed_test_data

seed-test-cleanup:
	python manage.py seed_test_data --cleanup

preflight:
	python manage.py preflight

security-audit:
	python manage.py security_audit

# Testing
test:
	pytest

test-verbose:
	pytest -v

test-cov:
	pytest --cov --cov-report=term-missing

test-fast:
	pytest -x -q

test-django:
	python manage.py test

# Maintenance
backup:
	python manage.py backup_db

cleanup:
	python manage.py cleanup_data --days 90

cleanup-dry:
	python manage.py cleanup_data --days 90 --dry-run

# Static files
collectstatic:
	python manage.py collectstatic --noinput

# Docker (production stack)
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f web

# Docker (dev services only: PostgreSQL + Redis)
db-up:
	docker compose -f docker-compose.dev.yml up -d

db-down:
	docker compose -f docker-compose.dev.yml down

db-wait:
	python manage.py wait_for_db

db-reset:
	docker compose -f docker-compose.dev.yml down -v
	docker compose -f docker-compose.dev.yml up -d
	python manage.py wait_for_db --timeout 15
	python manage.py migrate

# Utilities
shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true

# Deployment
deploy:
	bash scripts/deploy.sh

setup-ssl:
	bash scripts/setup-ssl.sh

security-check:
	bash scripts/security-check.sh

ssl-renew:
	docker compose run --rm certbot renew
	docker compose restart nginx

logs-nginx:
	docker compose logs -f nginx

# Monitoring (Prometheus + Grafana)
monitoring-up:
	docker compose -f docker-compose.monitoring.yml up -d

monitoring-down:
	docker compose -f docker-compose.monitoring.yml down

monitoring-logs:
	docker compose -f docker-compose.monitoring.yml logs -f

# Load Testing (Locust)
loadtest:
	locust -f loadtests/locustfile.py

loadtest-headless:
	python -m loadtests.runner --users 50 --spawn-rate 5 --duration 60

loadtest-stress:
	python -m loadtests.runner --users 200 --spawn-rate 20 --duration 120

loadtest-seed:
	python manage.py create_loadtest_users

loadtest-cleanup:
	python manage.py create_loadtest_users --cleanup

# Smoke test (post-deployment)
smoke-test:
	bash scripts/smoke-test.sh http://localhost:8000

smoke-test-prod:
	bash scripts/smoke-test.sh https://${DOMAIN:-localhost}
