import os
import sst
mh_debug_level=10
mh_debug=0
dbgAddr=0
stopDbg=0

pythonDebug=False

vanadis_isa = os.getenv("VANADIS_ISA", "MIPS")
isa="mipsel"
vanadis_isa = os.getenv("VANADIS_ISA", "RISCV64")
isa="riscv64"

loader_mode = os.getenv("VANADIS_LOADER_MODE", "0")

testDir="basic-io"
exe = "hello-world"
#exe = "hello-world-cpp"
#exe = "openat"
#exe = "printf-check"
#exe = "read-write"
#exe = "unlink"
#exe = "unlinkat"

#testDir = "basic-math"
#exe = "sqrt-double"
#exe = "sqrt-float"

#testDir = "basic-ops"
#exe = "test-branch"
#exe = "test-shift"

#testDir = "misc"
#exe = "mt-dgemm"
#exe = "stream"
#exe = "stream-fortran"
#exe = "gettime" 
#exe = "splitLoad"
#exe = "fork"
#exe = "clone"
#exe = "pthread"
#exe = "openmp"
#exe = "uname"
#exe = "mem-test"

physMemSize = "4GiB"

tlbType = "simpleTLB"
mmuType = "simpleMMU"

# Define SST core options
sst.setProgramOption("timebase", "1ps")
sst.setProgramOption("stop-at", "0 ns")

# Tell SST what statistics handling we want
sst.setStatisticLoadLevel(4)
sst.setStatisticOutput("sst.statOutputConsole")

full_exe_name = os.getenv("VANADIS_EXE", "./small/" + testDir + "/" + exe +  "/" + isa + "/" + exe )
exe_name= full_exe_name.split("/")[-1]

verbosity = int(os.getenv("VANADIS_VERBOSE", 2))
os_verbosity = os.getenv("VANADIS_OS_VERBOSE", verbosity)
pipe_trace_file = os.getenv("VANADIS_PIPE_TRACE", "")
lsq_entries = os.getenv("VANADIS_LSQ_ENTRIES", 32)

rob_slots = os.getenv("VANADIS_ROB_SLOTS", 64)
retires_per_cycle = os.getenv("VANADIS_RETIRES_PER_CYCLE", 4)
issues_per_cycle = os.getenv("VANADIS_ISSUES_PER_CYCLE", 4)
decodes_per_cycle = os.getenv("VANADIS_DECODES_PER_CYCLE", 4)

integer_arith_cycles = int(os.getenv("VANADIS_INTEGER_ARITH_CYCLES", 2))
integer_arith_units = int(os.getenv("VANADIS_INTEGER_ARITH_UNITS", 2))
fp_arith_cycles = int(os.getenv("VANADIS_FP_ARITH_CYCLES", 8))
fp_arith_units = int(os.getenv("VANADIS_FP_ARITH_UNITS", 2))
branch_arith_cycles = int(os.getenv("VANADIS_BRANCH_ARITH_CYCLES", 2))

auto_clock_sys = os.getenv("VANADIS_AUTO_CLOCK_SYSCALLS", "no")

cpu_clock = os.getenv("VANADIS_CPU_CLOCK", "2.3GHz")

numCpus = int(os.getenv("VANADIS_NUM_CORES", 2))
numThreads = int(os.getenv("VANADIS_NUM_HW_THREADS", 1))

vanadis_cpu_type = "vanadis."
vanadis_cpu_type += os.getenv("VANADIS_CPU_ELEMENT_NAME","dbg_VanadisCPU")

if (verbosity > 0):
    print("Verbosity: " + str(verbosity) + " -> loading Vanadis CPU type: " + vanadis_cpu_type)
    print("Auto-clock syscalls: " + str(auto_clock_sys))
#	vanadis_cpu_type = "vanadisdbg.VanadisCPU"

app_args = os.getenv("VANADIS_EXE_ARGS", "")

# this is broke, it need to be in CpuBlock
if app_args != "":
	app_args_list = app_args.split(" ")
	# We have a plus 1 because the executable name is arg0
	app_args_count = len( app_args_list ) + 1
	cpu.addParams({ "app.argc" : app_args_count })
	if (verbosity > 0):
		print("Identified " + str(app_args_count) + " application arguments, adding to input parameters.")
	arg_start = 1
	for next_arg in app_args_list:
		if (verbosity > 0):
			print("arg" + str(arg_start) + " = " + next_arg)
		cpu.addParams({ "app.arg" + str(arg_start) : next_arg })
		arg_start = arg_start + 1
