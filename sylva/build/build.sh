#! /bin/bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

source config

docker_rmi_build () {
    dockerfile=$1
    imagename=$2
    if [[ " $( docker image ls | grep -c "^${imagename}" || true ) " \
        -eq 1 ]]; then
        docker rmi -f "${imagename}"
    fi
    if [[ -z "${http_proxy+x}" ]] || [[ -z "${https_proxy+x}" ]]; then
        docker build -f "${dockerfile}" --rm . -t "${imagename}"
    else
        echo -n "Building with http_proxy=${http_proxy} "
        echo "and https_proxy=${https_proxy}"
        docker build -f "${dockerfile}" --rm . -t "${imagename}" \
            --build-arg="http_proxy=${http_proxy}" \
            --build-arg="https_proxy=${https_proxy}"
    fi
}

echo "Building ${IMAGENAME_VALIDATION}"
docker_rmi_build Dockerfile-validation "${IMAGENAME_VALIDATION}"

echo "Building ${IMAGENAME_XTESTING}"
if [[ -z "${KUBECONFIG}" ]] && [[ -f ~/.kube/config ]]; then
    KUBECONFIG=~/.kube/config
fi
if [[ ! -e "${KUBECONFIG}" ]]; then
    echo "Error: no KUBECONFIG file"
    exit 1
fi
cp -f "${KUBECONFIG}" "image/xtesting/etc/kubeconfig"
docker_rmi_build Dockerfile-xtesting "${IMAGENAME_XTESTING}"
