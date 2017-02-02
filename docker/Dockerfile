FROM ubuntu:14.04
RUN apt-get update
RUN apt-get install -y apt-transport-https

# Add needed files
ADD palette.list /etc/apt/sources.list.d/palette.list
ADD trusted.gpg /etc/apt/trusted.gpg
# ADD paldb.sql /home/ubuntu/paldb.sql

# Add ubuntu user
RUN useradd -d /home/ubuntu -m ubuntu -p palette

# Install dependencies
RUN apt-get update
RUN apt-get install -y man
RUN apt-get install -y vim
RUN apt-get install -y python python-webob python-paste python-pastedeploy python-pastescript python-tz python-apt
RUN apt-get install -y python-sqlalchemy
RUN apt-get install -y controller
RUN apt-get install -y palette
RUN apt-get install -y curl

ADD postgresql.conf /etc/postgresql/9.3/main/postgresql.conf
ADD pg_hba.conf /etc/postgresql/9.3/main/pg_hba.conf

# Set locale
RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  

# USER postgres
ADD domain.sql /home/ubuntu/domain.sql
ADD environment.sql /home/ubuntu/environment.sql
ADD roles.sql /home/ubuntu/roles.sql
ADD users.sql /home/ubuntu/users.sql
ADD install.sh /home/ubuntu/install.sh
ADD start.sh /home/ubuntu/start.sh

# USER root

EXPOSE 443
EXPOSE 5432
EXPOSE 888

WORKDIR /home/ubuntu
# RUN /home/ubuntu/install.sh

