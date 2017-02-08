#!/usr/bin/env bash

# Move to project root
pushd $(dirname $0)/../..
docker build -t center_package_builder -f docker/package/Dockerfile .
docker run -h builder -it --rm -v $(pwd):/project_root center_package_builder
popd
