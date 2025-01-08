#!/bin/python

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import sys
import json
from kubernetes import client, config, utils  # pip install kubernetes
import os
import subprocess
import time
import datetime

CONFIGFILE = "config.json"

USAGE = "[--only <testname>] [--debug]"
def usage():
    print(f"ERROR. Usage: python {sys.argv[0]} {USAGE}")
    exit()

ro = None
l = len(sys.argv)
if l == 1:    # no arguments
    DEBUG = False
elif l == 2:  # 1 argument
    if sys.argv[1] == "--debug":
        DEBUG = True
    else:
        usage()
elif l == 3:  # 2 arguments
    if sys.argv[1] == "--only":
        ro = sys.argv[2]
    else:
        usage()
elif l == 4: # 3 arguments
    if sys.argv[1] == "--only":
        ro = sys.argv[2]
        if sys.argv[3] == "--debug":
            DEBUG = True
        else:
            usage()
    elif sys.argv[1] == "--debug":
        DEBUG = True
        if sys.argv[2] == "--only":
            ro = sys.argv[3]
        else:
            usage()
    else:
        usage()
else:
    usage()

f = open(CONFIGFILE)
d = json.load(f)
#for i in d["testCases"]:
#    print(i["name"])

PODPAUSE = d["script"]["podPause"]
DIRECTORY = d["script"]["deployFiles"]["directory"]
NS = d["script"]["podNamespace"]
CPUPOWER = d["script"]["deployFiles"]["cpupower"]["name"]
##KERNELRT = d["script"]["deployFiles"]["kernelrt"]["name"]
MULTI = d["script"]["deployFiles"]["multi"]["name"]
TUNEDRT = d["script"]["deployFiles"]["tunedrt"]["name"]
PTPHWCLOCK = d["script"]["deployFiles"]["ptphwclock"]["name"]
#print(f"{PODPAUSE} {DIRECTORY} {NS}")
#print(f"{CPUPOWER} {KERNELRT} {TUNEDRT} {PTPHWCLOCK}")

config.load_kube_config()
v1 = client.CoreV1Api()
cl = client.ApiClient()

def createNamespace():
    ns_exists = False
    for i in v1.list_namespace().items:
        if i.metadata.name == NS:
            ns_exists = True
    if not ns_exists:
        #utils.create_from_yaml(cl, f"{DIRECTORY}/ns.yaml")
        o=os.popen(f"kubectl create ns {NS}").read()
        time.sleep(1)
        if not f"namespace/{NS} created" in o:
            print(f"ERROR: {o}")
            exit()

def deleteNamespace():
    o=os.popen(f"kubectl delete ns {NS}").read()
    if not f'namespace "{NS}" deleted' in o:
        print(f"ERROR: {o}")
        exit()

def checkEmptyNamespace():
    global resj
    r = v1.list_pod_for_all_namespaces(watch=False)
    for i in r.items:
        if i.metadata.namespace == NS:
            resj["error"] = f"There are already pods running in namespace {NS}. Manually delete them."
            return False
    return True

def createDaemonset(name, with_sleep):
    utils.create_from_yaml(cl, f"{DIRECTORY}/{name}.yaml")
    if with_sleep:
        time.sleep(PODPAUSE)
    #now = time.time()
    #while True:
    #    some_dont_run = False
    #    r = v1.list_pod_for_all_namespaces(watch=False)
    #    for i in r.items:
    #        if i.metadata.namespace == NS and i.metadata.name.startswith("test-ptphwclock-"):
    #            if i.status.phase != "Running":
    #                some_dont_run = True
    #    if not some_dont_run or time.time() - now > PODPAUSE:
    #        break
    #    time.sleep(1)

