include ../pylint.mk

all: pylint
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) controller/controller.py
	$(PYLINT) controller/auth.py
	$(PYLINT) controller/extracts.py
	$(PYLINT) controller/http_requests.py
	$(PYLINT) controller/odbc.py
	$(PYLINT) controller/util.py
#	find . -name \*.py -exec pylint $(PYLINT_OPTS) '{}'  ';'
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
