#! /bin/bash

# SPDX-License-Identifier: Apache-2.0

IMAGENAME="127.0.0.1:5000/stack-validation-xtesting"

if [[ -z "${KUBECONFIG}" ]] && [[ -f ~/.kube/config ]]; then
    KUBECONFIG=~/.kube/config
fi

if [[ ! -e "${KUBECONFIG}" ]]; then
    echo "Error: no KUBECONFIG file"
    exit 1
fi

cp -f "${KUBECONFIG}" "image/etc/kubeconfig"

if [[ ! -e "container-experience-kits" ]]; then
    git clone "https://github.com/petorre/container-experience-kits"
fi

for f in "config.json" "k8s" "requirements.txt" "validate.py"; do
    echo $f
    cp -rf "container-experience-kits/validation/sylva-validation/stack-validation/image/${f}" "image/stack-validation"
done

if [[ " $( docker image ls | grep -c "^${IMAGENAME}" || true ) " -eq 1 ]]; then
    docker rmi -f "${IMAGENAME}"
fi

if [[ -z "${http_proxy+x}" ]] || [[ -z "${https_proxy+x}" ]]; then
    docker build --rm . -t "${IMAGENAME}"
else
    echo -n "Building with http_proxy=${http_proxy} "
    echo "and https_proxy=${https_proxy}"
    docker build --rm . -t "${IMAGENAME}" \
        --build-arg="http_proxy=${http_proxy}" \
        --build-arg="https_proxy=${https_proxy}"
fi
