#!/usr/bin/env bash
pushd app
make setup
popd

pushd akiri.framework
python setup.py bdist_rpm
popd

export PALETTE_VERSION=2.3.4
export CONTROLLER_VERSION=2.3.4

make palette
make controller

PACKAGE=palette-${PALETTE_VERSION}
mkdir ${PACKAGE}
find . -name \*.rpm -print0 | xargs -0 cp -t ${PACKAGE}
zip -r ${PACKAGE}.zip ${PACKAGE}