def deleteDaemonset(name):
    #o=os.popen(f"kubectl delete -f {DIRECTORY}/{name}.yaml &").read()
    #os.popen(f"kubectl delete -f {DIRECTORY}/{name}.yaml")
    x = subprocess.Popen(["kubectl", "delete", "-f", f"{DIRECTORY}/{name}.yaml"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # doesn't wait

def addBegin(name):  # returns testcase node in result JSON
    global resj
    showDescription=d["script"]["show"]["description"]
    for tc in d["testCases"]:
        if tc["name"] == name:
            description = tc["description"]
            ra2Spec = tc["ra2Spec"]
    showRa2Spec = d["script"]["show"]["ra2Spec"]
    tcjn = {"name": f"{name}"}  # testcase JSON node
    resj["testCases"].append(tcjn)
    if showDescription:
        tcjn["description"] = f"{description}"
    if showRa2Spec:
        tcjn["ra2Spec"] = f"{ra2Spec}"
    return tcjn

def validateRT():
    name = "validateRT"
    tcjn = addBegin(name)  # testcase JSON node
    tcjn["nodes"] = []
    for tc in d["testCases"]:
        if tc["name"] == name:
            kernelNames = tc["kernelNames"]
            preemptName = tc["preemptName"]
    pods = v1.list_pod_for_all_namespaces(watch=False)
    res_cpupower = False
    res_kernelrt = False
    res_tunedrt = False
    for ln in NODES:
        n = ln.metadata.name
        cwn = {"name": f"{n}"}
        tcjn["nodes"].append(cwn)  # current worker node
        node_with_cpupower_pod = False
        node_with_multi_pod = False  # for kernelrt
        node_with_tunedrt_pod = False
        for p in pods.items:
            if p.metadata.namespace == NS and p.metadata.name.startswith(f"test-{CPUPOWER}-"):
                node_with_cpupower_pod = True
                log = v1.read_namespaced_pod_log(namespace=NS, name=p.metadata.name)
                shf = False  # cpupower frequency-info | grep "CPUs which run at the same hardware frequency"
                debug_cpupower = ""
                for l in log.split("\n"):
                    if "cpussamehwfreq=" in l:
                        if f'NotAvailable' in l:
                            shf = False
                        else:
                            shf = True
                        debug_cpupower = l
                res_cpupower = shf
            if p.metadata.namespace == NS and p.metadata.name.startswith(f"test-{MULTI}-"):
                node_with_multi_pod = True
                log = v1.read_namespaced_pod_log(namespace=NS, name=p.metadata.name)
                knr = False  # kernel with -rt, -realtime
                per = False  # PREEMPT_RT
                skr = False  # /sys/kernel/realtime
                pcr = False  # /proc/cmdline with BOOT_IMAGE=*/*-realtime
                debug_kernelrt = ""
                for l in log.split("\n"):
                    if "unamerv=" in l:
                        for kn in kernelNames:
                            if f'-{kn["name"]}' in l:
                                rkn = True
                        if f" {preemptName} " in l:
                            per = True
                        debug_kernelrt = l
                    if "syskernelrealtime=" in l:
                        x, l2 = l.split("syskernelrealtime=", 1)
                        if l2 == "1":
                            skr = True
                        debug_kernelrt += "; " + l
                    if l.startswith("proccmdline="):
                        x, l2 = l.split("proccmdline=", 1)
                        for w in l2.split(" "):
                            if w.startswith("BOOT_IMAGE="):
                                for kn in kernelNames:
                                    if f'-{kn["name"]}' in l:
                                        pcr = True
                        debug_kernelrt += "; " + l
                res_kernelrt = knr and per and skr and pcr
            if p.metadata.namespace == NS and p.metadata.name.startswith(f"test-{TUNEDRT}-") and p.status.phase == "Running":
                node_with_tunedrt_pod = True
                log = v1.read_namespaced_pod_log(namespace=NS, name=p.metadata.name)
                trt = False  # grep "static tuning from profile" /var/log/tuned/tuned.log | tail -1 | grep -c realtime
                for l in log.split("\n"):
                    if "tunedlogrealtime=" in l:
                        x, l2 = l.split("tunedlogrealtime=", 1)
                        if l2 == "1":
                            trt = True
                    if "tunedlogstatictuning=" in l:
                        debug_tunedrt = l
                res_cpupower = shf
        if node_with_cpupower_pod and node_with_multi_pod:  # node_with_tunedrt_pod won't schedule if it cannot mount tuned log file, but still show debug for cpupower and kernelrt
            if DEBUG:
                cwn["debug"] = f"{debug_cpupower}; {debug_kernelrt}"
        if node_with_cpupower_pod and node_with_multi_pod and node_with_tunedrt_pod:
            res = res_cpupower and res_kernelrt and res_tunedrt
            cwn["pass"] = str(res).lower()
            if DEBUG:
                cwn["debug"] = f"{debug_cpupower}; {debug_kernelrt}; {debug_tunedrt}"
        else:
            cwn["pass"] = "false"
            e = "Cannot find pods "
            if not node_with_cpupower_pod:
                e += f"test-{CPUPOWER} "
            if not node_with_multi_pod:
                e += f"test-{MULTI} "
            if not node_with_tunedrt_pod:
                e += f"test-{TUNEDRT}"
            cwn["error"] = e

def validateTSN():
    name = "validateTSN"
    tcjn = addBegin(name)
    tcjn["nodes"] = []
    for tc in d["testCases"]:
        if tc["name"] == name:
            kernelNames = tc["dev"]
    pods = v1.list_pod_for_all_namespaces(watch=False)
    res_ptphwclock = False
    for ln in NODES:
        n = ln.metadata.name
        cwn = {"name": f"{n}"}
        tcjn["nodes"].append(cwn)  # current worker node
        node_with_ptphwclock_pod = False
        for p in pods.items:
            if p.metadata.namespace == NS and p.metadata.name.startswith(f"test-{PTPHWCLOCK}-"):
                node_with_ptphwclock_pod = True
                log = v1.read_namespaced_pod_log(namespace=NS, name=p.metadata.name)
                phc = False  # ethtool -T eth0 | grep PTP
                debug_ptphwclock = ""
                for l in log.split("\n"):
                    if "ptphwclock=" in l:
                        if f'none' in l:
                            shf = False
                        else:
                            shf = True
                        debug_ptphwclock = l
                res_ptphwclock = phc
        if node_with_ptphwclock_pod:
            res = res_ptphwclock
            cwn["pass"] = str(res).lower()
            if DEBUG:
                cwn["debug"] = debug_ptphwclock
        else:
            cwn["pass"] = "false"
            cwn["error"] = f"Cannot find pod test-{PTPHWCLOCK}"


# main

NODES = v1.list_node().items

endresj = {}  # Dictionary to hold result that will at the end be printed as JSON
resj = endresj["stackValidation"] = {}

startTime = time.time()

if ro == None:
    createNamespace()
    if checkEmptyNamespace():
        createDaemonset(CPUPOWER, True)
        createDaemonset(MULTI, True)  # for kernel RT
        createDaemonset(TUNEDRT, True)
        createDaemonset(PTPHWCLOCK, True)
        resj["testCases"] = []
        validateRT()
        #validateTSN()
        deleteDaemonset(CPUPOWER)
        deleteDaemonset(MULTI)
        deleteDaemonset(TUNEDRT)
        #deleteDaemonset(PTPHWCLOCK)
        deleteNamespace()
elif ro == "validateRT":
    createNamespace()
    if checkEmptyNamespace():
        createDaemonset(CPUPOWER, True)
        createDaemonset(MULTI, True)  # for kernel RT
        createDaemonset(TUNEDRT, True)
        resj["testCases"] = []
        validateRT()
        deleteDaemonset(CPUPOWER)
        deleteDaemonset(MULTI)
        deleteDaemonset(TUNEDRT)
        deleteNamespace()
elif ro == "validateTSN":
    resj["error"] = f"Current testcase validateTSN doesn't work with virtual networking."
    #createNamespace()
    #checkEmptyNamespace()
    #createDaemonset(PTPHWCLOCK, True)
    #resj["testCases"] = []
    #validateTSN()
    #deleteDaemonset(PTPHWCLOCK)
    #deleteNamespace()
elif ro == "validateHugepages" or ro == "validateSMT" or ro == "validatePhysicalStorage" or ro == "validateStorageQuantity" or ro == "validateVcpuQuantity" or ro == "validateNFD" or ro == "validateSystemResourceReservation" or ro == "validateCPUPinning" or ro == "validateLinuxDistribution" or ro == "validateKubernetesAPIs" or ro == "validateLinuxKernelVersion" or ro == "validateAnuketProfileLabels" or ro == "validateSecurityGroups":
    resj["error"] = f"Testcase {ro} not implemented yet in validate.py. Try validate.sh instead."
else:
    resj["error"] = f"Cannot find testcase {ro}."

def time2datetime(t):  # from float to "Mon Dec  2 20:17:31 UTC 2024"
    dt = datetime.datetime.fromtimestamp(t, tz=datetime.UTC).ctime()
    return f"{dt[:-4]}UTC {dt[-4:]}"

showTimeStamps = d["script"]["show"]["timeStamps"]
if showTimeStamps:
    resj["timeStamps"] = {}
    resj["timeStamps"]["startTime"] = f"{time2datetime(startTime)}"
    stopTime = time.time()
    resj["timeStamps"]["stopTime"] = f"{time2datetime(stopTime)}"

print(json.dumps(endresj, indent=2))
