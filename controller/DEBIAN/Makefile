PACKAGE := controller

# This version is used only for the package name.
VERSION := $(CONTROLLER_VERSION)
# VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

export PYTHONPATH:=$(PYTHONPATH):$(PWD)/controller
DATE:=`date +"%b %d, %Y"`

all:
	rm -rf $(PACKAGE)-*; mkdir -p $(PACKAGE)-$(VERSION)
	cp -a ../$(PACKAGE) ../setup.py $(PACKAGE)-$(VERSION)/
	cp -a MANIFEST.in etc var usr debian $(PACKAGE)-$(VERSION)/
	python -c "from controller.util import version; print 'VERSION=\'$(VERSION)\''" >$(PACKAGE)-$(VERSION)/controller/version.py
	echo "DATE='"$(DATE)"'" >> $(PACKAGE)-$(VERSION)/controller/version.py
	cd $(PACKAGE)-$(VERSION) && python setup.py sdist --dist-dir=../
	echo "xxxxxxxxxxxxxxxxxxxx"
	tar -tzvf $(PACKAGE)-$(VERSION).tar.gz
	echo "xxxxxxxxxxxxxxxxxxx"
	mv $(PACKAGE)-$(VERSION).tar.gz $(PACKAGE)_$(VERSION).orig.tar.gz
	../../scripts/genchangelog.sh $(PACKAGE) $(VERSION)
	../../scripts/genchangelog.sh $(PACKAGE) $(VERSION) >\
		$(PACKAGE)-$(VERSION)/debian/changelog
	cat $(PACKAGE)-$(VERSION)/debian/changelog
	cd $(PACKAGE)-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -uc -us
.PHONY: all

clean:
	rm -rf $(PACKAGE)-* *.tar.gz *.dsc *.deb *.changes
.PHONY: clean

version:
	echo $(VERSION)
