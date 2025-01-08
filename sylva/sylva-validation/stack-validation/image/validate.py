#!/bin/python

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from kubernetes import client, config, utils  # pip install kubernetes
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
import time
import traceback

CONFIGFILE = "config.json"

class Validate:

    def __init__(self, configfile, debug):
        try:
            self.debug = debug
            f = open(configfile)
            self.d = json.load(f)
            #for i in self.d["testCases"]:
            #    print(i["name"])
            self.PODPAUSE = self.d["script"]["podPause"]
            self.DIRECTORY = self.d["script"]["deployFiles"]["directory"]
            self.NS = self.d["script"]["podNamespace"]
            self.CPUPOWER = self.d["script"]["deployFiles"]["cpupower"]["name"]
            self.MULTI = self.d["script"]["deployFiles"]["multi"]["name"]
            self.TUNEDRT = self.d["script"]["deployFiles"]["tunedrt"]["name"]
            #self.PTPHWCLOCK = self.d["script"]["deployFiles"]["ptphwclock"]["name"]
            #print(f"{self.PODPAUSE} {self.DIRECTORY} {self.NS}")
            #print(f"{self.CPUPOWER} {self.KERNELRT} {self.TUNEDRT} {self.PTPHWCLOCK}")
            self.SHOWTIMESTAMPS = self.d["script"]["show"]["timeStamps"]
            self.SHOWDESCRIPTION = self.d["script"]["show"]["description"]
            self.SHOWRA2SPEC = self.d["script"]["show"]["ra2Spec"]

            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.cl = client.ApiClient()
            n = []
            for ln in self.v1.list_node().items:
                n.append(ln.metadata.name)
            self.NODES = n
            self.ready = True
        except:
            self.ready = False
            self.resj["error"] = f"Initialization error: {traceback.format_exc()}"

    def run(self, test, label, node):  # test = run only that one test case, or None to run all;  label = test only labeled nodes, or None to test all;  node = test only one worker node, or None to test all
        if not self.ready:
            return
        self.start_time = time.time()
        #
        # implement logic to check that minimum of 1 worker node has given label
        #
        try:
            if node != None:
                self.NODES.index(node)
        except ValueError:
            self.resj["error"] = f"Cannot find node {node}."
            self.stop_time = time.time()
            return
        self.node = node
        if test == None:
            self.createNamespace()
            if self.checkEmptyNamespace():
                self.createDaemonset(self.CPUPOWER, False)
                self.createDaemonset(self.MULTI, False)  # for kernel RT
                self.createDaemonset(self.TUNEDRT, True)
                #self.createDaemonset(self.PTPHWCLOCK, True)
                self.resj["testCases"] = []
                self.validateRT()
                #self.validateTSN()
                self.deleteDaemonset(self.CPUPOWER)
                self.deleteDaemonset(self.MULTI)
                self.deleteDaemonset(self.TUNEDRT)
                #self.deleteDaemonset(self.PTPHWCLOCK)
                self.deleteNamespace()
        elif test == "validateRT":
            self.createNamespace()
            if self.checkEmptyNamespace():
                self.createDaemonset(self.CPUPOWER, False)
                self.createDaemonset(self.MULTI, False)  # for kernel RT
                self.createDaemonset(self.TUNEDRT, True)
                self.resj["testCases"] = []
                self.validateRT()
                self.deleteDaemonset(self.CPUPOWER)
                self.deleteDaemonset(self.MULTI)
                self.deleteDaemonset(self.TUNEDRT)
                self.deleteNamespace()
        elif test == "validateTSN":
            self.resj["error"] = f"Current testcase validateTSN doesn't work with virtual networking."
            #self.createNamespace()
            #self.checkEmptyNamespace()
            #self.createDaemonset(self.PTPHWCLOCK, True)
            #self.resj["testCases"] = []
            #self.validateTSN()
            #self.deleteDaemonset(self.PTPHWCLOCK)
            #self.deleteNamespace()
        elif test == "validateHugepages" or test == "validateSMT" or test == "validatePhysicalStorage" or test == "validateStorageQuantity" or test == "validateVcpuQuantity" or test == "validateNFD" or test == "validateSystemResourceReservation" or test == "validateCPUPinning" or test == "validateLinuxDistribution" or test == "validateKubernetesAPIs" or test == "validateLinuxKernelVersion" or test == "validateAnuketProfileLabels" or test == "validateSecurityGroups":
            self.resj["error"] = f"Testcase {test} not implemented yet in validate.py. Try validate.sh instead."
        else:
            self.resj["error"] = f"Cannot find testcase {test}."

        def time2datetime(t):  # from float to "Mon Dec  2 20:17:31 UTC 2024"
            #dt = datetime.datetime.fromtimestamp(t, tz=datetime.UTC).ctime()
            dt = datetime.now(timezone.utc).ctime()
            return f"{dt[:-4]}UTC {dt[-4:]}"

        self.stop_time = time.time()
        if self.SHOWTIMESTAMPS:
            self.resj["timeStamps"] = {}
            self.resj["timeStamps"]["startTime"] = f"{time2datetime(self.start_time)}"
            self.resj["timeStamps"]["stopTime"] = f"{time2datetime(self.stop_time)}"

    def createNamespace(self):
        ns_exists = False
        for i in self.v1.list_namespace().items:
            if i.metadata.name == self.NS:
                ns_exists = True
        if not ns_exists:
            #utils.create_from_yaml(cl, f"{DIRECTORY}/ns.yaml")
            o=os.popen(f"kubectl create ns {self.NS}").read()
            time.sleep(1)
            if not f"namespace/{self.NS} created" in o:
                print(f"ERROR: {o}")
                exit()

    def deleteNamespace(self):
        o = os.popen(f"kubectl delete ns {self.NS}").read()
        if not f'namespace "{self.NS}" deleted' in o:
            print(f"ERROR: {o}")
            exit()

    def checkEmptyNamespace(self):
        r = self.v1.list_pod_for_all_namespaces(watch=False)
        for i in r.items:
            if i.metadata.namespace == self.NS:
                self.resj["error"] = f"There are pods already running in namespace {self.NS}. Wait after previous test, or manually delete them (like with kubectl delete ns {self.NS})."
                return False
        return True

    def createDaemonset(self, name, with_sleep):
        utils.create_from_yaml(self.cl, f"{self.DIRECTORY}/{name}.yaml")
        if with_sleep:
            time.sleep(self.PODPAUSE)
        #now = time.time()
        #while True:
        #    some_dont_run = False
        #    r = self.v1.list_pod_for_all_namespaces(watch=False)
        #    for i in r.items:
        #        if i.metadata.namespace == NS and i.metadata.name.startswith("test-ptphwclock-"):
        #            if i.status.phase != "Running":
        #                some_dont_run = True
        #    if not some_dont_run or time.time() - now > self.PODPAUSE:
        #        break
        #    time.sleep(1)

    def deleteDaemonset(self, name):
        #o=os.popen(f"kubectl delete -f {DIRECTORY}/{name}.yaml &").read()
        #os.popen(f"kubectl delete -f {DIRECTORY}/{name}.yaml")
        x = subprocess.Popen(["kubectl", "delete", "-f", f"{self.DIRECTORY}/{name}.yaml"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # doesn't wait

    def addBegin(self, name):  # returns testcase node in result JSON
        for tc in self.d["testCases"]:
            if tc["name"] == name:
                description = tc["description"]
                ra2Spec = tc["ra2Spec"]
        tcjn = {"name": f"{name}"}  # testcase JSON node
        self.resj["testCases"].append(tcjn)
        if self.SHOWDESCRIPTION:
            tcjn["description"] = f"{description}"
        if self.SHOWRA2SPEC:
            tcjn["ra2Spec"] = f"{ra2Spec}"
        return tcjn

    def validateRT(self):
        name = "validateRT"
        tcjn = self.addBegin(name)  # testcase JSON node
        tcjn["nodes"] = []
        for tc in self.d["testCases"]:
            if tc["name"] == name:
                kernelNames = tc["kernelNames"]
                preemptName = tc["preemptName"]
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        res_cpupower = False
        res_kernelrt = False
        res_tunedrt = False
        for n in self.NODES:
            if self.node != None and self.node != n:  # if single node to test is set, then skip other nodes
                continue
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            node_with_cpupower_pod = False
            node_with_multi_pod = False  # for kernelrt
            node_with_tunedrt_pod = False
            for p in pods.items:
                if p.metadata.namespace == self.NS and p.metadata.name.startswith(f"test-{self.CPUPOWER}-"):
                    node_with_cpupower_pod = True
                    log = self.v1.read_namespaced_pod_log(namespace=self.NS, name=p.metadata.name)
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
                if p.metadata.namespace == self.NS and p.metadata.name.startswith(f"test-{self.MULTI}-"):
                    node_with_multi_pod = True
                    log = self.v1.read_namespaced_pod_log(namespace=self.NS, name=p.metadata.name)
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
                if p.metadata.namespace == self.NS and p.metadata.name.startswith(f"test-{self.TUNEDRT}-") and p.status.phase == "Running":
                    node_with_tunedrt_pod = True
                    log = self.v1.read_namespaced_pod_log(namespace=self.NS, name=p.metadata.name)
                    trt = False  # grep "static tuning from profile" /var/log/tuned/tuned.log | tail -1 | grep -c realtime
                    for l in log.split("\n"):
                        if "tunedlogrealtime=" in l:
                            x, l2 = l.split("tunedlogrealtime=", 1)
                            if l2 == "1":
                                trt = True
                        if "tunedlogstatictuning=" in l:
                            debug_tunedrt = l
                    res_tunedrt = trt
            if node_with_cpupower_pod and node_with_multi_pod:  # node_with_tunedrt_pod won't schedule if it cannot mount tuned log file, but still show debug for cpupower and kernelrt
                if self.debug:
                    cwn["debug"] = f"{debug_cpupower}; {debug_kernelrt}"
            if node_with_cpupower_pod and node_with_multi_pod and node_with_tunedrt_pod:
                res = res_cpupower and res_kernelrt and res_tunedrt
                cwn["pass"] = str(res).lower()
                if self.debug:
                    cwn["debug"] = f"{debug_cpupower}; {debug_kernelrt}; {debug_tunedrt}"
            else:
                cwn["pass"] = "false"
                e = "Cannot find pods "
                if not node_with_cpupower_pod:
                    e += f"test-{self.CPUPOWER} "
                if not node_with_multi_pod:
                    e += f"test-{self.MULTI} "
                if not node_with_tunedrt_pod:
                    e += f"test-{self.TUNEDRT}"
                cwn["error"] = e

    def validateTSN(self):
        name = "validateTSN"
        tcjn = self.addBegin(name)
        tcjn["nodes"] = []
        for tc in self.d["testCases"]:
            if tc["name"] == name:
                kernelNames = tc["dev"]
        pods = self.v1.list_pod_for_all_namespaces(watch=False)
        res_ptphwclock = False
        for n in self.NODES:
            if self.node != None and self.node != n:  # if single node to test is set, then skip other nodes
                continue
            cwn = {"name": f"{n}"}
            tcjn["nodes"].append(cwn)  # current worker node
            node_with_ptphwclock_pod = False
            for p in pods.items:
                if p.metadata.namespace == self.NS and p.metadata.name.startswith(f"test-{PTPHWCLOCK}-"):
                    node_with_ptphwclock_pod = True
                    log = self.v1.read_namespaced_pod_log(namespace=self.NS, name=p.metadata.name)
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
                if self.DEBUG:
                    cwn["debug"] = debug_ptphwclock
            else:
                cwn["pass"] = "false"
                cwn["error"] = f"Cannot find pod test-{self.PTPHWCLOCK}"

    endresj = {}  # Dictionary to hold result that will at the end be printed as JSON
    resj = endresj["stackValidation"] = {}

# main
if __name__ == "__main__":
    def usage():
        USAGE = "[--debug] [--config=configfilename] [--test=testName] [--node=workernodename]"
        print(f"ERROR. Usage: python {sys.argv[0]} {USAGE}")
        exit()
    configfile = CONFIGFILE
    debug = False
    test = None  # if only single test case should be run
    label = None  # if only labeled nodes should be tested
    node = None  # if only single node should be tested
    for a in sys.argv[1:]:
        b = a.split("=")
        if b[0] == "--debug":
            debug = True
        elif b[0] == "--config":
            configfile = b[1]
        elif b[0] == "--test":
            test = b[1]
        #elif b[0] == "--label":
        #    label = b[1]
        elif b[0] == "--node":
            node = b[1]
        else:
            usage()
    val = Validate(configfile, debug)
    if val.ready:
        val.run(test, label, node)
    print(json.dumps(val.endresj, indent=2))
