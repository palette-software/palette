CONTROLLER_PROJECT=controller
CONTROLLER_VERSION=0.1
CONTROLLER_PACKAGE=$(CONTROLLER_PROJECT)-$(CONTROLLER_VERSION)

all: controller

controller: 
	# Add the required "project-version" directory via a symbolic link.
	rm -f $(CONTROLLER_PACKAGE); ln -s $(CONTROLLER_PROJECT) $(CONTROLLER_PACKAGE)
	# Build the SOURCE package
	cd $(CONTROLLER_PACKAGE) && python setup.py sdist $(COMPILE) --dist-dir=../
	# rename it to project_version.orig.tar.gz
	rename -f 's/$(CONTROLLER_PROJECT)-(.*)\.tar\.gz/$(CONTROLLER_PROJECT)_$$1\.orig\.tar\.gz/' *
	# Build the BINARY package
	cd $(CONTROLLER_PACKAGE) && dpkg-buildpackage -i -I -rfakeroot
	# Remove the "project-version" symbolic link that was needed for the build.
	rm -f $(CONTROLLER_PACKAGE)
.PHONY: controller
