import sst
import argparse
import os

def connect(name, c0, port0, c1, port1, latency):
    link = sst.Link(name)
    link.connect((c0, port0, latency), (c1, port1, latency))
    return link

parser = argparse.ArgumentParser()
parser.add_argument('--home_path', default="../../../../") # TODO: Update as per your path
#parser.add_argument('--proj_path', default="iarpa_intel_branch/")
parser.add_argument('--proj_path', default="sst-src/")
parser.add_argument('--node1minAddr', type=int, default=100)
parser.add_argument('--node2minAddr', type=int, default=200)
parser.add_argument('--node3minAddr', type=int, default=300)
parser.add_argument('--node4minAddr', type=int, default=400)
parser.add_argument('--node1maxAddr', type=int, default=200)
parser.add_argument('--node2maxAddr', type=int, default=300)
parser.add_argument('--node3maxAddr', type=int, default=400)
parser.add_argument('--node4maxAddr', type=int, default=500)
parser.add_argument('--packet_count', type=int, default=1)
parser.add_argument('--max_reqs_per_cycle', type=int, default=2)

args = parser.parse_args()

exp_name = "Arbiter-Scenario6"

num_mem_ctrls = 4
num_pes = 1 # Number of Processing Engines (CPUs)
core_clock = "2800MHz"
cache_line_size = 64
memory_clock = "1600MHz"
total_memory_size = 1 # GB
total_memory_size_in_MB = total_memory_size * 1024
total_memory_size_in_bytes = total_memory_size * 1024 * 1024 * 1024

num_routers = 5
mem_interleave_size = 64
ring_latency = "300ps"
scratch_latency = "300ps"
ring_bandwidth = "96GB/s"
ring_flit_size = "8B"

mem_params = {
    "clock": memory_clock,
    "memNIC.network_bw": ring_bandwidth
}

pe_params = {
    "verbose": 0,
    "clock": core_clock,
    "max_reqs_cycle": args.max_reqs_per_cycle,
}

coherence_protocol = "MESI"

l1_cache_params = {
    "debug": 0,
    "cache_frequency": core_clock,
    "cache_size": "64KiB",
    "associativity": 8,
    "access_latency_cycles": 20,
    "L1": 1,
    "cache_line_size": cache_line_size,
    "coherence_protocol": coherence_protocol,
    "cache_type": "inclusive",
    "mshr_num_entries": 48,
    "mshr_latency_cycles": 4,
    "memNIC.network_bw": ring_bandwidth,
}

l2_cache_params = {
    "verbose": 0,
    "cache_frequency": core_clock,
    "cache_size": "256KiB",
    "associativity": 16,
    "access_latency_cycles": 100,
    "L1": 0,
    "cache_line_size": cache_line_size,
    "coherence_protocol": coherence_protocol,
    "cache_type": "inclusive",
    "mshr_num_entries": 256,
    "mshr_latency_cycles": 8,
    "memNIC.network_bw": ring_bandwidth,
    "num_cache_slices": num_pes,
    "slice_allocation_policy": "rr",
}

arbiter_params = {
    "arbiter_frequency": core_clock,
    "overrideGroupID": 3,
    "port1minAddr": args.node1minAddr,
    "port2minAddr": args.node2minAddr,
    "port3minAddr": args.node3minAddr,
    "port1maxAddr": args.node1maxAddr,
    "port2maxAddr": args.node2maxAddr,
    "port3maxAddr": args.node3maxAddr,
    "isCacheConnected": True,
}

mem_backend_params = {
    "config_ini": "%s%s/DRAMsim3/configs/DDR4_8Gb_x4_3200.ini"\
            % (args.home_path, args.proj_path),
    "output_dir": exp_name
}

ring_params = {
    "input_buf_size": "2KB",
    "output_buf_size": "2KB",
    "input_latency": ring_latency,
    "output_latency": ring_latency,
    "link_bw": ring_bandwidth,
    "xbar_bw": ring_bandwidth,
    "flit_size": ring_flit_size
}

topo_params = {
    "shape": num_routers, # Put number of router here
    "width": "1"
}

router_map = {}

