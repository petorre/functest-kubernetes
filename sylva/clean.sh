#! /bin/bash

# SPDX-License-Identifier: Apache-2.0

IMAGENAME="127.0.0.1:5000/stack-validation-xtesting"

if [[ -e "image/etc/kubeconfig" ]]; then
    rm -f "image/etc/kubeconfig"
fi

if [[ -e "container-experience-kits/" ]]; then
    rm -rf "container-experience-kits/"
fi

for f in "config.json" "k8s" "requirements.txt" "validate.py"; do
    rm -rf "image/stack-validation/${f}"
done

exit

if [[ " $( docker image ls | grep -c "^${IMAGENAME}" || true ) " -eq 1 ]]; then
    docker rmi -f "${IMAGENAME}"
fi

