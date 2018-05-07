#!/usr/bin/env bash

# Stop on first error
set -e

# Move to project root
DIRNAME=$(dirname $0)
pushd ${DIRNAME}/../..
docker build -t center_package_builder -f ${DIRNAME}/Dockerfile .
docker run \
    --hostname builder \
    --env PALETTE_VERSION \
    --env CONTROLLER_VERSION \
    --rm \
    --volume $(pwd):/project_root \
    center_package_builder docker/package.rpm/build_package.sh
popd
