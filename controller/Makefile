include ../pylint.mk
dpkg_dir := ../dpkg

all: pylint debian
.PHONY: all

debian:
	make -C DEBIAN all
	mkdir -p $(dpkg_dir)/pool
	cp -f DEBIAN/*.deb $(dpkg_dir)/pool
.PHONY: debian

pylint:
	$(PYLINT) DEBIAN/usr/bin/upgrade-agent
	$(PYLINT) controller
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm -f '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
