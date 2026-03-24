.PHONY: install run debug clean lint lint-strict

install:
	python3 -m pip install --upgrade pip
	python3 -m pip install flake8 mypy

run:
	python3 parser.py

debug:
	python3 -m pdb parser.py

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs