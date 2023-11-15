#
# Copyright (C) 2017-2023 Tactical Computing Laboratories, LLC
# All Rights Reserved
# contact@tactcomplabs.com
#
# See LICENSE in the top level directory for licensing details
#
# rev-test-ex3.py
#



#
# RevCPU --- memHierarchy.standardInterface --> MemH.L1$ ---> Merlin.hr_router (just to connect L1$ to bridge) ---> Merlin.Bridge ---> Merlin.hr_router (Modeling wider network) ---> MemH.DC ---> MemH.mem
#
#

import os
import sst

numcpus  = 2
numprocs = 2
numharts = 2

DEBUG = 1
DEBUG_LEVEL = 10
VERBOSE = 16
MEM_SIZE = 1024*1024*1024

# Define SST core options
sst.setProgramOption("timebase", "1ps")

# Tell SST what statistics handling we want
sst.setStatisticLoadLevel(10)

max_addr_gb = 1

# set the network params
verb_params = { "verbose" : 6 }

# Define the simulation components

# Setup Network
network = sst.Component("network_rtr", "merlin.hr_router")
network.setSubComponent("topology", "merlin.singlerouter")
network.addParams({
    "xbar_bw" : "1GB/s",
    "flit_size" : "32B",
    "num_ports" : str(1+numcpus),
    "input_buf_size" : "512B",
    "output_buf_size" : "512B",
    "link_bw" : "1GB/s",
    "id" : 0 })

# Setup CPUs
for cid in range(numcpus):
    comp_cpu = sst.Component("cpu"+str(cid), "revcpu.RevCPU")
    comp_cpu.addParams({
            "verbose" : 6,                                # Verbosity
            "numCores" : numprocs,                        # Number of processors per core
	    "numHarts" : numharts,                        # Number of harts per processor
    	    "clock" : "1.0GHz",                           # Clock
            "memSize" : MEM_SIZE,                         # Memory size in bytes
            "machine" : "[CORES:RV64IMAFD]",                  # Core:Config; RV32I for core 0
            "startAddr" : "[0:0x100b0]",                  # Starting address for core 0
            "memCost" : "[0:1:10]",                       # Memory loads required 1-10 cycles
            "program" : os.getenv("REV_EXE", "ex3.exe"),  # Target executable
            "enable_memH" : 1,                            # Enable memHierarchy support
            "splash" : 1                                  # Display the splash message
    })

    # Create the RevMemCtrl subcomponent
    comp_lsq = comp_cpu.setSubComponent("memory", "revcpu.RevBasicMemCtrl");
    comp_lsq.addParams({
          "verbose"         : "5",
          "clock"           : "2.0Ghz",
          "max_loads"       : 16,
          "max_stores"      : 16,
          "max_flush"       : 16,
          "max_llsc"        : 16,
          "max_readlock"    : 16,
          "max_writeunlock" : 16,
          "max_custom"      : 16,
          "ops_per_cycle"   : 16
    })
    comp_lsq.enableAllStatistics({"type":"sst.AccumulatorStatistic"})

    memiface = comp_lsq.setSubComponent("memIface", "memHierarchy.standardInterface")
    memiface.addParams({
          "verbose" : VERBOSE,
          "input_buf_size" : "512B",
          "output_buf_size" : "512B",
          "link_bw" : "1GB/s"
    })

    l1cache = sst.Component("cpu"+str(cid)+"_l1cache", "memHierarchy.Cache")
    l1cache.addParams({
        "access_latency_cycles" : "4",
        "cache_frequency" : "2 Ghz",
        "replacement_policy" : "lru",
        "coherence_protocol" : "MESI",
        "associativity" : "4",
        "cache_line_size" : "64",
        "debug" : 1,
        "debug_level" : DEBUG_LEVEL,
        "verbose" : VERBOSE,
        "L1" : "1",
        "cache_size" : "16KiB"
    })

    # Setup Cache Router
    l1router = sst.Component("cpu"+str(cid)+"_l1router", "merlin.hr_router")
    l1router.setSubComponent("topology", "merlin.singlerouter")
    l1router.addParams({
        "input_buf_size" : "512B",
        "output_buf_size" : "512B",
        "link_bw" : "1GB/s",
        "xbar_bw" : "1GB/s",
        "flit_size" : "32B",
        "num_ports" : "2",
        "id" : 0 })

    # Setup cache bridge
    bridge = sst.Component("cpu"+str(cid)+"_l1bridge", "merlin.Bridge")
    bridge.addParams({
        "translator": "memHierarchy.MemNetBridge",
        "debug": DEBUG,
        "debug_level" : DEBUG_LEVEL,
        "network_bw" : "25GB/s",
    })

    # Setup Links

    link_cpu_l1 = sst.Link("link_cpu"+str(cid)+"_l1")
    link_cpu_l1.connect( (memiface, "port", "1ns"), (l1cache, "high_network_0", "1ns") )

    link_l1_l1rtr = sst.Link("link_cpu"+str(cid)+"l1_l1rtr")
    link_l1_l1rtr.connect( (l1cache, "directory", "500ps"), (l1router, "port0", "500ps") )

    link_l1bridge = sst.Link("link_cpu"+str(cid)+"l1_bridge")
    link_l1bridge.connect( (bridge, "network0", "500ps"), (l1router, "port1", "500ps") )

    link_bridgenet = sst.Link("link_cpu"+str(cid)+"bridge_net")
    link_bridgenet.connect( (bridge, "network1", "500ps"), (network, "port"+str(cid), "500ps") )


# Setup Memory MC
memctrl = sst.Component("memory", "memHierarchy.MemController")
memctrl.addParams({
    "debug" : DEBUG,
    "debug_level" : DEBUG_LEVEL,
    "clock" : "2GHz",
    "verbose" : VERBOSE,
    "addr_range_start" : 0,
    "addr_range_end" : MEM_SIZE-1,
    "backing" : "malloc"
})

memory = memctrl.setSubComponent("backend", "memHierarchy.simpleMem")
memory.addParams({
    "access_time" : "100ns",
    "mem_size" : str(MEM_SIZE)+"B"
})

# Setup Directory Controller
dc = sst.Component("dc", "memHierarchy.DirectoryController")
dc.addParams({
    "debug": DEBUG,
    "debug_level" : DEBUG_LEVEL,
    "entry_cache_size": 256*1024*1024, #Entry cache size of mem/blocksize
    "clock": "1GHz",
    "network_bw": "25GB/s",
    "addr_range_start" : 0,
    "addr_range_end" : MEM_SIZE -1,
})

# Setup the links

dcmemLink = sst.Link("dc_to_mem")
dcmemLink.connect( (dc, "memory", "500ps"), (memctrl, "direct_link", "500ps") )
dcLink = sst.Link("dc_to_rtr")
dcLink.connect( (dc, "network", "500ps"), (network, "port"+str(numcpus), "500ps") )


sst.setStatisticOutput("sst.statOutputCSV")
sst.enableAllStatisticsForAllComponents()

# EOF

