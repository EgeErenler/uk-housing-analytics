.PHONY: install test lint demo data clean

install:
	pip install -e ".[dev,charts]"

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .

# Offline demo on synthetic data in the real file format.
demo:
	ukhousing sample && ukhousing load && ukhousing analyse && ukhousing site --out site
	@echo "Open site/index.html"

# The real thing: about 1.5 GB of downloads, then a few minutes of SQL.
data:
	ukhousing all && ukhousing site --out site

clean:
	rm -rf data outputs site .pytest_cache .ruff_cache
