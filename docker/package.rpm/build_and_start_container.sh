#!/usr/bin/env bash

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
    center_package_builder
popd