print("Building a ring")
# Create routers --------------------------------------------------------------
for rtr_id in range(num_routers):
    rtr_name = "rtr_%d" % (rtr_id)
    print("\tBuilding %s" % (rtr_name))
    rtr = sst.Component(rtr_name, "merlin.hr_router")
    rtr.addParam("id", rtr_id)
    rtr.addParams(ring_params)
    rtr.addParams({"num_ports": 3})

    topo = rtr.setSubComponent("topology", "merlin.torus")
    topo.addParams(topo_params)
    topo.addParams({"local_ports": 1})

    router_map[rtr_name] = rtr
#------------------------------------------------------------------------------

# Connect routers -------------------------------------------------------------
for rtr_id in range(num_routers):
    if rtr_id == num_routers - 1:
        curr_rtr_name = "rtr_" + str(rtr_id)
        next_rtr_name = "rtr_0"
        print("\tConnecting %s.port0 to %s.port1" % (curr_rtr_name, next_rtr_name))
        connect("rtr_" + str(rtr_id),
                router_map[curr_rtr_name], "port0",
                router_map[next_rtr_name], "port1",
                ring_latency)
    else:
        curr_rtr_name = "rtr_" + str(rtr_id)
        next_rtr_name = "rtr_" + str(rtr_id+1)
        print("\tConnecting %s.port0 to %s.port1" % (curr_rtr_name, next_rtr_name))
        connect("rtr_" + str(rtr_id),
                router_map[curr_rtr_name], "port0",
                router_map[next_rtr_name], "port1",
                ring_latency)
#------------------------------------------------------------------------------

node_id = 0
mem_id = 0
pe_id = 0

###########################################################################
# Router 0 connection -----------------------------------------------------
###########################################################################

rtr_id = 0
rtr_name = "rtr_%d" % (rtr_id)

print("Building node_%d" % (rtr_id))

# Memory controller with the address range 0-node1minAddr
print("\tBuilding mem_ctrl_%d" % mem_id)
mem = sst.Component("mem_ctrl_%d" % mem_id, "memHierarchy.MemController")
mem.addParams(mem_params)
mem.addParams({
    "addr_range_start": 0,
    "addr_range_end": args.node1minAddr * 1024 * 1024})

mem_backend = mem.setSubComponent("backend", "memHierarchy.dramsim3")
mem_backend.addParams({"mem_size": str((args.node3maxAddr-args.node1minAddr) * 1024 * 1024) + "B"})
mem_backend.addParams(mem_backend_params)

print("\tBuilding directory_ctrl_%d" % mem_id)
dc = sst.Component("directory_ctrl_%d" % (mem_id), "memHierarchy.DirectoryController")
dc.addParams({
    "addr_range_start": args.node1minAddr * 1024 * 1024,
    "addr_range_end": args.node3maxAddr * 1024 * 1024})

print("\tCreating mem_ctrl_%d_directory_ctrl_%d_link"%(mem_id, mem_id))
connect("mem_ctrl_%d_directory_ctrl_%d_link"%(mem_id, mem_id),
        mem, "direct_link",
        dc, "memory",
        ring_latency)

print("\tCreating directory_ctrl_%d_rtr_%d_link"%(mem_id, rtr_id))
connect("directory_ctrl_%d_rtr_%d_link"%(mem_id, rtr_id),
        dc, "network",
        router_map[rtr_name], "port2",
        ring_latency)

mem_id += 1

###########################################################################
# Router 1 connection -----------------------------------------------------
###########################################################################

node_id += 1
rtr_id += 1
rtr_name = "rtr_%d" % (rtr_id)

print("Building node_%d" % (rtr_id))

# Memory controller with the address range 0-node1minAddr
print("\tBuilding mem_ctrl_%d" % mem_id)
mem = sst.Component("mem_ctrl_%d" % mem_id, "memHierarchy.MemController")
mem.addParams(mem_params)
mem.addParams({
    "addr_range_start": 0,
    "addr_range_end": args.node1minAddr * 1024 * 1024})

mem_backend = mem.setSubComponent("backend", "memHierarchy.dramsim3")
mem_backend.addParams({"mem_size": str((args.node1minAddr) * 1024 * 1024) + "B"})
mem_backend.addParams(mem_backend_params)

