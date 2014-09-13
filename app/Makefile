include ../pylint.mk

all: pylint
	python setup.py bdist
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) palette/__init__.py
	$(PYLINT) palette/auth.py
	$(PYLINT) palette/passwd.py
	$(PYLINT) palette/request.py
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
