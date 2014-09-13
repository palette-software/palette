include ../pylint.mk

all:
	python setup.py bdist
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) palette/__init__.py
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
