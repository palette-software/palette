PKG1 = akiri.framework_0.5.0_all.deb
POOL_DIR = dpkg/pool
DOWNLOAD_DIR = https://www.akirisolutions.com/download/framework/
PREBUILT_PACKAGES = $(POOL_DIR)/$(PKG1)

all: palette controller palette-agent palette-support myip

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

publish-dev2: $(PREBUILT_PACKAGES)
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/dev2

publish-dev3: $(PREBUILT_PACKAGES)
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/dev3

publish-sc: $(PREBUILT_PACKAGES)
	make clean all
	GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb
	chmod 600 dpkg/client/id_rsa; cd dpkg/apt; scp -r -i ../client/id_rsa -r . ubuntu@apt.palette-software.com:/var/packages/sc

$(POOL_DIR)/$(PKG1):
	wget --directory-prefix=$(POOL_DIR) $(DOWNLOAD_DIR)/$(PKG1)

palette: 
	make -C app all
.PHONY: palette

controller:
	make -C controller all
.PHONY: controller

palette-agent:
	make -C ../palette-agent all
.PHONY: palette-agent

palette-support:
	make -C ../palette-support all
.PHONY: palette-support

myip:
	make -C ../myip
.PHONY: myip

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
	sudo apt-get install -y debhelper reprepro python-setuptools pylint python-passlib python-tz
	sudo apt-get install -y python-dateutil python-crypto python-boto
	sudo apt-get install -y python-netifaces
	sudo apt-get install -y npm nodejs-legacy
	sudo npm install -g less
	sudo npm install -g grunt-cli
	cd app; sudo ../scripts/setup.sh

.PHONY: build-setup
