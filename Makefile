PALETTE_PROJECT_DIR=app
PALETTE_PROJECT=palette
PALETTE_VERSION=0.1
PALETTE_PACKAGE=$(PALETTE_PROJECT)-$(PALETTE_VERSION)

CONTROLLER_PROJECT=controller
CONTROLLER_VERSION=0.1
CONTROLLER_PACKAGE=$(CONTROLLER_PROJECT)-$(CONTROLLER_VERSION)

all: palette

#all: controller

palette: 
	# Add the required "project-version" directory via a symbolic link.
	rm -f $(PALETTE_PACKAGE); ln -s $(PALETTE_PROJECT_DIR) $(PALETTE_PACKAGE)
	# Build the SOURCE package
	cd $(PALETTE_PACKAGE) && python setup.py sdist $(COMPILE) --dist-dir=../
	# rename it to project_version.orig.tar.gz
	rename -f 's/$(PALETTE_PROJECT)-(.*)\.tar\.gz/$(PALETTE_PROJECT)_$$1\.orig\.tar\.gz/' *
	# Build the BINARY package
	cd $(PALETTE_PACKAGE) && dpkg-buildpackage -i -I -rfakeroot
	# Remove the "project-version" symbolic link that was needed for the build.
	rm -f $(PALETTE_PACKAGE)
.PHONY: palette

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
