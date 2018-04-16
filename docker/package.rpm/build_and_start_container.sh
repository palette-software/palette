#!/usr/bin/env bash

# Move to project root
DIRNAME=$(dirname $0)
pushd ${DIRNAME}/../..
docker build -t center_package_builder -f ${DIRNAME}/Dockerfile .
docker run -h builder -it --rm -v $(pwd):/project_root center_package_builder
popd
