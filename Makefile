.DEFAULT_GOAL := run

export FLASK_APP = api
export FLASK_ENV = development

venv:
	@python3 -m venv .venv
	@. ./.venv/bin/activate
PHONY: venv

pip:
	@pip install -r requirements.txt
	@pip install '.[test]'
PHONY: pip

clean:
	@rm -rf .venv
	@rm -rf ./build
	@rm -rf ./dist
PHONY: clean

install: venv pip

lint:
	pylint api
PHONY: lint

pytest:
	pytest --junitxml=junit.xml
PHONY: pytest

run:
	flask run
PHONY: test
