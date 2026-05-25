.PHONY: build build-wheel build-sdist publish clean

build:
	uv build

build-wheel:
	uv build --wheel

publish: build
	uv publish

clean:
	rm -rf build dist *.egg-info src/*.egg-info
