include ../prepare_package.mk

.PHONY: create

create:
	rpmbuild -bb --buildroot $(shell pwd) -D "version $(VERSION)" -D "buildrelease 1" -D "_rpmdir rpm-build/_build" palettecentercontroller.spec