else:
		if (verbosity > 0):
			print("No application arguments found, continuing with argc=0")

vanadis_decoder = "vanadis.Vanadis" + vanadis_isa + "Decoder"
vanadis_os_hdlr = "vanadis.Vanadis" + vanadis_isa + "OSHandler"


protocol="MESI"

# OS related params
osParams = {
    "processDebugLevel" : 0,
    "dbgLevel" : os_verbosity,
    "dbgMask" : 8,
    "cores" : numCpus,
    "hardwareThreadCount" : numThreads,
    "heap_start" : 512 * 1024 * 1024,
    "heap_end"   : (2 * 1024 * 1024 * 1024) - 4096,
    "page_size"  : 4096,
    "heap_verbose" : verbosity,
    "physMemSize" : physMemSize,
    "useMMU" : True,
}


processList = ( 
    ( 1, {
        "env_count" : 1,
        "env0" : "OMP_NUM_THREADS={}".format(numCpus*numThreads),
        "exe" : full_exe_name,
        "arg0" : exe_name,
    } ),
    #( 1, {
    #    "env_count" : 2, "env0" : "HOME=/home/sdhammo", "env1" : "NEWHOME=/home/sdhammo2", "argc" : 1, "exe" : "./tests/small/basic-io/hello-world/mipsel/hello-world",  
        #"exe" : "./tests/small/basic-io/read-write/mipsel/read-write",  
    #} ),
)

osl1cacheParams = {
    "access_latency_cycles" : "2",
    "cache_frequency" : cpu_clock,
    "replacement_policy" : "lru",
    "coherence_protocol" : protocol,
    "associativity" : "8",
    "cache_line_size" : "64",
    "cache_size" : "32 KB",
    "L1" : "1",
    "debug" : mh_debug,
    "debug_level" : mh_debug_level,
}

mmuParams = {
    "debug_level": 0,
    "num_cores": numCpus,
    "num_threads": numThreads,
    "page_size": 4096,
}

memRtrParams ={
      "xbar_bw" : "1GB/s",
      "link_bw" : "1GB/s",
      "input_buf_size" : "2KB",
      "num_ports" : str(numCpus+2),
      "flit_size" : "72B",
      "output_buf_size" : "2KB",
      "id" : "0",
      "topology" : "merlin.singlerouter"
}

dirCtrlParams = {
      "coherence_protocol" : protocol,
      "entry_cache_size" : "1024",
      "debug" : mh_debug,
      "debug_level" : mh_debug_level,
      "arbiter_name" : "arbiter",
#      "addr_range_start" : "0x0",
#      "addr_range_end" : "0xFFFFFFFF"
}

dirNicParams = {
      "network_bw" : "25GB/s",
      "group" : 2,
}

memCtrlParams = {
      "clock" : cpu_clock,
      "backend.mem_size" : physMemSize,
      "backing" : "malloc",
      "initBacking": 1,
#      "addr_range_start": 0,
#      "addr_range_end": 0xffffffff,
      "debug_level" : mh_debug_level,
      "debug" : mh_debug,

}

memParams = {
      "mem_size" : "4GiB",
      "access_time" : "1 ns"
}

# CPU related params
tlbParams = {
    "debug_level": 0,
    "hitLatency": 1,
    "num_hardware_threads": numThreads,
    "num_tlb_entries_per_thread": 64,
    "tlb_set_size": 4,
}

tlbWrapperParams = {
    "debug_level": 0,
}

decoderParams = {
    "loader_mode" : loader_mode,
    "uop_cache_entries" : 1536,
    "predecode_cache_entries" : 4
}

osHdlrParams = {
    "verbose" : os_verbosity,
}

branchPredParams = {
    "branch_entries" : 32
}

