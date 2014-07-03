#!/bin/bash
# Script to configure environment for development
#
# Install basic pre-requisites
apt-get install build-essential debhelper gdebi python-setuptools
apt-get install python-docutils python-sphinx postgresql python-sqlalchemy python-psycopg2 python-boto python-dateutil postfix

# Install Akiri packages
wget https://www.akirisolutions.com/download/framework/akiri.framework_0.3.1_all.deb
gdebi -n akiri.framework_0.3.1_all.deb

wget https://www.akirisolutions.com/download/framework/akiri.framework-sqlalchemy_0.1_all.deb
gdebi -n akiri.framework-sqlalchemy_0.1_all.deb

wget https://www.akirisolutions.com/download/framework/python-apscheduler_2.1.2-1ubuntu1_all.deb
gdebi -n python-apscheduler_2.1.2-1ubuntu1_all.deb
