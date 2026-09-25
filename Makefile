.PHONY: install index build dev test clean

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

index:
	.venv/bin/python -m gallery index

build:
	.venv/bin/python -m gallery build

dev: build
	cd dist && ../.venv/bin/python -m http.server 8000

test:
	.venv/bin/python -m unittest discover -s tests -t .

clean:
	rm -rf dist gallery/data/gallery.json
