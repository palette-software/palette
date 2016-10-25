PACKAGE := controller

# This version is used only for the package name.
VERSION := $(CONTROLLER_VERSION)
# VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

export PYTHONPATH:=$(PYTHONPATH):$(PWD)/controller
DATE:=`date +"%b %d, %Y"`

.PHONY: prepare clean version

all: prepare create
	# create target is defined in the DEBIAN and REDHAT directories

prepare:
	rm -rf $(PACKAGE)-*; mkdir -p $(PACKAGE)-$(VERSION)
	cp -a ../$(PACKAGE) ../setup.py $(PACKAGE)-$(VERSION)/
	# python -c "from controller.util import version; print 'VERSION=\'$(VERSION)\''" >$(PACKAGE)-$(VERSION)/controller/version.py
	echo "VERSION='"$(VERSION)"'" > $(PACKAGE)-$(VERSION)/controller/version.py
	echo "DATE='"$(DATE)"'" >> $(PACKAGE)-$(VERSION)/controller/version.py

clean:
	rm -rf $(PACKAGE)-* *.tar.gz *.dsc *.deb *.changes
	rm -rf usr/lib rpm-build

version:
	echo $(VERSION)
