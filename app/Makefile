include ../pylint.mk

all: pylint
	python setup.py bdist
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) palette/__init__.py
	$(PYLINT) palette/about.py
	$(PYLINT) palette/activity.py
	$(PYLINT) palette/auth.py
	$(PYLINT) palette/backup.py
	$(PYLINT) palette/billing.py
	$(PYLINT) palette/environment.py
	$(PYLINT) palette/event.py
	$(PYLINT) palette/gcs.py
	$(PYLINT) palette/general.py
	$(PYLINT) palette/passwd.py
	$(PYLINT) palette/request.py
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
