all: palette controller

publish:
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/release

publish-test:
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/test

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
	rm -rf dpkg/dists dpkg/pool dpkg/apt/db dpkg/apt/dists dpkg/apt/pool
.PHONY: clean

build-setup:
	sudo apt-get install -y debhelper reprepro python-setuptools pylint
.PHONY: build-setup
