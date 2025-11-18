#! /bin/bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

# multi
l=$( lscpu --json | jq -r ' .lscpu[] ' )
echo -n "vcpus="
echo "${l}" | jq -r ' select ( ."field" == "CPU(s):" ) | .data '
echo -n "threadspercore="
echo "${l}" | jq -r ' select ( ."field" == "Thread(s) per core:" ) | .data '
echo -n "corespersocket="
echo "${l}" | jq -r ' select ( ."field" == "Core(s) per socket:" ) | .data '
echo -n "sockets="
echo "${l}" | jq -r ' select ( ."field" == "Socket(s):" ) | .data '

cpuinfocpus=` cat /proc/cpuinfo | grep -c ^processor `
allrange=` echo "0-"\` expr $cpuinfocpus - 1 \` `
if [ -e /sys/fs/cgroup/cpuset/cpuset.cpus ]; then
    cpusetcpus=` cat /sys/fs/cgroup/cpuset/cpuset.cpus `
else
    cpusetcpus=` cat /sys/fs/cgroup/cpuset.cpus.effective `
fi
if [ "$cpusetcpus" == "$allrange" ]; then
    cpusetlimited=0
else
    cpusetlimited=1
fi
echo "allrange=${allrange}"
echo "cpusetcpus=${cpusetcpus}"
echo "cpusetlimited=${cpusetlimited}"

lspci | awk ' { print "pcidev= " $0 } '

echo -n "unamerv="
uname -rv
echo -n "syskernelrealtime="
if [[ -e /sys/kernel/realtime ]]; then
    cat /sys/kernel/realtime
else
    echo "-1"
fi
echo -n "proccmdline="
cat /proc/cmdline


# huge
r1=$( cat /proc/sys/vm/nr_hugepages )
echo "nr_hugepages=${r1}"
r2=$( awk ' $1=="HugePages_Free:" { f=$2 } END { print f } ' /proc/meminfo )
echo "meminfo_HugePages_Free=${r2}"
if mount | grep -q /dev/hugepages; then
    r3=$( mount | grep -c /dev/hugepages )
else
    r3=0
fi
echo "mount_dev_hugepages=${r3}"
if [[ "${r1}" -gt 0 ]] && [[ "${r2}" -gt 0 ]] && [[ "${r3}" -eq 1 ]]; then
    echo "hugepages=1"
else
    echo "hugepages=0"
fi

# reserve
ps -ef | awk ' { printf("ps-ef=%s\n",$0); } '

# vCPUs on same frequency
echo -n "cpussamehwfreq="
freqs=$( grep "cpu MHz" /proc/cpuinfo 2>/dev/null | \
    awk -vFS=":" ' { print $2 } ' | sort -u | wc -l )
if [[ "${freqs}" -eq 1 ]]; then
    echo 1
else
    echo 0
fi

# tunedrt
if [[ -e /var/log/tuned/tuned.log ]]; then
    cd /var/log/tuned
    p=$( grep "static tuning from profile" tuned.log | tail -1 )
    if [ $( echo "${p}" | grep -c "realtime" ) -gt 0 ]; then
        echo "tunedlogrealtime=1"
    else
        echo "tunedlogrealtime=0"
    fi
else
    echo "tunedlogrealtime=-1"
fi
echo "tunedlogstatictuning=${p}"

sleep infinity