cpuParams = {
    "clock" : cpu_clock,
    "verbose" : verbosity,
    "hardware_threads": numThreads,
    "physical_fp_registers" : 168 * numThreads,
    "physical_integer_registers" : 180 * numThreads,
    "integer_arith_cycles" : integer_arith_cycles,
    "integer_arith_units" : integer_arith_units,
    "fp_arith_cycles" : fp_arith_cycles,
    "fp_arith_units" : fp_arith_units,
    "branch_unit_cycles" : branch_arith_cycles,
    "print_int_reg" : False,
    "print_fp_reg" : False,
    "pipeline_trace_file" : pipe_trace_file,
    "reorder_slots" : rob_slots,
    "decodes_per_cycle" : decodes_per_cycle,
    "issues_per_cycle" :  issues_per_cycle,
    "retires_per_cycle" : retires_per_cycle,
    "auto_clock_syscall" : auto_clock_sys,
    "pause_when_retire_address" : os.getenv("VANADIS_HALT_AT_ADDRESS", 0),
    "start_verbose_when_issue_address": dbgAddr,
    "stop_verbose_when_retire_address": stopDbg,
    "print_rob" : False,
}

lsqParams = {
    "verbose" : verbosity,
    "address_mask" : 0xFFFFFFFF,
    "load_store_entries" : lsq_entries,
    "fault_non_written_loads_after" : 0,
    "check_memory_loads" : "no"
}

l1dcacheParams = {
    "access_latency_cycles" : "2",
    "cache_frequency" : cpu_clock,
    "replacement_policy" : "lru",
    "coherence_protocol" : protocol,
    "associativity" : "8",
    "cache_line_size" : "64",
    "cache_size" : "32 KB",
    "L1" : "1",
    "debug" : mh_debug,
    "debug_level" : mh_debug_level,
}

l1icacheParams = {
    "access_latency_cycles" : "2",
    "cache_frequency" : cpu_clock,
    "replacement_policy" : "lru",
    "coherence_protocol" : protocol,
    "associativity" : "8",
    "cache_line_size" : "64",
    "cache_size" : "32 KB",
    "prefetcher" : "cassini.NextBlockPrefetcher",
    "prefetcher.reach" : 1,
    "L1" : "1",
    "debug" : mh_debug,
    "debug_level" : mh_debug_level,
}

l2cacheParams = {
    "access_latency_cycles" : "14",
    "cache_frequency" : cpu_clock,
    "replacement_policy" : "lru",
    "coherence_protocol" : protocol,
    "associativity" : "16",
    "cache_line_size" : "64",
    "cache_size" : "2MB",
    "mshr_latency_cycles": 3,
    "debug" : mh_debug,
    "debug_level" : mh_debug_level,
}
busParams = { 
    "bus_frequency" : cpu_clock, 
}

l2memLinkParams = { 
    "group" : 1,
    "network_bw" : "25GB/s" 
}

arbiter_params = {
    "arbiter_frequency": cpu_clock,
#    "overrideGroupID": 3,
    "port1minAddr": 0x0,
    "port2minAddr": 0xffffffff,
    "port3minAddr": 0x100000000,
    "port1maxAddr": 0x1ffffffff,
    "port2maxAddr": 0x200000000,
    "port3maxAddr": 0x2ffffffff,
    "isCacheConnected": True,
    "num_cpus": 1,
    "CPU0": "mirandaCPU_%d" % (0), 
    "allowedMinAddr0": 0x0, 
    "allowedMaxAddr0": 0x2ffffffff, 
}

