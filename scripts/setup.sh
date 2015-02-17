#!/bin/bash

VERSION=v3.3.2
TARBALL=$VERSION.tar.gz
URL=https://github.com/twbs/bootstrap/archive/$TARBALL

if [ ! -d downloads ]; then
    mkdir -p downloads
fi

if [ ! -f downloads/$TARBALL ]; then
    wget -nd --no-check-certificate $URL -P downloads
fi

tar xzf downloads/$TARBALL

npm install grunt --save-dev
npm install grunt-contrib-less --save-dev
