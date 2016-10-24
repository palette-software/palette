PACKAGE := palette
VERSION := $(PALETTE_VERSION)
# VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

.PHONY: prepare clean version

all: prepare create
	# create target is defined in the DEBIAN and REDHAT directories

prepare:
	rm -rf $(PACKAGE)-*; mkdir -p $(PACKAGE)-$(VERSION)
	cp -a ../$(PACKAGE) ../setup.py $(PACKAGE)-$(VERSION)/
	rm -f $(PACKAGE)-$(VERSION)/$(PACKAGE)/controller
	cp -a ../etc .
	mkdir -p var/www/css var/www/fonts var/www/images var/www/js
	cp -a ../css var/www
	cp -a ../fonts var/www
	cp -a ../images var/www
	cp -a ../js var/www
	mkdir -p opt/palette
	cp -a ../application.wsgi opt/palette

clean:
	rm -f *.tar.gz *.dsc *.deb *.changes
	rm -rf opt var etc usr rpm-build
	rm -rf $(PACKAGE)-*

version:
	echo $(VERSION)