print("\tBuilding directory_ctrl_%d" % mem_id)
dc = sst.Component("directory_ctrl_%d" % (mem_id), "memHierarchy.DirectoryController")
dc.addParams({
    "addr_range_start": 0,
    "addr_range_end": args.node1minAddr * 1024 * 1024})

print("\tCreating mem_ctrl_%d_directory_ctrl_%d_link"%(mem_id, mem_id))
connect("mem_ctrl_%d_directory_ctrl_%d_link"%(mem_id, mem_id),
        mem, "direct_link",
        dc, "memory",
        ring_latency)

print("\tCreating directory_ctrl_%d_rtr_%d_link"%(mem_id, rtr_id))
connect("directory_ctrl_%d_rtr_%d_link"%(mem_id, rtr_id),
        dc, "network",
        router_map[rtr_name], "port2",
        ring_latency)

mem_id += 1

###########################################################################
# Router 2 connection -----------------------------------------------------
###########################################################################

node_id += 1
rtr_id += 1
rtr_name = "rtr_%d" % (rtr_id)

print("Building node_%d" % (rtr_id))

# Memory controller with the address range node4maxAddr to total_memory_size_in_MB
print("\tBuilding mem_ctrl_%d" % mem_id)
mem = sst.Component("mem_ctrl_%d" % mem_id, "memHierarchy.MemController")
mem.addParams(mem_params)
mem.addParams({
    "addr_range_start": args.node4maxAddr * 1024 * 1024,
    "addr_range_end": total_memory_size_in_MB * 1024 * 1024})

mem_backend = mem.setSubComponent("backend", "memHierarchy.dramsim3")
mem_backend.addParams({"mem_size": str((total_memory_size_in_MB-args.node4maxAddr) * 1024 * 1024) + "B"})
mem_backend.addParams(mem_backend_params)

print("\tBuilding directory_ctrl_%d" % mem_id)
dc = sst.Component("directory_ctrl_%d" % (mem_id), "memHierarchy.DirectoryController")
dc.addParams({
    "addr_range_start": args.node4maxAddr * 1024 * 1024,
    "addr_range_end": total_memory_size_in_MB * 1024 * 1024})

print("\tCreating mem_ctrl_%d_directory_ctrl_%d_link"%(mem_id, mem_id))
connect("mem_ctrl_%d_directory_ctrl_%d_link"%(mem_id, mem_id),
        mem, "direct_link",
        dc, "memory",
        ring_latency)

print("\tCreating directory_ctrl_%d_rtr_%d_link"%(mem_id, rtr_id))
connect("directory_ctrl_%d_rtr_%d_link"%(mem_id, rtr_id),
        dc, "network",
        router_map[rtr_name], "port2",
        ring_latency)

mem_id += 1

###########################################################################
# Router 3 connection -----------------------------------------------------
###########################################################################

node_id += 1
rtr_id += 1
rtr_name = "rtr_%d" % (rtr_id)

print("Building node_%d" % (rtr_id))

# PE ------------------------------------------------------------------
print("\tBuilding mirandaCPU_%d" % (pe_id))
pe = sst.Component("mirandaCPU_%d" % (pe_id), "miranda.BaseCPU")
pe.addParams(pe_params)
#----------------------------------------------------------------------

# L1 ------------------------------------------------------------------
print("\tBuilding l1_cache_%d" % (pe_id))
l1_cache = sst.Component("l1_cache_%d" % (pe_id), "memHierarchy.Cache")
l1_cache.addParams(l1_cache_params)
#----------------------------------------------------------------------

# L2 ------------------------------------------------------------------
print("\tBuilding l2_cache_%d" % (pe_id))
l2_cache = sst.Component("l2_cache_%d" % (pe_id), "memHierarchy.Cache")
l2_cache.addParams(l2_cache_params)
l2_cache.addParams({"slice_id": pe_id})
#----------------------------------------------------------------------

