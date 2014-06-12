PACKAGE := controller
VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

all:
	rm -rf $(PACKAGE)-*; mkdir -p $(PACKAGE)-$(VERSION)
	cp -a ../$(PACKAGE) ../setup.py $(PACKAGE)-$(VERSION)/
	cp -a MANIFEST.in bin etc var debian $(PACKAGE)-$(VERSION)/
	cd $(PACKAGE)-$(VERSION) && python setup.py sdist --dist-dir=../
	mv $(PACKAGE)-$(VERSION).tar.gz $(PACKAGE)_$(VERSION).orig.tar.gz
	cd $(PACKAGE)-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -uc -us
.PHONY: all

clean:
	rm -rf $(PACKAGE)-$(VERSION) *.tar.gz *.dsc *.deb *.changes
.PHONY: clean

version:
	echo $(VERSION)
