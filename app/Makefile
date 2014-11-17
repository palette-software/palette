include ../pylint.mk
dpkg_dir := ../dpkg

all: pylint debian
.PHONY: all

debian:
	python setup.py bdist
	make -C DEBIAN all
	mkdir -p $(dpkg_dir)/pool
	cp -r DEBIAN/*.deb $(dpkg_dir)/pool
dpkg_dir := ../dpkg

.PHONY: debian

pylint:
	$(PYLINT) palette
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
