#! /bin/bash

# SPDX-License-Identifier: Apache-2.0

IMAGENAME="127.0.0.1:5000/stack-validation-xtesting"

if [[ -e "image/etc/kubeconfig" ]]; then
    rm -f "image/etc/kubeconfig"
fi

if [[ " $( docker image ls | grep -c "^${IMAGENAME}" || true ) " -eq 1 ]]; then
    docker rmi -f "${IMAGENAME}"
fi

