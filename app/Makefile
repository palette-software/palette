include ../pylint.mk

all: pylint
	python setup.py bdist
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) palette
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
