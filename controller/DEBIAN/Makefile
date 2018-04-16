include ../prepare_package.mk

.PHONY: create

create:
	cp -a MANIFEST.in etc var usr debian $(PACKAGE)-$(VERSION)/
	cd $(PACKAGE)-$(VERSION) && python setup.py sdist --dist-dir=../
	mv $(PACKAGE)-$(VERSION).tar.gz $(PACKAGE)_$(VERSION).orig.tar.gz
	../../scripts/genchangelog.sh $(PACKAGE) $(VERSION)
	../../scripts/genchangelog.sh $(PACKAGE) $(VERSION) >\
		$(PACKAGE)-$(VERSION)/debian/changelog
	cd $(PACKAGE)-$(VERSION) && dpkg-buildpackage -i -I -rfakeroot -uc -us
