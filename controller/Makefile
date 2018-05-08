include ../pylint.mk
dpkg_dir := ../dpkg

all: redhat
.PHONY: all

redhat:
	make -C REDHAT all
.PHONY: redhat

debian:
	make -C DEBIAN all
	mkdir -p $(dpkg_dir)/pool
	cp -f DEBIAN/*.deb $(dpkg_dir)/pool
.PHONY: debian

pylint:
	pylint --version
	$(PYLINT) DEBIAN/usr/bin/upgrade-agent
	$(PYLINT) controller
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm -f '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
