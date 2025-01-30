#! /bin/bash

for i in s3www minio testapi registry mongo jenkins; do
    docker kill "${i}"
    docker rm "${i}"
done

