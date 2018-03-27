# Disable the stupid stuff rpm distros include in the build process by default:
#   Disable any prep shell actions. replace them with simply 'true'
%define __spec_prep_post true
%define __spec_prep_pre true
#   Disable any build shell actions. replace them with simply 'true'
%define __spec_build_post true
%define __spec_build_pre true
#   Disable any install shell actions. replace them with simply 'true'
%define __spec_install_post true
%define __spec_install_pre true
#   Disable any clean shell actions. replace them with simply 'true'
%define __spec_clean_post true
%define __spec_clean_pre true
# Disable checking for unpackaged files ?
#%undefine __check_files

# Use md5 file digest method.
# The first macro is the one used in RPM v4.9.1.1
%define _binary_filedigest_algorithm 1
# This is the macro I find on OSX when Homebrew provides rpmbuild (rpm v5.4.14)
%define _build_binary_file_digest_algo 1

# Use bzip2 payload compression
%define _binary_payload w9.bzdio

# Enable bash specific commands (eg. pushd)
%define _buildshell /bin/bash

#
# The Preamble
#
Name: palette-center-webapp
Version: %{version}
Release: %{buildrelease}
Summary: Palette Center Web App
Group: Productivity/Other
License: commercial
Vendor: Palette Software
URL: http://www.palette-software.com
Packager: Palette Developers <developers@palette-software.com>
BuildArch: noarch
# Disable Automatic Dependency Processing
AutoReqProv: no
# Add prefix, must not end with / except for root (/)
Prefix: /
# Seems specifying BuildRoot is required on older rpmbuild (like on CentOS 5)
# fpm passes '--define buildroot ...' on the commandline, so just reuse that.
# BuildRoot: %buildroot

BuildRequires: python >= 2.6 python-setuptools 

Requires: python
Requires: python-docutils, python-sphinx, python-webob
Requires: python-sqlalchemy, python-psycopg2, python-dateutil, pytz
Requires: postgresql
Requires: telnet
Requires: httpd, mod_wsgi, mod_ssl
Requires: palette-center-controller >= 2.0.0
Requires: akiri.framework

%description
This package contains the Palette Web Application.

# Variables
%define package palette
 
%prep
# noop

%build
# noop

%install
mkdir -p var/log/palette
mkdir -p opt/palette/plugins
cd %{package}-%{version} && python setup.py install --single-version-externally-managed --no-compile --root=../ --record=INSTALLED_FILES
sed -i -e 's#^#%{prefix}#' INSTALLED_FILES

%clean
rm -rf %{package}-%{version}

%post
PYTHON_PACKAGE_DIR=$(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

# /usr/sbin/a2enmod ssl rewrite proxy_connect

# port 80/http site is used only to redirect to 443/https
# /usr/sbin/a2dissite 000-default

# pyshared can't be used here, it doesn't exist on 14.04
cd /opt/palette/plugins
for x in `ls -d ${PYTHON_PACKAGE_DIR}/palette*`; do
    ln -s -f $x
done

chkconfig --add framework-postfix
service framework-postfix start

chkconfig --add framework-ssl
service framework-ssl start

chkconfig --add framework-timezone
service framework-timezone start

service httpd stop
service httpd start 

%files -f %{buildroot}/%{package}-%{version}/INSTALLED_FILES
%config /etc/httpd/conf.d/palette.conf
%config /etc/httpd/conf.d/palette-software-ssl.conf
%config /etc/httpd/conf.d/palette-software.conf
%config /etc/init.d/framework-postfix
%config /etc/init.d/framework-ssl
%config /etc/init.d/framework-timezone
%config /etc/ssl/certs/palette_server.crt
%attr(640, -, -) %config /etc/ssl/private/palette_server.key

%attr(640, apache, apache) /opt/palette/application.wsgi
%attr(640, apache, apache) %dir /opt/palette/plugins

%attr(-, apache, apache) %dir /var/log/palette 
/var

%changelog
