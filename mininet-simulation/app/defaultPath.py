#!/usr/bin/env python

from topoDiscovery import *
from monitoringTools import *
import math
from runElasticTree import *


def installDefaultPaths(topo, Ncore, NAgg_p):
    DownPriority = 600
    UpPriority = 5
    k = topo.degree
    density = k/2 # Number of devices in each pod layer
    
    EDGE_DEVICES = topo.EDGE_DEVICES
    AGREGATION_DEVICES = topo.AGGREGATION_DEVICES
    CORE_DEVICES = topo.CORE_DEVICES

    # EDGE LAYER SWITCHES
    for s in range(len(EDGE_DEVICES)):
        edgeSwitchNbinPod = ((s) % density) +1
        sw = EDGE_DEVICES[s]
        podNb = int(math.ceil((s+1)/float(density)))
        subsubNet = "10." + str(podNb) + "." + str(edgeSwitchNbinPod) + "."

        for h in range(1, density+1):
            # Downstream traffic
            host = subsubNet + str(h)
            outPort = topo.hostLocation[host].split("::")[1]
            hostIP = host + "/32"
            postFlowRule_dstIP_outPort(sw, str(hostIP), str(outPort), DownPriority)

            # Upstream Traffic
            host = subsubNet + str(h)
            if (h > NAgg_p[podNb-1]):
                offset = NAgg_p[podNb-1]
            else:
                offset = h
            aggrSwitchID = AGREGATION_DEVICES[(podNb-1)*density + offset-1] 
            outPort = topo.linkPorts[sw + "::" + aggrSwitchID].split("::")[0] 
            hostIP = host + "/32"
            postFlowRule_srcIP_outPort(sw, hostIP, outPort, UpPriority)
    print(">> EDGE LAYER : down and up traffic OK")

    # AGGREGATION LAYER SWITCHES
    c = 0
    for s in range(len(AGREGATION_DEVICES)):
        sw = AGREGATION_DEVICES[s]
        podNb = int(math.ceil((s+1)/float(density)))
        subNet = "10." + str(podNb) + "."

        for i in range(1, density+1): # For each subsubNet in the current pod
            subsubNet = subNet + str(i) + "." # example : 10.1.1.
            subsubNetIP = subsubNet + "0/24" # example : 10.1.1.0/24 

            # Downstream traffic
            edgeSwitchId = topo.hostLocation[subsubNet + "1"].split("::")[0] # Edge Switch ID connected to 10.1.1.0 host network
            outPort = topo.linkPorts[sw + "::" + edgeSwitchId].split("::")[0] # Port between the current Aggr switch and the edge switch required
            postFlowRule_dstIP_outPort(sw, str(subsubNetIP), str(outPort), DownPriority)

            # Upstream traffic
            coreSwicthID = CORE_DEVICES[c]
            outPort = topo.linkPorts[sw + "::" + coreSwicthID].split("::")[0]
            postFlowRule_srcIP_outPort(sw, subsubNetIP, outPort, UpPriority)
            if (c < len(CORE_DEVICES)-1): 
                c += 1
            else:
                c = 0
    print(">> AGGREAGTION LAYER : down and up traffic OK")

    # CORE LAYER SWITCHES (downstream traffic)
    for s in range(Ncore):
        sw = CORE_DEVICES[s]

        offset = 0
        if (s >= k/2):
            offset = 1
        if (s >= k):
            offset = 2
        if (s >= 3*k/2):
            offset = 3
        # print(str(s) + " - " + str(offset))
        for pod in range(1, k+1):
            subNet = "10." + str(pod) + ".0.0/16"
            aggrSwitchID = AGREGATION_DEVICES[(pod-1)*density + offset] # Aggr swicth connected to the current pod
            outPort = topo.linkPorts[sw + "::" + aggrSwitchID].split("::")[0]
            postFlowRule_dstIP_outPort(sw, str(subNet), str(outPort), DownPriority)
    print(">> CORE LAYER : down traffic OK")

if __name__ == "__main__":
    # Initialize Topo Manger, get the latest version of the topology and set default paths
    if (len(sys.argv) != 2):
        print("Usage : python defaultpath.py k")
    else: 
        # Initialize Topo Manger and get the latest version of the topology
        k = int(sys.argv[1]) # Get fat-tree degree from args
        if k==4:
            from deviceList.deviceList_k4 import *
        if k==8:
            from deviceList.deviceList_k8 import *
            
        topo = TopoManager(k, CORE_DEVICES, AGREGATION_DEVICES, EDGE_DEVICES)
        installDefaultPaths(topo, k, [2,2,2,2])