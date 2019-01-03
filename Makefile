
version = 0.1.0

.PHONY: build release default

default: build

build:
	rm -rf build
	mkdir -p build/pico8
	cp -r web build/pico8/
	cp web.py build/pico8/
	echo "$(version)" > build/pico8/version

release: build
	cd build; tar -zcf pico8-runner.tar.gz pico8