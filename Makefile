all: palette controller

palette: 
	make -C app all
.PHONY: palette

controller:
	make -C controller all
.PHONY: controller

debian:
	make -C controller debian
	make -C app debian

pylint:
	make -C controller pylint
	make -C app pylint
.PHONY: pylint

clean:
	make -C app clean
	make -C controller clean
.PHONY: clean

build-setup:
	sudo apt-get install -y debhelper python-setuptools pylint
.PHONY: build-setup
