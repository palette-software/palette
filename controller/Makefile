include ../pylint.mk

all: pylint debian
.PHONY: all

debian:
	make -C DEBIAN all
.PHONY: debian

pylint:
	$(PYLINT) controller
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
