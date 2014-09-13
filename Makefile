all: palette controller

palette: 
	make -C app all
.PHONY: palette

controller:
	make -C controller all
.PHONY: controller

clean:
	make -C app clean
	make -C controller clean
.PHONY: clean

build-setup:
	sudo apt-get install -y debhelper python-setuptools pylint
