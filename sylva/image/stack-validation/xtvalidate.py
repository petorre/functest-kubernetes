#!/bin/python

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import traceback
import time
import validate
from xtesting.core import testcase  # pip install xtesting

class XtestingValidate(testcase.TestCase):
    def run(self, **kwargs):
        #print(kwargs)
        try:
            rj = None  # file to write results in JSON format
            os.makedirs(self.res_dir, exist_ok=True)
            try:
                test = kwargs["test"]  # must have args name for the name of test case
                try:
                    debug = kwargs["debug"]
                except KeyError:
                    debug = False
                try:
                    node = kwargs["node"]
                except KeyError:
                    node = None
                val = validate.Validate(configfile=validate.CONFIGFILE, debug=debug)
                if val.ready:
                    val.run(test=test, node=node)  # None for all nodes
                    self.start_time = val.start_time
                else:
                    self.start_time = time.time()
                rj = open('{}/result.json'.format(self.res_dir), 'w+')
                #json.dump(val.endresj, rj, indent=4, sort_keys=True)
                json.dump(val.endresj, rj, indent=2)
                rj.close()
                try:
                    r = 1
                    for tc in val.endresj["stackValidation"]["testCases"]:
                        #print(tc)
                        for n in tc["nodes"]:
                            if n["pass"] == "false":
                                r = 0
                    self.result = r
                    #self.result = 1
                except KeyError:
                    self.result = 0
                self.stop_time = val.stop_time
            except KeyError:
                error = open('{}/error.txt'.format(self.res_dir), 'w+')  # file to write error message
                error.write(f"Error: no name or nonexistent test case name given in args: {kwargs}")
                error.close()
                if rj != None:
                    rj.close()
                self.result = 0
        except:
            print(f"Error: {traceback.format_exc()}")
            self.result = 0

# main
if __name__ == "__main__":
    XtV = XtestingValidate()
    XtV.res_dir = "res"  # to avoid Permission denied: '/var/lib/xtesting'
    XtV.run(test="validateRT")
    print(XtV.result)
