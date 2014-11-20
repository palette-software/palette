PKG1:= akiri.framework-sqlalchemy_0.1_all.deb
PKG2 = akiri.framework_0.4.0_all.deb
POOL_DIR = dpkg/pool
DOWNLOAD_DIR = https://www.akirisolutions.com/download/framework/
PREBUILT_PACKAGES = $(POOL_DIR)/$(PKG1) $(POOL_DIR)/$(PKG2)

all: palette controller

publish-release: $(PREBUILT_PACKAGES)
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/release

publish-early: $(PREBUILT_PACKAGES)
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/early

publish-dev: $(PREBUILT_PACKAGES)
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/dev

$(POOL_DIR)/$(PKG1):
	wget --directory-prefix=$(POOL_DIR) $(DOWNLOAD_DIR)/$(PKG1)

$(POOL_DIR)/$(PKG2):
	wget --directory-prefix=$(POOL_DIR) $(DOWNLOAD_DIR)/$(PKG2)

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
	rm -rf dpkg/dists dpkg/pool/*controller* dpkg/pool/*palette* dpkg/apt/db dpkg/apt/dists dpkg/apt/pool
.PHONY: clean

build-setup:
	sudo apt-get install -y debhelper reprepro python-setuptools pylint python-passlib
.PHONY: build-setup
