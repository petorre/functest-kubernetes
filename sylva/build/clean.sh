#! /bin/bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

source config

docker_rmi () {
    imagename=$1
    for i in $( docker image ls | \
        awk -vI="${imagename}" ' $1==I { print $3 } ' ); do
        docker rmi -f "${i}"
    done
}

if [[ -e "image/xtesting/etc/kubeconfig" ]]; then
    rm -f "image/xtesting/etc/kubeconfig"
fi

docker_rmi "${IMAGENAME}"
