PYLINT_DISABLED_WARNINGS := relative-import,missing-docstring,fixme,star-args,too-many-lines,locally-disabled,too-few-public-methods,too-many-ancestors,no-self-use,duplicate-code --ignored-classes=SQLObject,scoped_session
PYLINT_GOOD_NAMES := "i,j,k,d,f,s,x,ex,Run,pw,handle_GET,handle_POST,id"
PYLINT_OPTS := -rn -d $(PYLINT_DISABLED_WARNINGS) --good-names=$(PYLINT_GOOD_NAMES)
PYLINT := pylint $(PYLINT_OPTS)
