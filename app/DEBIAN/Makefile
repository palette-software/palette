PACKAGE := palette
VERSION := $(PALETTE_VERSION)
# VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

all:
	rm -rf $(PACKAGE)-*; mkdir -p $(PACKAGE)-$(VERSION)
	cp -a ../$(PACKAGE) ../setup.py $(PACKAGE)-$(VERSION)/
	rm -f $(PACKAGE)-$(VERSION)/$(PACKAGE)/controller
	cp -a MANIFEST.in etc debian $(PACKAGE)-$(VERSION)/
	mkdir -p var/www/css var/www/fonts var/www/images var/www/js
	cp -a ../css var/www
	cp -a ../fonts var/www
	cp -a ../images var/www
	cp -a ../js var/www
	mkdir -p opt
	cp -a ../application.wsgi opt
	cd $(PACKAGE)-$(VERSION) && python setup.py sdist --dist-dir=../
	echo "xxxxxxxxxxxxxxxxxxxx"
	tar -tzvf $(PACKAGE)-$(VERSION).tar.gz
	echo "xxxxxxxxxxxxxxxxxxx"
	mv $(PACKAGE)-$(VERSION).tar.gz $(PACKAGE)_$(VERSION).orig.tar.gz
	../../scripts/genchangelog.sh $(PACKAGE) $(VERSION)
	../../scripts/genchangelog.sh $(PACKAGE) $(VERSION) > $(PACKAGE)-$(VERSION)/debian/changelog
	ls -ltr $(PACKAGE)-$(VERSION)/debian/
	cat $(PACKAGE)-$(VERSION)/debian/changelog
	cd $(PACKAGE)-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -uc -us
.PHONY: all

clean:
	rm -rf $(PACKAGE)-* *.tar.gz *.dsc *.deb *.changes
	rm -rf opt var
.PHONY: clean

version:
	echo $(VERSION)
