all: palette controller

palette: 
	make -C app all
.PHONY: palette

controller:
	make -C controller all
.PHONY: controller

clean:
	make -C app clean
	make -C controller clean
.PHONY: clean

install:
	cd app; python setup.py clean; python setup.py build; python setup.py install
	cd controller; python setup.py clean; python setup.py build; python setup.py install
.PHONY: install

#
# This rule will install using the debian packages
#
package_install:
	gdebi -n controller/DEBIAN/controller_0.2_all.deb
	gdebi -n app/DEBIAN/palette_0.2_all.deb

#
# This rule will setup development pre-requisites
#
development:
	apt-get install debhelper
	apt-get install gdebi
	wget https://www.akirisolutions.com/download/framework/akiri.framework_0.3.1_all.deb
	gdebi -n akiri.framework_0.3.1_all.deb
	wget https://www.akirisolutions.com/download/framework/akiri.framework-sqlalchemy_0.1_all.deb
	gdebi -n akiri.framework-sqlalchemy_0.1_all.deb
	wget https://www.akirisolutions.com/download/framework/python-apscheduler_2.1.2-1ubuntu1_all.deb
	gdebi -n python-apscheduler_2.1.2-1ubuntu1_all.deb
	apt-get install python-docutils python-sphinx postgresql python-sqlalchemy python-psycopg2 python-boto python-dateutil postfix
