VERSION := $(shell awk 'match($$0, /[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH) }' ../setup.py)

all:
	rm -rf palette-*; mkdir -p palette-$(VERSION)
	cd palette-$(VERSION)
	cd .. && python setup.py sdist
	cp -f ../dist/palette-$(VERSION).tar.gz \
		palette_$(VERSION).orig.tar.gz
	cp -r debian palette-$(VERSION)/
	cd palette-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -uc -us
.PHONY: all

clean:
	rm -rf palette-$(VERSION) *.tar.gz *.dsc *.deb *.changes
.PHONY: clean

version:
	echo $(VERSION)
