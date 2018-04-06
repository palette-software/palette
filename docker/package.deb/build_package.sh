#!/usr/bin/env bash
pushd app
make setup
popd

export PALETTE_VERSION=2.3.4
export CONTROLLER_VERSION=2.3.4

make palette
make controller

cp dependencies/*.deb dpkg/pool/
GNUPGHOME=dpkg/keys reprepro -b dpkg/apt includedeb stable dpkg/pool/*.deb

export PCKG_FILE=palette-${PALETTE_VERSION}.zip
zip -r $PCKG_FILE dpkg/apt
