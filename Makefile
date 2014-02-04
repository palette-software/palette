PYVERS := 2.7

dpkg_dir := dpkg

all: controller

controller: clean
	mkdir -p debian/controller/usr/sbin
	cp -a pcontroller debian/controller/usr/sbin/controller
	python setup.py install --root=$(PWD)/debian/controller --install-lib=/usr/lib/python$(PYVERS)/dist-packages
	# Move any old packages out of the way
	mkdir -p old
	-mv *.deb old
	fakeroot dpkg-deb --build debian/controller .
	# Place the package in the pool directory
	rm -rf $(dpkg_dir)/pool; mkdir -p $(dpkg_dir)/pool
	cp -rf *.deb $(dpkg_dir)/pool
.PHONY: controller

clean:
	rm -rf debian/controller/usr debian/client/usr connector.egg-info build
	rm -rf dpkg/dists dpkg/pool dpkg/apt/db dpkg/apt/dists dpkg/apt/pool
	rm -rf *.deb
.PHONY: clean

install:
	dpkg -i connector_*.deb
.PHONY: install

uninstall: 
	dpkg -r connector
.PHONY: uninstall

reinstall: uninstall install
.PHONY: reinstall

list:
	dpkg --contents connector_*.deb
.PHONY: list