class CPU_Builder:
    def __init__(self):
        pass

    # CPU 
    def build( self, prefix, nodeId, cpuId ):

        if pythonDebug:
            print("build {}".format(prefix) )

        # CPU
        cpu = sst.Component(prefix, vanadis_cpu_type)
        cpu.addParams( cpuParams )
        cpu.addParam( "core_id", cpuId )
        cpu.enableAllStatistics()

        # CPU.decoder
        for n in range(numThreads):
            decode     = cpu.setSubComponent( "decoder"+str(n), vanadis_decoder )
            decode.addParams( decoderParams )

            decode.enableAllStatistics()

            # CPU.decoder.osHandler 
            os_hdlr     = decode.setSubComponent( "os_handler", vanadis_os_hdlr )
            os_hdlr.addParams( osHdlrParams )

            # CPU.decocer.branch_pred
            branch_pred = decode.setSubComponent( "branch_unit", "vanadis.VanadisBasicBranchUnit" )
            branch_pred.addParams( branchPredParams )
            branch_pred.enableAllStatistics()

        # CPU.lsq
        cpu_lsq = cpu.setSubComponent( "lsq", "vanadis.VanadisBasicLoadStoreQueue" )
        cpu_lsq.addParams(lsqParams)
        cpu_lsq.enableAllStatistics()

        # CPU.lsq mem interface which connects to D-cache 
        cpuDcacheIf = cpu_lsq.setSubComponent( "memory_interface", "memHierarchy.standardInterface" )

        # CPU.mem interface for I-cache
        cpuIcacheIf = cpu.setSubComponent( "mem_interface_inst", "memHierarchy.standardInterface" )

        # L1 D-cache
        cpu_l1dcache = sst.Component(prefix + ".l1dcache", "memHierarchy.Cache")
        cpu_l1dcache.addParams( l1dcacheParams )

        # L1 I-cache to cpu interface 
        l1dcache_2_cpu     = cpu_l1dcache.setSubComponent("cpulink", "memHierarchy.MemLink")
        # L1 I-cache to L2 interface 
        l1dcache_2_l2cache = cpu_l1dcache.setSubComponent("memlink", "memHierarchy.MemLink")

        # L2 I-cache
        cpu_l1icache = sst.Component( prefix + ".l1icache", "memHierarchy.Cache")
        cpu_l1icache.addParams( l1icacheParams )

        # L1 I-iache to cpu interface 
        l1icache_2_cpu     = cpu_l1icache.setSubComponent("cpulink", "memHierarchy.MemLink")
        # L1 I-cache to L2 interface 
        l1icache_2_l2cache = cpu_l1icache.setSubComponent("memlink", "memHierarchy.MemLink")

        # L2 cache
        cpu_l2cache = sst.Component(prefix+".l2cache", "memHierarchy.Cache")
        cpu_l2cache.addParams( l2cacheParams )

        # L2 cache cpu interface
        l2cache_2_l1caches = cpu_l2cache.setSubComponent("cpulink", "memHierarchy.MemLink")

        # L2 cache mem interface
        l2cache_2_mem = cpu_l2cache.setSubComponent("memlink", "memHierarchy.MemNIC")
        l2cache_2_mem.addParams( l2memLinkParams )

        # L1 to L2 buss
        cache_bus = sst.Component(prefix+".bus", "memHierarchy.Bus")
        cache_bus.addParams(busParams)

        # CPU data TLB
        dtlbWrapper = sst.Component(prefix+".dtlb", "mmu.tlb_wrapper")
        dtlbWrapper.addParams(tlbWrapperParams)
#        dtlbWrapper.addParam( "debug_level", 0)
        dtlb = dtlbWrapper.setSubComponent("tlb", "mmu." + tlbType );
        dtlb.addParams(tlbParams)

        # CPU instruction TLB
        itlbWrapper = sst.Component(prefix+".itlb", "mmu.tlb_wrapper")
        itlbWrapper.addParams(tlbWrapperParams)
