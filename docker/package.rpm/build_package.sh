#!/usr/bin/env bash
pushd app
make setup
popd

pushd akiri.framework
make
popd

export PALETTE_VERSION=3.4.5
export CONTROLLER_VERSION=3.4.5

make palette
make controller

PACKAGE=palette-${PALETTE_VERSION}
mkdir ${PACKAGE}
find . -name \*.rpm -print0 | xargs -0 cp -t ${PACKAGE}
zip -r ${PACKAGE}.zip ${PACKAGE}
