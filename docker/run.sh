#!/bin/bash

docker run -it --rm \
    -p="9443:443" \
    -p="45432:5432" \
    -p="5888:888" \
    -P \
    -v $PWD/app:/opt/palette \
    -v $PWD/app/palette:/usr/lib/python2.7/dist-packages/palette \
    -v $PWD/controller/controller:/usr/lib/python2.7/dist-packages/controller \
    -v $PWD/app/js:/var/www/js \
    -v $PWD/app/css:/var/www/css \
    palette-center \
    /bin/bash