#        itlbWrapper.addParam(    "debug_level", 0)
        itlbWrapper.addParam("exe",True)
        itlb = itlbWrapper.setSubComponent("tlb", "mmu." + tlbType );
        itlb.addParams(tlbParams)

        # CPU (data) -> TLB -> Cache
        link_cpu_dtlb_link = sst.Link(prefix+".link_cpu_dtlb_link")
        link_cpu_dtlb_link.connect( (cpuDcacheIf, "port", "1ns"), (dtlbWrapper, "cpu_if", "1ns") )
        link_cpu_dtlb_link.setNoCut()

        # data TLB -> data L1 
        link_cpu_l1dcache_link = sst.Link(prefix+".link_cpu_l1dcache_link")
        link_cpu_l1dcache_link.connect( (dtlbWrapper, "cache_if", "1ns"), (l1dcache_2_cpu, "port", "1ns") )
        link_cpu_l1dcache_link.setNoCut()

        # CPU (instruction) -> TLB -> Cache
        link_cpu_itlb_link = sst.Link(prefix+".link_cpu_itlb_link")
        link_cpu_itlb_link.connect( (cpuIcacheIf, "port", "1ns"), (itlbWrapper, "cpu_if", "1ns") )
        link_cpu_itlb_link.setNoCut()

        # instruction TLB -> instruction L1 
        link_cpu_l1icache_link = sst.Link(prefix+".link_cpu_l1icache_link")
        link_cpu_l1icache_link.connect( (itlbWrapper, "cache_if", "1ns"), (l1icache_2_cpu, "port", "1ns") )
        link_cpu_l1icache_link.setNoCut();

        # data L1 -> bus
        link_l1dcache_l2cache_link = sst.Link(prefix+".link_l1dcache_l2cache_link")
        link_l1dcache_l2cache_link.connect( (l1dcache_2_l2cache, "port", "1ns"), (cache_bus, "high_network_0", "1ns") )
        link_l1dcache_l2cache_link.setNoCut()

        # instruction L1 -> bus
        link_l1icache_l2cache_link = sst.Link(prefix+".link_l1icache_l2cache_link")
        link_l1icache_l2cache_link.connect( (l1icache_2_l2cache, "port", "1ns"), (cache_bus, "high_network_1", "1ns") )
        link_l1icache_l2cache_link.setNoCut()

        # BUS to L2 cache
        link_bus_l2cache_link = sst.Link(prefix+".link_bus_l2cache_link")
        link_bus_l2cache_link.connect( (cache_bus, "low_network_0", "1ns"), (l2cache_2_l1caches, "port", "1ns") )
        link_bus_l2cache_link.setNoCut()

        return (cpu, "os_link", "5ns"), (l2cache_2_mem, "port", "1ns") , (dtlb, "mmu", "1ns"), (itlb, "mmu", "1ns")


def addParamsPrefix(prefix,params):
    #print( prefix )
    ret = {}
    for key, value in params.items():
        #print( key, value )
        ret[ prefix + "." + key] = value

    #print( ret )
    return ret

# node OS
node_os = sst.Component("os", "vanadis.VanadisNodeOS")
node_os.addParams(osParams)

num=0
for i,process in processList: 
    #print( process )
    for y in range(i):
        #print( "process", num )
        node_os.addParams( addParamsPrefix( "process" + str(num), process ) )
        num+=1

if pythonDebug:
    print('total hardware threads ' + str(num) )
    
# node OS MMU
node_os_mmu = node_os.setSubComponent( "mmu", "mmu." + mmuType )
node_os_mmu.addParams(mmuParams)

# node OS memory interface to L1 data cache
node_os_mem_if = node_os.setSubComponent( "mem_interface", "memHierarchy.standardInterface" )

# node OS l1 data cache
os_cache = sst.Component("node_os.cache", "memHierarchy.Cache")
os_cache.addParams(osl1cacheParams)
os_cache_2_cpu = os_cache.setSubComponent("cpulink", "memHierarchy.MemLink")
os_cache_2_mem = os_cache.setSubComponent("memlink", "memHierarchy.MemNIC")
os_cache_2_mem.addParams( l2memLinkParams )

# node memory router 
comp_chiprtr = sst.Component("chiprtr", "merlin.hr_router")
comp_chiprtr.addParams(memRtrParams)
comp_chiprtr.setSubComponent("topology","merlin.singlerouter")

# Arbiter ------------------------------------------------------------------
#print("\tBuilding arbiter_%d" % (rtr_id))
arbiter = sst.Component("arbiter", "memHierarchy.RoundRobinArbiter")
arbiter.addParams(arbiter_params)

# node directory controller
dirctrl0 = sst.Component("dirctrl0", "memHierarchy.DirectoryController")
dirctrl0.addParams(dirCtrlParams)
dirctrl0.addParams({
    "addr_range_start": 0x0,
    "addr_range_end": 0xffffffff})
dirctrl1 = sst.Component("dirctrl1", "memHierarchy.DirectoryController")
dirctrl1.addParams(dirCtrlParams)
dirctrl1.addParams({
    "addr_range_start": 0x100000000,
    "addr_range_end": 0x1ffffffff})
dirctrl2 = sst.Component("dirctrl2", "memHierarchy.DirectoryController")
dirctrl2.addParams(dirCtrlParams)
dirctrl2.addParams({
    "addr_range_start": 0x200000000,
    "addr_range_end": 0x2ffffffff})

