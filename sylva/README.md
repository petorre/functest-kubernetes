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

Next following section [Play](https://github.com/opnfv/functest-xtesting/blob/master/README.md#play) select "validate" job, click "Build with Parameters", observe how it completes, on the last completed step click on "Console" logo to see if "RESULT" is "SUCCESS" or "FAIL", and link with results.json to see details per test case.

### (Optional) CLI without Jenkins

Without previous virtual environment:

```
pip install kubernetes xtesting
cd build/image/xtesting/stack-validation
python validate.py
```

An example is in:

```
# python validate.py --debug
{
  "stackValidation": {
    "testCases": [
      {
        "name": "validateAnuketProfileLabels",
        "description": "Validate Anuket profile labels",
        "ra2Spec": "ra2.k8s.011",
        "nodes": [
          {
            "name": "node01",
            "result": "true",
            "debug": "anuket.io/profile=network-intensive"
          }
        ]
      },
      {
        "name": "validateLinuxDistribution",
        "description": "Validate Linux distribution for deb/rpm",
        "ra2Spec": "ra2.os.001",
        "nodes": [
          {
            "name": "node01",
            "result": "true",
            "debug": "linux=Ubuntu 22.04.2 LTS"
          }
        ]
      },
      {
        "name": "validateKubernetesAPIs",
        "description": "Validate k8s APIs without alpha+beta or is exception",
        "ra2Spec": "ra2.k8s.012",
        "nodes": [
          {
            "name": "node01",
            "result": "true",
            "debug": "exception=flowcontrol.apiserver.k8s.io/v1beta3"
          }
        ]
      },
      {
        "name": "validateLinuxKernelVersion",
        "description": "Validate Linux kernel version",
        "ra2Spec": "ra2.os.002",
        "nodes": [
          {
            "name": "node01",
            "result": "true",
            "debug": "kernel=5.15.0-1052-realtime"
          }
        ]
      },
      {
        "name": "validateSMT",
        "description": "Validate SMT",
        "ra2Spec": "ra2.ch.004",
        "nodes": [
          {
            "name": "node01",
            "result": "true",
            "debug": "vcpus=128, threadspercore=2, corespersocket=32, sockets=2"
          }
        ]
      },
      {
        "name": "validateHugepages",
        "description": "Validate huge pages",
        "ra2Spec": "ra2.ch.001",
        "nodes": [
          {
            "name": "node01",
            "result": "true",
            "debug": "alloc_2Mi=0, alloc_1Gi=80, nr_hugepages=80, meminfo_hugepages_free=80, mount_dev_hugepages=1, nr_hugepages=0, meminfo_hugepages_free=0, mount_dev_hugepages=0"
          }
        ]
      },
      {
        "name": "validateRT",
        "description": "Validate Real-Time versions and/or configurations in BIOS, kernel and OS services",
        "ra2Spec": "ra2.ch.026",
        "nodes": [
          {
            "name": "node01",
            "debug": "cpussamehwfreq=64; unamerv=5.15.0-1052-realtime #58-Ubuntu SMP PREEMPT_RT Wed Nov 15 20:57:45 UTC 2023; syskernelrealtime=1; proccmdline=BOOT_IMAGE=/vmlinuz-5.15.0-1052-realtime root=/dev/mapper/ubuntu--vg-ubuntu--lv ro intel_iommu=on iommu=pt usbcore.autosuspend=-1 selinux=0 enforcing=0 nmi_watchdog=0 crashkernel=auto softlockup_panic=0 audit=0 intel_pstate=disable mce=off hugepagesz=1G hugepages=80 hugepagesz=2M hugepages=0 default_hugepagesz=1G kthread_cpus=0-4,64-68,32-36,96-100 irqaffinity=0-4,64-68,32-36,96-100 nohz=on skew_tick=1 skew_tick=1 isolcpus=managed_irq,domain,5-31,37-63,69-95,101-127 nohz_full=5-31,37-63,69-95,101-127 rcu_nocbs=5-31,37-63,69-95,101-127 rcu_nocb_poll intel_pstate=disable nosoftlockup tsc=nowatchdog nohz=on; tunedlogstatictuning=2025-02-22 07:42:55,706 INFO     tuned.daemon.daemon: static tuning from profile 'realtime' applied",
            "result": "true"
          }
        ]
      }
    ],
    "timeStamps": {
      "startTime": "Thu Mar 27 17:36:37 UTC 2025",
      "stopTime": "Thu Mar 27 17:36:59 UTC 2025"
    }
  }
}
```

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

All included test cases were tested on servers with 4th Gen Intel Xeon Scalable Processors, using these Kubernetes and Linux distributions:

* k3s v1.31.6+k3s1 on Ubuntu 22.04.2 LTS with kernel 5.15-realtime on premises
* k3s v1.33.5+k3s1 on Ubuntu 24.04.3 LTS with kernel 6.14 on EC2 VM
* k3s v1.31.6+k3s1 on Rocky Linux 9.5 with kernel 5.14 on EC2 VM
