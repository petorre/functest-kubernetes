# Xtesting with Stack Validation

## Summary

Integration of Python-based test cases from https://github.com/petorre/container-experience-kits/tree/master/validation/sylva-validation/stack-validation (after upstreaming will be https://github.com/intel/container-experience-kits/tree/master/validation/sylva-validation/stack-validation) into [Xtesting framework](https://github.com/opnfv/functest-xtesting).

## Configuration

Set environment variable KUBECONFIG to point to your Kubernetes configuration file that Python Kubernetes library in container will use.

Check [image/etc/xtesting/testcases.yaml](./image/etc/xtesting/testcases.yaml) for test cases. Further test cases configuration details are in [image/stack-validation/config](./image/stack-validation/config.json) (created during build process).

## Building and pushing Docker image

Use script [build.sh](./build.sh) or do similar.

```
./build.sh
```

Use script [push.sh](./push.sh) or do similar.

```
./push.sh
```

## Usage

(Adopted from https://github.com/opnfv/functest-xtesting/blob/master/README.md#make-world)

### Jenkins

```
virtualenv xtesting -p python3 --system-site-packages
. xtesting/bin/activate
pip install ansible
ansible-galaxy install collivier.xtesting
ansible-galaxy collection install ansible.posix community.general community.grafana \
    community.kubernetes community.docker community.postgresql
ansible-playbook site.yml
```

### (Optional) CLI without Jenkins

```
virtualenv xtesting -p python3 --system-site-packages
. xtesting/bin/activate
cd image/stack-validation
python xtvalidate.py
```

## Example run

Follow section [Play](https://github.com/opnfv/functest-xtesting/blob/master/README.md#play)

## Stop

```
deactivate
rm -r xtesting
```

Kill running Docker containers opnfv/xtesting-s3www, minio/minio, opnfv/testapi, registry, mongo, opnfv/xtesting-jenkins.

### Manually deleting pods

If needed, manually delete stack-validation pods with

```
kubectl delete -f image/stack-validation/k8s/ns.yaml
```

## Clean

```
./clean.sh
```

## Tested on

Currently only validateRT test cases was tested on worker nodes that are EC2 VMs, on servers with Intel Xeon Scalable Processors, using these Kubernetes distributions and Linux:

* k3s v1.29.5+k3s1 on CentOS 9 Stream