# link directory controller 
dc0_cpulink = dirctrl0.setSubComponent("cpulink", "memHierarchy.MemLink") # Connect this to your component
dc0_memlink = dirctrl0.setSubComponent("memlink", "memHierarchy.MemLink") # Connect this to the memory controller
dc1_cpulink = dirctrl1.setSubComponent("cpulink", "memHierarchy.MemLink") # Connect this to your component
dc1_memlink = dirctrl1.setSubComponent("memlink", "memHierarchy.MemLink") # Connect this to the memory controller
dc2_cpulink = dirctrl2.setSubComponent("cpulink", "memHierarchy.MemLink") # Connect this to your component
dc2_memlink = dirctrl2.setSubComponent("memlink", "memHierarchy.MemLink") # Connect this to the memory controller

# node memory controller
memctrl0 = sst.Component("memory0", "memHierarchy.MemController")
memctrl0.addParams( memCtrlParams )
memctrl0.addParams({
    "addr_range_start": 0x0,
    "addr_range_end": 0xffffffff})
memctrl1 = sst.Component("memory1", "memHierarchy.MemController")
memctrl1.addParams( memCtrlParams )
memctrl1.addParams({
    "addr_range_start": 0x100000000,
    "addr_range_end": 0x1ffffffff})
memctrl2 = sst.Component("memory2", "memHierarchy.MemController")
memctrl2.addParams( memCtrlParams )
memctrl2.addParams({
    "addr_range_start": 0x200000000,
    "addr_range_end": 0x2ffffffff})

# node memory controller port to directory controller
#memToDir0 = memctrl0.setSubComponent("cpulink", "memHierarchy.MemLink")
#memToDir1 = memctrl1.setSubComponent("cpulink", "memHierarchy.MemLink")
#memToDir2 = memctrl2.setSubComponent("cpulink", "memHierarchy.MemLink")

# node memory controller backend 
mem_backend_params = {
    "config_ini": "%s%s/DRAMSim3/configs/DDR4_8Gb_x4_3200.ini"\
            % ("../../../../../", "sst-src"),
    "output_dir": "./"
}
memory0 = memctrl0.setSubComponent("backend", "memHierarchy.dramsim3")
memory0.addParams(memParams)
memory0.addParams(mem_backend_params)
memory1 = memctrl1.setSubComponent("backend", "memHierarchy.dramsim3")
memory1.addParams(memParams)
memory1.addParams(mem_backend_params)
memory2 = memctrl2.setSubComponent("backend", "memHierarchy.dramsim3")
memory2.addParams(memParams)
memory2.addParams(mem_backend_params)

#memory0 = memctrl0.setSubComponent("backend", "memHierarchy.simpleMem")
#memory0.addParams(memParams)
#memory1 = memctrl1.setSubComponent("backend", "memHierarchy.simpleMem")
#memory1.addParams(memParams)
#memory2 = memctrl2.setSubComponent("backend", "memHierarchy.simpleMem")
#memory2.addParams(memParams)

# node OS data TLB
#ostlbWrapper = sst.Component("ostlb", "mmu.tlb_wrapper")
#ostlbWrapper.addParams(tlbWrapperParams)
#ostlb = ostlbWrapper.setSubComponent("tlb", "mmu." + tlbType );
#ostlb = ostlbWrapper.setSubComponent("tlb", "mmu.passThroughTLB" );
#ostlb.addParams(tlbParams)

# OS (data) -> TLB -> Cache
#link_os_ostlb_link = sst.Link("link_os_ostlb_link")
#link_os_ostlb_link.connect( (node_os_mem_if, "port", "1ns"), (ostlbWrapper, "cpu_if", "1ns") )

# arbiter to memory router
link_arb_2_rtr = sst.Link("link_arb_2_rtr")
link_arb_2_rtr.connect( (comp_chiprtr, "port"+str(numCpus), "1ns"), (arbiter, "directory", "1ns") )
link_arb_2_rtr.setNoCut()

