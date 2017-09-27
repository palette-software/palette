FROM ubuntu:14.04

WORKDIR /root

# Install local repository
RUN apt-get update
RUN apt-get install unzip
ADD palette-*.zip .
RUN unzip palette-*.zip
ADD palette.local.list /etc/apt/sources.list.d/

# Install Center
RUN apt-get update
RUN apt-get install -d -y --force-yes palette controller
RUN apt-get install -y --force-yes akiri.framework daemon ntp palette-agent palette-support postfix telnet \
   python python-apt python-boto python-crypto python-dateutil python-docutils python-mako python-passlib \
   python-psycopg2 python-sphinx python-sqlalchemy python-tz python-yaml libpython2.7 \
   libaprutil1 libaprutil1-dbd-sqlite3 libaprutil1-ldap libxml2
RUN apt-get install -d -y --force-yes apache2 apache2-bin apache2-data controller libapache2-mod-wsgi palette \
  postgresql postgresql-9.3 postgresql-client-9.3 postgresql-client-common postgresql-common

# Set locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Expose ports
EXPOSE 443
EXPOSE 5432
EXPOSE 888

# Add volumes
VOLUME /var/log/palette /var/log/apache2 /var/log/postgresql /var/lib/postgresql/9.3/main

# Run Center
ADD docker-entrypoint.sh .
CMD ["/root/docker-entrypoint.sh"]
