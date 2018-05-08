#!/usr/bin/env bash

# Echo commands
set -x

if [[ -z $PALETTE_VERSION ]]; then echo "PALETTE_VERSION environment variable is not set!"; exit 1; fi
if [[ -z $CONTROLLER_VERSION ]]; then echo "CONTROLLER_VERSION environment variable is not set!"; exit 1; fi

pushd app
make setup || exit 1
popd

pushd akiri.framework
make || exit 1
popd

make palette || exit 1
make controller || exit 1

PACKAGE=palette-"${PALETTE_VERSION}"
PACKAGE_REPO_DIR="${PACKAGE}/noarch"
rm -rf ${PACKAGE} || exit 1
mkdir -p ${PACKAGE_REPO_DIR} || exit 1
find . -name \*.rpm -print0 | xargs -0 cp -t ${PACKAGE_REPO_DIR}
zip -r ${PACKAGE}.zip ${PACKAGE} || exit 1
cp -r ${PACKAGE} /project_root || exit 1
