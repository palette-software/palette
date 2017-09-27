#!/bin/bash
set -e

INSTALLER_DIR=$(dirname $0)
LOCAL_PALETTE_REPO_ROOT="/usr/local"

# Add repo sign key
apt-key add "${INSTALLER_DIR}/key.asc"

# Add system packages local repo
pushd "${LOCAL_PALETTE_REPO_ROOT}"
tar xzf ${INSTALLER_DIR}/palette-trusty-local.tar.gz
echo "deb file://${LOCAL_PALETTE_REPO_ROOT}/palette-trusty-local stable non-free" > /etc/apt/sources.list.d/palette.trusty.local.list
popd

# Install local palette repo
pushd "${LOCAL_PALETTE_REPO_ROOT}"

apt-get update
apt-get install unzip

unzip ${INSTALLER_DIR}/palette-*.zip
echo "deb file://${LOCAL_PALETTE_REPO_ROOT}/dpkg/apt stable non-free" > /etc/apt/sources.list.d/palette.local.list
popd

# Install Center
apt-get update
apt-get install -y --force-yes palette controller