# Directory controller to arbiter 
link_dir0_arb = sst.Link("directory_ctrl_%d_arbiter"%(0))
link_dir0_arb.connect((dc0_cpulink, "port","1ns"), (arbiter, "port1", "1ns"))
link_dir1_arb = sst.Link("directory_ctrl_%d_arbiter"%(1))
link_dir1_arb.connect((dc1_cpulink, "port","1ns"), (arbiter, "port2", "1ns"))
link_dir2_arb = sst.Link("directory_ctrl_%d_arbiter"%(2))
link_dir2_arb.connect((dc2_cpulink, "port","1ns"), (arbiter, "port3", "1ns"))

# Directory controller to memory controller 
link_dir_0_mem = sst.Link("link_dir_0_mem")
link_dir_0_mem.connect( (dc0_memlink, "port", "1ns"), (memctrl0, "direct_link", "1ns") )
link_dir_0_mem.setNoCut()
link_dir_1_mem = sst.Link("link_dir_1_mem")
link_dir_1_mem.connect( (dc1_memlink, "port", "1ns"), (memctrl1, "direct_link", "1ns") )
link_dir_1_mem.setNoCut()
link_dir_2_mem = sst.Link("link_dir_2_mem")
link_dir_2_mem.connect( (dc2_memlink, "port", "1ns"), (memctrl2, "direct_link", "1ns") )
link_dir_2_mem.setNoCut()

#link_dir_0_mem = sst.Link("link_dir_0_mem")
#link_dir_0_mem.connect( (dc0_memlink, "port", "1ns"), (memctrl0, "port", "1ns") )
#link_dir_0_mem.setNoCut()
#link_dir_1_mem = sst.Link("link_dir_1_mem")
#link_dir_1_mem.connect( (dc1_memlink, "port", "1ns"), (memToDir1, "port", "1ns") )
#link_dir_1_mem.setNoCut()
#link_dir_2_mem = sst.Link("link_dir_2_mem")
#link_dir_2_mem.connect( (dc2_memlink, "port", "1ns"), (memToDir2, "port", "1ns") )
#link_dir_2_mem.setNoCut()

# MMU -> ostlb 
# don't need when using pass through TLB
#link_mmu_ostlb_link = sst.Link("link_mmu_ostlb_link")
#link_mmu_ostlb_link.connect( (node_os_mmu, "ostlb", "1ns"), (ostlb, "mmu", "1ns") )

# ostlb -> os l1 cache
link_os_cache_link = sst.Link("link_os_cache_link")
#link_os_cache_link.connect( (ostlbWrapper, "cache_if", "1ns"), (os_cache_2_cpu, "port", "1ns") )
link_os_cache_link.connect( (node_os_mem_if, "port", "1ns"), (os_cache_2_cpu, "port", "1ns") )
link_os_cache_link.setNoCut()

os_cache_2_rtr = sst.Link("os_cache_2_rtr")
os_cache_2_rtr.connect( (os_cache_2_mem, "port", "1ns"), (comp_chiprtr, "port"+str(numCpus+1), "1ns") )
os_cache_2_rtr.setNoCut()

cpuBuilder = CPU_Builder()

# build all CPUs
nodeId = 0
for cpu in range(numCpus):

    prefix="node" + str(nodeId) + ".cpu" + str(cpu)
    os_hdlr, l2cache, dtlb, itlb = cpuBuilder.build(prefix, nodeId, cpu)

    # MMU -> dtlb 
    link_mmu_dtlb_link = sst.Link(prefix + ".link_mmu_dtlb_link")
    link_mmu_dtlb_link.connect( (node_os_mmu, "core"+ str(cpu) +".dtlb", "1ns"), dtlb )

    # MMU -> itlb 
    link_mmu_itlb_link = sst.Link(prefix + ".link_mmu_itlb_link")
    link_mmu_itlb_link.connect( (node_os_mmu, "core"+ str(cpu) +".itlb", "1ns"), itlb )
    
    # CPU os handler -> node OS
    link_core_os_link = sst.Link(prefix + ".link_core_os_link")
    link_core_os_link.connect( os_hdlr, (node_os, "core" + str(cpu), "5ns") )

    # connect cpu L2 to router
    link_l2cache_2_rtr = sst.Link(prefix + ".link_l2cache_2_rtr")
    link_l2cache_2_rtr.connect( l2cache, (comp_chiprtr, "port" + str(cpu), "1ns") )

