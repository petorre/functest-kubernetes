# Xtesting with Stack Validation

## Summary

Integration of Python-based test cases from https://github.com/petorre/container-experience-kits/tree/master/validation/sylva-validation/stack-validation (after upstreaming will be https://github.com/intel/container-experience-kits/tree/master/validation/sylva-validation/stack-validation) into [Xtesting framework](https://github.com/opnfv/functest-xtesting).

## Prerequisites

Local Docker Engine.

Access to Kubernetes cluster.

## Configuration

Set environment variable KUBECONFIG to point to your Kubernetes configuration file that Python Kubernetes library in container will use.

Check [image/etc/xtesting/testcases.yaml](./image/etc/xtesting/testcases.yaml) for test cases. Further test cases configuration details are in [image/stack-validation/config](./image/stack-validation/config.json) (created during build process).

## Building and pushing Docker image

Use script [build.sh](./build.sh) or do similar.

```
./build.sh
```

Start local Docker registry (image repository) with:

```
./registry.sh
```

Use script [push.sh](./push.sh) or do similar.

```
./push.sh
```

## Usage

(Adopted from https://github.com/opnfv/functest-xtesting/blob/master/README.md#make-world)

### Jenkins

Do once:

```
virtualenv xtesting -p python3 --system-site-packages
. xtesting/bin/activate
pip install ansible
ansible-galaxy install collivier.xtesting
ansible-galaxy collection install ansible.posix community.general community.grafana \
    community.kubernetes community.docker community.postgresql
ansible-playbook site.yml
```

and later only:

```
. xtesting/bin/activate
ansible-playbook site.yml
```

### (Optional) CLI without Jenkins

Without previous virtual environment:

```
pip install kubernetes xtesting
cd build/image/xtesting/stack-validation
python xtvalidate.py
```

## Example run

Follow section [Play](https://github.com/opnfv/functest-xtesting/blob/master/README.md#play)

## Stop

```
deactivate
rm -r xtesting
./stop_jenkins.sh
```

Script [stop_jenkins.sh](./stop_jenkins.sh) will docker kill and rm containers s3www minio testapi registry mongo jenkins.

### Deleting namespace

If needed, delete test cases namespace with

```
cd build/image/xtesting/stack-validation
python validate.py --delete-ns
```

## Clean

```
cd build
./clean.sh
```

## Tested on

Currently only validateLinuxDistribution and validateRT test cases were tested on worker nodes that are EC2 VMs, on servers with 4th Gen Intel Xeon Scalable Processors, using these Kubernetes distributions and Linux:

* k3s v1.31.6+k3s1 on Rocky Linux 9.5 with kernel 5.14
