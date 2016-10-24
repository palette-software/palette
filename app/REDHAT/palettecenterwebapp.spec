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
Requires: python-docutils, python-sphinx, python-sqlalchemy, python-psycopg2, python-dateutil, pytz
Requires: postgresql
Requires: telnet
Requires: controller >= 2.0.0
Requires: httpd, mod_wsgi

%description
This package contains the Palette Web Application.

# Variables
%define package palette
 
%pre
# noop

%postun
# noop

%prep
# noop

%build
# noop

%install
cd %{package}-%{version} && python setup.py install --root=../

%post
# noop

%clean
rm -rf %{package}-%{version}

%files
#%defattr(-,insight,insight,-)
# Reject config files already listed or parent directories, then prefix files
# with "/", then make sure paths with spaces are quoted.
#%dir /%{install_dir}
#/%{install_dir}/%packaged_msi_name
/etc
/opt
/usr
/var

%changelog
