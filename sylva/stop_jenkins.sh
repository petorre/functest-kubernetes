#! /bin/bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

for i in s3www minio testapi registry mongo jenkins; do
    docker kill "${i}"
    docker rm "${i}"
done

# rm /data/*
