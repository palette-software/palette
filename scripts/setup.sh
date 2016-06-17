#!/bin/bash

set -x
set -e

BS_VERSION=3.3.5
BS_TARBALL=v$BS_VERSION.tar.gz
BS_URL=https://github.com/twbs/bootstrap/archive/$BS_TARBALL

FA_VERSION=4.6.3
FA_ZIP=font-awesome-$FA_VERSION.zip
FA_URL=http://fontawesome.io/assets/$FA_ZIP


if [ ! -d downloads ]; then
    mkdir -p downloads
fi

if [ ! -f downloads/$BS_TARBALL ]; then
    wget -nd --no-check-certificate $BS_URL -P downloads
fi

if [ ! -f downloads/$FA_ZIP ]; then
    wget -nd --no-check-certificate $FA_URL -P downloads
fi

tar xzf downloads/$BS_TARBALL
unzip -o downloads/$FA_ZIP

cp -f bootstrap-$BS_VERSION/dist/js/bootstrap.js js/vendor/
cp -f bootstrap-$BS_VERSION/dist/js/bootstrap.min.js js/vendor/
cp -f font-awesome-$FA_VERSION/fonts/* fonts/

npm install grunt --save-dev
npm install grunt-contrib-less --save-dev
