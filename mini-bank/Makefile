.PHONY: help dev dev-sqlite seed test test-be test-fe build down clean

help:
	@echo "Targets:"
	@echo "  dev         - docker compose up (postgres + backend + frontend)"
	@echo "  dev-sqlite  - docker compose up with SQLite instead of Postgres"
	@echo "  seed        - load 40 customers, 3 employees, ~70 accounts, ~800 trx into running backend"
	@echo "  test        - run all backend pytest + frontend build sanity check"
	@echo "  test-be     - backend pytest only"
	@echo "  test-fe     - frontend build only (no test framework yet in v1)"
	@echo "  build       - docker compose build"
	@echo "  down        - docker compose down (keeps volumes)"
	@echo "  clean       - docker compose down -v (drops DB volumes)"

dev:
	docker compose up --build

dev-sqlite:
	docker compose -f docker-compose.yml -f docker-compose.sqlite.yml up --build

seed:
	docker compose exec backend python -m minibank.db.seed

test: test-be test-fe

test-be:
	cd backend && PYTHONPATH=src python3 -m pytest -v

test-fe:
	cd frontend && npm run build

build:
	docker compose build

down:
	docker compose down

clean:
	docker compose down -v
