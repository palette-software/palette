include ../pylint.mk

all: pylint debian
.PHONY: all

debian:
	make -C DEBIAN all
.PHONY: debian

pylint:
	$(PYLINT) DEBIAN/bin/sum-files
	$(PYLINT) DEBIAN/bin/upgrade-agent
	$(PYLINT) controller
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
