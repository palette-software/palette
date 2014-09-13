PYLINT_DISABLED_WARNINGS := relative-import,missing-docstring,fixme,star-args,too-many-lines,locally-disabled,too-few-public-methods,too-many-ancestors,no-self-use
PYLINT_GOOD_NAMES := "i,j,k,x,ex,Run,d,pw,handle_GET,handle_POST"
PYLINT_OPTS := -rn -d $(PYLINT_DISABLED_WARNINGS) --good-names=$(PYLINT_GOOD_NAMES)
PYLINT := pylint $(PYLINT_OPTS)
