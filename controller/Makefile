include ../pylint.mk

all: pylint
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) controller/controller.py
	$(PYLINT) controller/agentmanager.py
	$(PYLINT) controller/auth.py
	$(PYLINT) controller/clihandler.py
	$(PYLINT) controller/clierror.py
	$(PYLINT) controller/event.py
	$(PYLINT) controller/extracts.py
	$(PYLINT) controller/http_requests.py
	$(PYLINT) controller/licensing.py
	$(PYLINT) controller/odbc.py
	$(PYLINT) controller/system.py
	$(PYLINT) controller/system.py
	$(PYLINT) controller/tableau.py
	$(PYLINT) controller/util.py
#	find . -name \*.py -exec pylint $(PYLINT_OPTS) '{}'  ';'
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
