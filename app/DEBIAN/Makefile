PACKAGE := palette
VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

all:
	rm -rf $(PACKAGE)-*; mkdir -p $(PACKAGE)-$(VERSION)
	cp -a ../$(PACKAGE) ../setup.py $(PACKAGE)-$(VERSION)/
	rm -f $(PACKAGE)-$(VERSION)/$(PACKAGE)/controller
	cp -a MANIFEST.in etc debian $(PACKAGE)-$(VERSION)/
	cd $(PACKAGE)-$(VERSION) && python setup.py sdist --dist-dir=../
	mv $(PACKAGE)-$(VERSION).tar.gz $(PACKAGE)_$(VERSION).orig.tar.gz
	../../scripts/genchangelog.sh $(PACKAGE) $(VERSION) >\
		$(PACKAGE)-$(VERSION)/debian/changelog
	cd $(PACKAGE)-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -uc -us
.PHONY: all

clean:
	rm -rf $(PACKAGE)-$(VERSION) *.tar.gz *.dsc *.deb *.changes
.PHONY: clean

version:
	echo $(VERSION)
