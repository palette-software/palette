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

install:
	cd app; python setup.py clean; python setup.py build; python setup.py install
	cd controller; python setup.py clean; python setup.py build; python setup.py install
.PHONY: install

#
# This rule will install using the debian packages
#
package_install:
	gdebi -n controller/DEBIAN/controller_1.0_all.deb
	gdebi -n app/DEBIAN/palette_1.0_all.deb

