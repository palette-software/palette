PYLINT_DISABLED_WARNINGS := relative-import,missing-docstring,fixme,star-args,too-many-lines,locally-disabled,too-few-public-methods
PYLINT_GOOD_NAMES := "i,j,k,ex,Run,d,pw"
PYLINT_OPTS := -rn -d $(PYLINT_DISABLED_WARNINGS) --good-names=$(PYLINT_GOOD_NAMES)
PYLINT := pylint $(PYLINT_OPTS)
