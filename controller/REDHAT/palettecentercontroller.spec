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
Name: palette-center-controller
Version: %{version}
Release: %{buildrelease}
Summary: Palette Center Controller
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
Requires: python-docutils, python-sphinx
Requires: python-sqlalchemy, python-psycopg2, python-dateutil
Requires: python-crypto, python-boto, python-mako, PyYAML
Requires: postgresql-server
Requires: telnet, postfix, ntp
Requires: akiri.framework >= 0.5.6
# Requires: daemon ????
# Requires: palette-agent >= 1.6.0, palette-support >= 1.4.0

%description
This package contains the Palette Controller and Web Application
 for controlling, monitoring and managing Tableau databases.

# Variables
%define package controller
 
%prep
# noop

%build
# noop

%install
# mkdir -p var/log/palette
# mkdir -p opt/palette/plugins
cd %{package}-%{version} && python setup.py install --single-version-externally-managed --no-compile --root=../ --record=INSTALLED_FILES
sed -i -e 's#^#%{prefix}#' INSTALLED_FILES

%clean
# rm -rf %{package}-%{version}

%post
install_type=$1

rm -f /etc/ssl/private/ssl-cert-palette-software.key
rm -f /etc/ssl/certs/star_palette-software_com.crt

# Get the database in a state where we can ALTER it, if needed.
set +o errexit
systemctl status postgresql
APACHE_STATUS=$?
set -o errexit

if [ $APACHE_STATUS -eq 0 ];
then
    systemctl restart httpd
fi

# POSTGRES_CONFIG_FILE=/etc/postgresql/9.3/main/postgresql.conf
# if grep -q '^max_connections = 100' $POSTGRES_CONFIG_FILE
# then
#     sed --in-place 's/^max_connections = 100/max_connections = 300/' $POSTGRES_CONFIG_FILE
# fi

systemctl restart postgresql

if [ "$install_type" -gt "1" ]; then
    echo Upgrading $install_type
    # We are upgrading from a previous version (vs. a new install).
    # Currently: nothing special to do.
elif [ "$install_type" -eq "1" ]; then
    echo First install

    # The "| echo" is so it returns exit status of 0 even if they already exist.
    sudo -u postgres createuser --superuser $USER 2>&1 | echo

    echo CREATE ROLE palette WITH SUPERUSER LOGIN PASSWORD \'palpass\' | sudo -u postgres psql 2>&1 | echo

    sudo -u postgres createdb paldb 2>&1 | echo
    psql paldb -c "ALTER DATABASE paldb SET timezone TO 'GMT'" 2>&1 | echo

    mkdir -p /var/log/palette /var/palette/data/workbook-archive
    if [ ! -f /var/palette/.aes ]; then
        dd if=/dev/urandom of=/var/palette/.aes bs=32 count=1
        chown www-data /var/palette/.aes
        chmod 0400 /var/palette/.aes
    fi
fi

chkconfig --add controller
service controller start

# Restart apache if it had been running before
if [ $APACHE_STATUS -eq 0 ];
then
    systemctl restart httpd
fi

%files -f %{buildroot}/%{package}-%{version}/INSTALLED_FILES
/etc/controller.ini
/etc/ssl/certs/palette_cert.pem
/etc/systemd/system/multi-user.target.wants/controller.service
/usr/bin/controller
/usr/bin/upgrade-agent
/usr/bin/palette-version
/usr/sbin/palette-backup
/usr/sbin/palette-restore
/usr/sbin/palette-update
/usr/sbin/palette-update-sc
/usr/share/palette/conf/key.asc
/var/palette/sched/auth_import
/var/palette/sched/backup
/var/palette/sched/checkports
/var/palette/sched/cpu_load
/var/palette/sched/daily
/var/palette/sched/extract
/var/palette/sched/info_all
/var/palette/sched/license_check
/var/palette/sched/license_verify
/var/palette/sched/metrics_prune
/var/palette/sched/sync
/var/palette/sched/workbook
/var/palette/sched/datasource
/var/palette/sched/yml
/var/palette/sched/agent_upgrader

%changelog
