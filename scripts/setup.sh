#!/bin/bash

set -x
set -e

FA_VERSION=4.7.0
FA_ZIP=font-awesome-$FA_VERSION.zip
FA_URL=https://fontawesome.com/v${FA_VERSION}/assets/$FA_ZIP

if [ ! -d downloads ]; then
    mkdir -p downloads
fi

if [ ! -f downloads/$FA_ZIP ]; then
    wget -nd --no-check-certificate $FA_URL -P downloads
fi

unzip -o downloads/$FA_ZIP

npm install
npm install -g bower
bower install
gulp

cp -f font-awesome-$FA_VERSION/fonts/* fonts/
