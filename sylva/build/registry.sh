#! /bin/bash -v

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

docker run -d -p 5000:5000 --name registry registry:2.7