# Custom Random Generator ------------------------------------------------------
gen = pe.setSubComponent("generator", "miranda.CustomRandomGenerator")
gen.addParams({
    "avoid_addr_range_min_value" : args.node4minAddr,
    "avoid_addr_range_max_value" : args.node4maxAddr,
    "max_address" : total_memory_size_in_MB,
    "verbose" : 0,
    "count" : args.packet_count,
})
#----------------------------------------------------------------------

print("\tCreating mirandaCPU_%d_l1_cache_%d_link"%(pe_id, pe_id))
connect("mirandaCPU_%d_l1_cache_%d_link"%(pe_id, pe_id),
        pe, "cache_link",
        l1_cache, "high_network_0",
        ring_latency).setNoCut()

print("\tCreating l1_cache_%d_l2_cache_%d_link"%(pe_id, pe_id))
connect("l1_cache_%d_l2_cache_%d_link"%(pe_id, pe_id),
        l1_cache, "low_network_0",
        l2_cache, "high_network_0",
        ring_latency).setNoCut()

print("\tCreating l2_cache_%d_rtr_%d_link"%(pe_id, rtr_id))
connect("l2_cache_%d_rtr_%d_link"%(pe_id, rtr_id),
        l2_cache, "directory",
        router_map[rtr_name], "port2",
        ring_latency)

pe_id += 1

###########################################################################
# Router 4 connection -----------------------------------------------------
###########################################################################

node_id += 1
rtr_id += 1
rtr_name = "rtr_%d" % (rtr_id)

print("Building node_%d" % (rtr_id))

# PE ------------------------------------------------------------------
print("\tBuilding mirandaCPU_%d" % (pe_id))
pe = sst.Component("mirandaCPU_%d" % (pe_id), "miranda.BaseCPU")
pe.addParams(pe_params)
#----------------------------------------------------------------------

# L1 ------------------------------------------------------------------
print("\tBuilding l1_cache_%d" % (pe_id))
l1_cache = sst.Component("l1_cache_%d" % (pe_id), "memHierarchy.Cache")
l1_cache.addParams(l1_cache_params)
#----------------------------------------------------------------------

# L2 ------------------------------------------------------------------
print("\tBuilding l2_cache_%d" % (pe_id))
l2_cache = sst.Component("l2_cache_%d" % (pe_id), "memHierarchy.Cache")
l2_cache.addParams(l2_cache_params)
l2_cache.addParams({"slice_id": pe_id})
#----------------------------------------------------------------------

# Custom Random Generator ------------------------------------------------------
gen = pe.setSubComponent("generator", "miranda.CustomRandomGenerator")
gen.addParams({
    "avoid_addr_range_min_value" : args.node4minAddr,
    "avoid_addr_range_max_value" : args.node4maxAddr,
    "max_address" : total_memory_size_in_MB,
    "verbose" : 0,
    "count" : args.packet_count,
})
#----------------------------------------------------------------------

print("\tCreating mirandaCPU_%d_l1_cache_%d_link"%(pe_id, pe_id))
connect("mirandaCPU_%d_l1_cache_%d_link"%(pe_id, pe_id),
        pe, "cache_link",
        l1_cache, "high_network_0",
        ring_latency).setNoCut()

print("\tCreating l1_cache_%d_l2_cache_%d_link"%(pe_id, pe_id))
connect("l1_cache_%d_l2_cache_%d_link"%(pe_id, pe_id),
        l1_cache, "low_network_0",
        l2_cache, "high_network_0",
        ring_latency).setNoCut()

print("\tCreating l2_cache_%d_rtr_%d_link"%(pe_id, rtr_id))
connect("l2_cache_%d_rtr_%d_link"%(pe_id, rtr_id),
        l2_cache, "directory",
        router_map[rtr_name], "port2",
        ring_latency)

pe_id += 1

###########################################################################
# Connections Done -----------------------------------------------------
###########################################################################

sst.setStatisticOutput("sst.statoutputcsv")

csv_path = "%s%s"\
            % (args.home_path, args.proj_path)

sst.setStatisticOutputOptions({"filepath": "%s/sst-scripts/arbiter/%s.csv" % (csv_path, exp_name)})
sst.setStatisticLoadLevel(16)
sst.enableAllStatisticsForAllComponents()
