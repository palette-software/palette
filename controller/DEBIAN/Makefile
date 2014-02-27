VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

all:
	rm -rf controller-*; mkdir -p controller-$(VERSION)
	cd controller-$(VERSION)
	cd .. && python setup.py sdist
	cp -f ../dist/controller-$(VERSION).tar.gz \
		controller_$(VERSION).orig.tar.gz
	cp -r debian controller-$(VERSION)/
	cd controller-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -uc -us
.PHONY: all

clean:
	rm -rf controller-$(VERSION) *.tar.gz *.dsc *.deb *.changes
.PHONY: clean

version:
	echo $(VERSION)
