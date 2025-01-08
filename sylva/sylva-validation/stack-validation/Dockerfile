# Copyright (C) 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM alpine:3.20

ENV DIR=/stack-validation
COPY image/ "${DIR}"

RUN apk update && \
    apk add --no-cache bash jq wget python3 py3-pip mesa-gl && \
    pip install --no-cache-dir --break-system-packages -r "${DIR}/requirements.txt"
WORKDIR /bin
RUN ln -s /usr/bin/python
WORKDIR /usr/local/bin
RUN wget -q "https://dl.k8s.io/release/$( wget -qO - \
        https://dl.k8s.io/release/stable.txt )/bin/linux/amd64/kubectl" && \
    chmod 755 kubectl

WORKDIR "${DIR}"
ENV USER=validation
ENV UID=65432
ENV GID=65432
ENV KUBECONFIG="${DIR}/kubeconfig"
RUN addgroup --gid "${GID}" "${USER}" && \
    adduser --disabled-password --gecos "" --home "${DIR}" --ingroup \
        "${USER}" --no-create-home --uid "${UID}" -s /bin/bash "${USER}" && \
    chown -R "${USER}:${USER}" "${DIR}"
USER validation

HEALTHCHECK NONE
