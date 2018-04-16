include ../pylint.mk
dpkg_dir := ../dpkg

all: grunt pylint redhat
.PHONY: all

redhat:
	make -C REDHAT all
.PHONY: redhat

debian:
	make -C DEBIAN all
	mkdir -p $(dpkg_dir)/pool
	cp -r DEBIAN/*.deb $(dpkg_dir)/pool
dpkg_dir := ../dpkg

.PHONY: debian

grunt:
	grunt less
.PHONY: grunt

pylint:
	pylint --version
	$(PYLINT) application.wsgi
	$(PYLINT) palette
.PHONY: pylint

check-tabs:
	grep -P "\t" palette/templates/*.mako; test $$? -ne 0
.PHONY: check-tabs

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
	rm -f css/style.css css/palette.css.map
.PHONY: pylint

realclean: clean
	rm -rf bootstrap-* font-awesome-* downloads node_modules
.PHONY: realclean

setup:
	../scripts/setup.sh
.PHONY: setup
