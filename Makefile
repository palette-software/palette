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

package_install:
	sudo dpkg -i controller/DEBIAN/controller_0.2_all.deb
	sudo dpkg -i app/DEBIAN/palette_0.2_all.deb

