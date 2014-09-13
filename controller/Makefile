include ../pylint.mk

all: pylint
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) controller/controller.py
#	find . -name \*.py -exec pylint $(PYLINT_OPTS) '{}'  ';'
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
