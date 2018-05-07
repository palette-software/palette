#!/usr/bin/env bash
if [[ -z $PALETTE_VERSION ]]; then echo "PALETTE_VERSION environment variable is not set!"; exit 1; fi
if [[ -z $CONTROLLER_VERSION ]]; then echo "CONTROLLER_VERSION environment variable is not set!"; exit 1; fi

pushd app
make setup
popd

pushd akiri.framework
make
popd

make palette
make controller

PACKAGE=palette-${PALETTE_VERSION}
mkdir ${PACKAGE}
find . -name \*.rpm -print0 | xargs -0 cp -t ${PACKAGE}
zip -r ${PACKAGE}.zip ${PACKAGE}
cp -r ${PACKAGE} /project_root
