.PHONY: run install test lint clean docker-build docker-up docker-down

run:
	streamlit run app.py

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

lint:
	python -m py_compile app.py
	python -m py_compile config.py
	python -c "from src.schemas import *; from src.providers.base import *; from src.prompts import *; from src.services import *; print('All modules compile OK')"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
