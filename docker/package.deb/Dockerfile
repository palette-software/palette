FROM ubuntu:14.04

WORKDIR /build

RUN sudo apt-get update

ADD dependencies/akiri.framework_0.5.6_all.deb /build
RUN sudo dpkg --install --force-depends /build/akiri.framework_0.5.6_all.deb
RUN sudo apt-get install -f -y

RUN sudo apt-get install -y build-essential
RUN sudo apt-get install -y pylint
RUN sudo apt-get install -y python-sqlalchemy

RUN sudo apt-get install -y python-dateutil python-mako python-yaml python-crypto python-boto python-passlib
RUN sudo apt-get install -y python-apt
RUN sudo apt-get install -y debhelper

RUN sudo apt-get install -y unzip # pushd app && make setup && popd

RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -

RUN sudo apt-get install -y nodejs

RUN npm install -g grunt bower gulp

RUN sudo apt-get install -y reprepro # deb sign
RUN sudo apt-get install -y zip
RUN sudo apt-get install -y wget
RUN sudo apt-get install -y git

ADD . /build

RUN useradd -d /home/ubuntu -m ubuntu -p $(echo "palette" | openssl passwd -1 -stdin)
RUN adduser ubuntu sudo

RUN sudo chown -R ubuntu:ubuntu /build

USER ubuntu

CMD /bin/bash
