PYLINT_DISABLED_WARNINGS := relative-import,missing-docstring,fixme,star-args,too-many-lines,locally-disabled
PYLINT_GOOD_NAMES := "i,j,k,ex,Run,d,pw"
PYLINT_OPTS := -rn -d $(PYLINT_DISABLED_WARNINGS) --good-names=$(PYLINT_GOOD_NAMES)

all: pylint
	make -C DEBIAN all
.PHONY: all

pylint:
	pylint controller/controller.py $(PYLINT_OPTS)
#	find . -name \*.py -exec pylint $(PYLINT_OPTS) '{}'  ';'

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
