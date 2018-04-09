FROM centos:7

WORKDIR /build

RUN yum install -y epel-release
RUN yum install -y gcc-c++ make
RUN yum install -y wget
RUN yum install -y unzip
RUN yum install -y git
RUN curl --silent --location https://rpm.nodesource.com/setup_6.x | bash -
RUN yum -y install nodejs
RUN npm install -g grunt bower gulp
RUN yum install -y pylint
RUN yum install -y rpm-build

ADD . /build

CMD /bin/bash
