.PHONY: dev down test lint format schema

dev:
	docker-compose up --build

down:
	docker-compose down

test:
	pytest tests/

lint:
	ruff check .

format:
	ruff format .

schema:
	python -c "from shared.schemas.billing import BillingRecord; print('Schema OK')"
