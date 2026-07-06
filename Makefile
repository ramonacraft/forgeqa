# Shortcuts. Run `make help` to see them.

.PHONY: help setup run test example compose-up compose-down

help:
	@echo "setup        - create venv, install deps, install chromium"
	@echo "run          - start the Streamlit dashboard (dev, LM Studio)"
	@echo "example      - run the reference saucedemo test"
	@echo "test         - run all tests under examples/ and generated_tests/"
	@echo "compose-up   - customer deploy (Ollama + app in Docker)"
	@echo "compose-down - stop the Docker stack"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt && playwright install chromium
	cp -n .env.example .env || true

run:
	. .venv/bin/activate && streamlit run app/dashboard.py

example:
	. .venv/bin/activate && pytest examples/test_saucedemo_login.py

test:
	. .venv/bin/activate && pytest examples generated_tests

compose-up:
	docker compose up --build

compose-down:
	docker compose down
