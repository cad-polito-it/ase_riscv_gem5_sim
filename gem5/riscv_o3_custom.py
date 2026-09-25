# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# Generic python libraries
import argparse
import os
import os.path
import sys

# Interface to m5 simulation, implementing in gem5/src
import m5
from m5.objects import (
    System, SrcClockDomain, VoltageDomain, AddrRange, SystemXBar, 
    MemCtrl, DDR3_1600_8x8, Process, Root, SEWorkload, DerivO3CPU
)
from m5.objects import *
from m5.objects.BranchPredictor import *
from m5.objects.FUPool import FUPool
from m5.objects.FuncUnit import OpDesc, FUDesc
from m5.objects.FuncUnitConfig import (
    FP_ALU, IntALU, FP_MultDiv, RdWrPort, IprPort
)

from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
# Utilities included with m5 for configuring common simulations
# from gem5/configs/common
from common import Options
from common import Simulation
from common.Caches import L1_ICache, L1_DCache
from m5.objects import Cache
from common import SimpleOpts
from m5 import trace

import create_predictor as predictor

"""
In the following a CPU configuration is created for the simulation.

To see the list of parameters you can set on the CPU, check:
gem5/src/cpu/o3/O3CPU.py.

Set functional units (i.e. pipelines for execution) the processor
has, see the 'fuPool' parameter to the CPU. You can see the definition of
DefaultFUPool, the default setting for this parameter, in src/cpu/o3/FUPool.py
This uses definitions of the available functional units shown in
src/cpu/o3/FuncUnitConfig.py.

For options for the branch predictor, see src/cpu/pred/BranchPredictor.py.
You can set the branch predictor using something like:

    my_predictor = LocalBP()
    my_predictor.localPredictorSize = 128
    the_cpu.branchPred = my_predictor

"""

# Some specific options for caches
# For all options see src/mem/cache/BaseCache.py
class L1Cache(Cache):
    """Simple L1 Cache with default values"""

    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def __init__(self, options=None):
        super(L1Cache, self).__init__()
        if options:
            self.tag_latency = options.ase_cache_latency
            self.data_latency = options.ase_cache_latency
            self.response_latency = options.ase_cache_latency

    def connectBus(self, bus):
        """Connect this cache to a memory-side bus"""
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU-side port
        This must be defined in a subclass"""
        raise NotImplementedError


class L1ICache(L1Cache):
    """Simple L1 instruction cache with default values"""

    # Set the default size
    size = "16kB"

    SimpleOpts.add_option(
        "--l1i_size", help=f"L1 instruction cache size. Default: {size}"
    )

    def __init__(self, opts=None):
        super(L1ICache, self).__init__(opts)
        if not opts or not opts.l1i_size:
            return
        self.size = opts.l1i_size

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU icache port"""
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    """Simple L1 data cache with default values"""

    # Set the default size
    size = "64kB"

    SimpleOpts.add_option(
        "--l1d_size", help=f"L1 data cache size. Default: {size}"
    )

    def __init__(self, opts=None):
        super(L1DCache, self).__init__(opts)
        if not opts or not opts.l1d_size:
            return
        self.size = opts.l1d_size

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU dcache port"""
        self.cpu_side = cpu.dcache_port


class L2Cache(Cache):
    """Simple L2 Cache with default values"""

    # Default parameters
    size = "256kB"
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

    SimpleOpts.add_option("--l2_size", help=f"L2 cache size. Default: {size}")

    def __init__(self, opts=None):
        super(L2Cache, self).__init__()
        if not opts or not opts.l2_size:
            return
        self.size = opts.l2_size

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports

def create_cpu(options, cpu_id):
    # from    gem5/src/arch/riscv/RiscvCPU.py
    # RiscvO3CPU is the configurable out-of-order CPU model supplied by gem5 for RISCV
    the_cpu = RiscvO3CPU() # it also creates an instance of the RiscvMMU and assign it to the cpu's mmu attribute
    # it inherits BaseO3CPU   
    # Constrains stores loads only
    the_cpu.cacheStorePorts = 200
    the_cpu.cacheLoadPorts =200
    # ********************************************************
    #  -- CHANGE HERE THE CPU CONFIGURATION PARAMETERS --    *
    # ********************************************************
    # possible values "RoundRobin", "Branch", "IQCount", "LSQCount"
    the_cpu.smtFetchPolicy="RoundRobin"
    ## possible values "Dynamic", "Partitioned", "Threshold" 
    the_cpu.smtLSQPolicy="Partitioned"
    ## possible values "RoundRobin", "OldestReady"
    the_cpu.smtCommitPolicy ="RoundRobin"
    # ****************************
    # - STAGES DELAY in clock cycles
    # ****************************
    # Decode to fetch delay
    the_cpu.decodeToFetchDelay = 1 
    # Rename to fetch delay
    the_cpu.renameToFetchDelay = 1 
    # Issue/Execute/Writeback to fetch delay
    the_cpu.iewToFetchDelay = 1
    # Commit to fetch delay
    the_cpu.commitToFetchDelay = 1
    # Rename to decode delay
    the_cpu.renameToDecodeDelay = 1
    # Issue/Execute/Writeback to decode delay
    the_cpu.iewToDecodeDelay = 1
    # Commit to decode delay
    the_cpu.commitToDecodeDelay = 1
    # Fetch to decode delay
    the_cpu.fetchToDecodeDelay = 1
    # Issue/Execute/Writeback to rename delay
    the_cpu.iewToRenameDelay =1
    # Commit to rename delay
    the_cpu.commitToRenameDelay = 1
    # Decode to rename delay
    the_cpu.decodeToRenameDelay =1
    # Commit to Issue/Execute/Writeback delay
    the_cpu.commitToIEWDelay = 1
    # Rename to Issue/Execute/Writeback delay
    the_cpu.renameToIEWDelay = 2
    # Issue to execute delay (internal " "to the IEW stage)
    the_cpu.issueToExecuteDelay =1 
    # Issue/Execute/Writeback to commit delay
    the_cpu.iewToCommitDelay = 1
    # Rename to reorder buffer delay
    the_cpu.renameToROBDelay = 1
    the_cpu.trapLatency = 13
    the_cpu.fetchTrapLatency = 1
    # **************** ************
    # -- BPU SELECTION
    # ****************************
    # predictors from src/cpu/pred/BranchPredictor.py
    # see create_predictors for choosing a predictor
    branch_predictors = {
        "local": predictor.create_LocalBP,
        "tournament": predictor.create_TournamentBP,
        "bimode": predictor.create_BiModeBP,
        "tage": predictor.create_TAGE,
    }
    the_cpu.branchPred = branch_predictors[options.ase_branch_predictor]()
    # ****************************
    # - FETCH STAGE
    # ****************************
    the_cpu.fetchWidth = options.ase_fetch_width
    the_cpu.fetchBufferSize = 16
    the_cpu.fetchQueueSize = 32
    the_cpu.smtNumFetchingThreads = 1
    # possible values "Dynamic", "Partitioned", "Threshold"]
    the_cpu.smtIQPolicy = "Partitioned"
    #SMT IQ Threshold Sharing Parameter
    the_cpu.smtIQThreshold = 100

    # ****************************
    # - DECODE STAGE
    # ****************************
    the_cpu.decodeWidth = options.ase_decode_width
    # possible values "Dynamic", "Partitioned", "Threshold"
    the_cpu.smtROBPolicy = "Partitioned"
    the_cpu.smtROBThreshold = 100 
    

    # ****************************
    # - RENAME STAGE
    # ****************************
    the_cpu.numROBEntries = options.ase_rob_entries
    the_cpu.numIQEntries = options.ase_iq_entries
    the_cpu.numPhysIntRegs = 80
    the_cpu.numPhysFloatRegs = 64
    the_cpu.renameWidth = options.ase_rename_width
    the_cpu.numRobs = 2000
    the_cpu.numPhysVecPredRegs = 32
    # most ISAs don't use condition-code regs, so default is 0
    the_cpu.numPhysCCRegs = 0

    # ****************************
    # - DISPATCH/ISSUE STAGE
    # ****************************
    the_cpu.dispatchWidth = options.ase_dispatch_width
    the_cpu.issueWidth = options.ase_issue_width
    
    # ****************************
    # - EXECUTE STAGE
    # ****************************

    # ********************************
    # -- FUNTIONAL UNITS DEFINITION
    # ********************************
    class CPU_IntALU(IntALU):
        opList = [
            OpDesc(opClass="IntAlu", opLat=options.ase_int_alu_latency,
                   pipelined=options.ase_int_alu_pipelined == "on")
        ]
        count = 1

    class CPU_IntMultDiv(FUDesc):
        opList = [
            OpDesc(opClass="IntMult", opLat=options.ase_int_mul_latency,
                   pipelined=options.ase_int_mul_pipelined == "on"),
            OpDesc(opClass="IntDiv", opLat=options.ase_int_div_latency,
                   pipelined=options.ase_int_div_pipelined == "on")
        ]
        count = 1
    class CPU_FP_ALU(FP_ALU):
        opList = [
            OpDesc(opClass="FloatAdd", opLat=options.ase_float_alu_latency,
                   pipelined=options.ase_float_alu_pipelined == "on"),
            OpDesc(opClass="FloatCmp", opLat=options.ase_float_alu_latency,
                   pipelined=options.ase_float_alu_pipelined == "on"),
            OpDesc(opClass="FloatCvt", opLat=options.ase_float_alu_latency,
                   pipelined=options.ase_float_alu_pipelined == "on"),
        ]
        count = 1

    class CPU_FP_MultDiv(FP_MultDiv):
        opList = [
            OpDesc(opClass="FloatMult", opLat=options.ase_float_mul_latency,
                   pipelined=options.ase_float_mul_pipelined == "on"),
            OpDesc(opClass="FloatMultAcc", opLat=options.ase_float_mul_latency,
                   pipelined=options.ase_float_mul_pipelined == "on"),
            OpDesc(opClass="FloatDiv", opLat=options.ase_float_div_latency,
                   pipelined=options.ase_float_div_pipelined == "on"),
            OpDesc(opClass="FloatSqrt", opLat=options.ase_float_div_latency,
                   pipelined=options.ase_float_div_pipelined == "on"),
            OpDesc(opClass="FloatMisc", opLat=options.ase_float_alu_latency,
                   pipelined=options.ase_float_alu_pipelined == "on"),
        ]
        count = 1

    class CPU_SIMD(SIMD_Unit):
        opList = [ 
        OpDesc(opClass="SimdAdd"),
        OpDesc(opClass="SimdAddAcc"),
        OpDesc(opClass="SimdAlu"),
        OpDesc(opClass="SimdCmp"),
        OpDesc(opClass="SimdCvt"),
        OpDesc(opClass="SimdMisc"),
        OpDesc(opClass="SimdMult"),
        OpDesc(opClass="SimdMultAcc"),
        OpDesc(opClass="SimdShift"),
        OpDesc(opClass="SimdShiftAcc"),
        OpDesc(opClass="SimdDiv"),
        OpDesc(opClass="SimdSqrt"),
        OpDesc(opClass="SimdFloatAdd"),
        OpDesc(opClass="SimdFloatAlu"),
        OpDesc(opClass="SimdFloatCmp"),
        OpDesc(opClass="SimdFloatCvt"),
        OpDesc(opClass="SimdFloatDiv"),
        OpDesc(opClass="SimdFloatMisc"),
        OpDesc(opClass="SimdFloatMult"),
        OpDesc(opClass="SimdFloatMultAcc"),
        OpDesc(opClass="SimdFloatSqrt"),
        OpDesc(opClass="SimdReduceAdd"),
        OpDesc(opClass="SimdReduceAlu"),
        OpDesc(opClass="SimdReduceCmp"),
        OpDesc(opClass="SimdFloatReduceAdd"),
        OpDesc(opClass="SimdFloatReduceCmp"),
        ]
        count = 0
    class CPU_PredALU(PredALU):
        opList = [OpDesc(opClass="SimdPredAlu")]
        count = 0

    class CPU_ReadPort(ReadPort):
        opList = [OpDesc(opClass="MemRead", opLat=1), OpDesc(opClass="FloatMemRead", opLat=1)]
        count = 2
    class CPU_WritePort(WritePort):
        opList = [OpDesc(opClass="MemWrite", opLat=1), OpDesc(opClass="FloatMemWrite", opLat=1)]
        count = 2
    class CPU_RdWrPort(RdWrPort):
        opList = [
            OpDesc(opClass="MemRead"),
            OpDesc(opClass="MemWrite"),
            OpDesc(opClass="FloatMemRead"),
            OpDesc(opClass="FloatMemWrite"),
        ]
        count = 0 


    class CPU_IprPort(IprPort):
        opList = [OpDesc(opClass="IprAccess", opLat=3, pipelined=False)]
        count = 0  
    
    class CPUFUPool(FUPool):
        FUList = [
            CPU_IntALU(),
            CPU_IntMultDiv(),
            CPU_FP_ALU(),
            CPU_FP_MultDiv(),
            CPU_ReadPort(),
            CPU_SIMD(),
            CPU_PredALU(),
            CPU_WritePort(),
            CPU_RdWrPort(),
            CPU_IprPort(),
        ]

    the_cpu.fuPool = CPUFUPool()

    # ****************************
    # - WRITE/Memory STAGE
    # ****************************
    the_cpu.wbWidth = options.ase_writeback_width
    the_cpu.LQEntries = options.ase_lq_entries
    the_cpu.SQEntries = options.ase_sq_entries
    # Number of places to shift addr before check
    the_cpu.LSQDepCheckShift = 4 
    # Should dependency violations be checked for loads & stores or just stores
    the_cpu.LSQCheckLoads = True
    # Number of load/store insts before the dep predictor should be invalidated
    the_cpu.store_set_clear_period = 250000 
    # Last fetched store table size
    the_cpu.LFSTSize = 1024 
    # Store set ID table size
    the_cpu.SSITSize = 1024
    # SMT LSQ Threshold Sharing Parameter
    the_cpu.smtLSQThreshold = 100
    ## total store ordering 
    the_cpu.needsTSO = False

    # ****************************
    # - COMMIT STAGE
    # ****************************
    the_cpu.commitWidth = options.ase_commit_width
    the_cpu.squashWidth = options.ase_commit_width
    # Time buffer size for backwards communication
    # Functional-unit and memory completions can arrive well beyond the old
    # ten-cycle communication window.  A larger window prevents IEW from
    # indexing beyond TimeBuffer when a load or a long-latency FP op returns.
    the_cpu.backComSize = 256
    # Time buffer size for forward communication
    the_cpu.forwardComSize = 256
    return the_cpu

# run the gem5 simulation
def run_simulation(options, process):
    the_dir = os.path.join(options.directory)
    if not os.path.exists(the_dir):
        os.makedirs(the_dir)
    os.chdir(the_dir)
    # here it is the actual run
    exit_code=run_system_with_cpu(process, options, os.path.realpath("."),
                        real_cpu_create_function=lambda cpu_id: create_cpu(
                            options, cpu_id)
                        )
    sys.exit(exit_code)

def run_system_with_cpu(
        process, options, output_dir,
        warmup_cpu_class=None,
        warmup_instructions=0,
        real_cpu_create_function=lambda cpu_id: DerivO3CPU(cpu_id=cpu_id),
):
    # Override the -d outdir --outdir option to gem5
    m5.options.outdir = output_dir
    m5.core.setOutputDir(m5.options.outdir)
    m5.trace.disable()
    max_tick = options.abs_max_tick
    if options.rel_max_tick:
        max_tick = options.rel_max_tick
    elif options.maxtime:
        max_tick = int(options.maxtime * 1000 * 1000 * 1000 * 1000)

    eprint("Simulating until tick=%s" % (max_tick))
    system = System()

    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = "1GHz"
    system.clk_domain.voltage_domain = VoltageDomain()
    system.multi_thread = False
    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange(options.mem_size)]
    system.cpu = create_cpu(options,0)
    system.membus = SystemXBar()
    if options.ase_memory_mode != "cache":
        # Keep Direct mode deterministic: the configured delay is the full
        # memory-system latency rather than a delay plus hidden bus cycles.
        system.membus.forward_latency = 0
        system.membus.frontend_latency = 0
        system.membus.header_latency = 0
        system.membus.response_latency = 0
    for cpu in system.cpu:
        cpu.createInterruptController()
    system.system_port = system.membus.cpu_side_ports

    if options.ase_memory_mode == "cache":
        for cpu in system.cpu:
            cpu.icache = L1ICache(options)
            cpu.dcache = L1DCache(options)
            cpu.icache.connectCPU(cpu)
            cpu.dcache.connectCPU(cpu)
            cpu.icache.connectBus(system.membus)
            cpu.dcache.connectBus(system.membus)
        system.mem_ctrl = SimpleMemory(
            range=system.mem_ranges[0],
            latency=f"{options.ase_memory_latency}ns",
            latency_var="0ns", bandwidth="1000GiB/s")
    else:
        # Fetch/execute already contribute the first architectural cycle.
        # Delay elements model only the configured cycles beyond that stage.
        instruction_latency = max(0, options.ase_instruction_memory_latency - 1)
        data_read_latency = max(0, options.ase_data_read_latency - 1)
        data_write_latency = max(0, options.ase_data_write_latency - 1)
        system.instruction_delay = SimpleMemDelay(
            read_resp=f"{instruction_latency}ns")
        system.data_delay = SimpleMemDelay(
            read_resp=f"{data_read_latency}ns",
            write_resp=f"{data_write_latency}ns")
        for cpu in system.cpu:
            cpu.icache_port = system.instruction_delay.cpu_side_port
            cpu.dcache_port = system.data_delay.cpu_side_port
        system.instruction_delay.mem_side_port = system.membus.cpu_side_ports
        system.data_delay.mem_side_port = system.membus.cpu_side_ports
        system.mem_ctrl = SimpleMemory(
            range=system.mem_ranges[0], latency="0ns", latency_var="0ns",
            bandwidth="1000GiB/s")
    system.mem_ctrl.port = system.membus.mem_side_ports

    system.workload = RiscvSEWorkload.init_compatible(process.executable)
    system.cpu.workload = process
    system.cpu.createThreads()
    
    ## exit condition for region of interest
    system.exit_on_work_items=True
    system.num_work_ids=2
    system.work_begin_cpu_id_exit=0xc1a0
    system.work_begin_exit_count=1
    system.work_end_exit_count=1
    
    root = Root(full_system=False, system=system)
    m5.instantiate(None)
    print("Beginning simulation!")
    m5.trace.enable()
    exit_event = m5.simulate()
    m5.stats.dump()
    print("Ending simulation!")
    return 0

 

def create_process(options):
    #    process = LiveProcess()
    process = Process()
    process.executable = os.path.realpath(options.cmd)
    if options.options != "":
        process.cmd = [options.cmd] + options.options.split()
    else:
        process.cmd = [options.cmd]

    if options.input != "":
        process.input = options.input
    if options.output != "":
        process.output = options.output
    if options.errout != "":
        process.errout = options.errout

    return process


"""Retrieve command-line options for gem5 run"""


def get_options():
    parser = argparse.ArgumentParser()
    Options.addCommonOptions(parser)
    Options.addSEOptions(parser)

    # base output directory to use.
    # This takes precedence over gem5's built-in outdir option
    parser.add_argument("--directory", type=str, default="m5out")
    parser.add_argument("--ase-int-alu-latency", type=int, default=1)
    parser.add_argument("--ase-int-mul-latency", type=int, default=3)
    parser.add_argument("--ase-int-div-latency", type=int, default=8)
    parser.add_argument("--ase-float-alu-latency", type=int, default=6)
    parser.add_argument("--ase-float-mul-latency", type=int, default=8)
    parser.add_argument("--ase-float-div-latency", type=int, default=4)
    parser.add_argument("--ase-int-alu-pipelined", choices=("on", "off"), default="on")
    parser.add_argument("--ase-int-mul-pipelined", choices=("on", "off"), default="on")
    parser.add_argument("--ase-int-div-pipelined", choices=("on", "off"), default="on")
    parser.add_argument("--ase-float-alu-pipelined", choices=("on", "off"), default="on")
    parser.add_argument("--ase-float-mul-pipelined", choices=("on", "off"), default="on")
    parser.add_argument("--ase-float-div-pipelined", choices=("on", "off"), default="off")
    parser.add_argument("--ase-cache-stalls", choices=("on", "off"), default="on")
    parser.add_argument("--ase-memory-mode", choices=("direct", "cache"), default="direct")
    parser.add_argument("--ase-instruction-memory-latency", type=int, default=1)
    parser.add_argument("--ase-data-read-latency", type=int, default=1)
    parser.add_argument("--ase-data-write-latency", type=int, default=1)
    parser.add_argument("--ase-cache-latency", type=int, default=2)
    parser.add_argument("--ase-memory-latency", type=int, default=30)
    parser.add_argument("--ase-fetch-width", type=int, default=2)
    parser.add_argument("--ase-decode-width", type=int, default=2)
    parser.add_argument("--ase-rename-width", type=int, default=2)
    parser.add_argument("--ase-dispatch-width", type=int, default=2)
    parser.add_argument("--ase-issue-width", type=int, default=2)
    parser.add_argument("--ase-writeback-width", type=int, default=2)
    parser.add_argument("--ase-commit-width", type=int, default=2)
    parser.add_argument("--ase-rob-entries", type=int, default=64)
    parser.add_argument("--ase-iq-entries", type=int, default=128)
    parser.add_argument("--ase-lq-entries", type=int, default=32)
    parser.add_argument("--ase-sq-entries", type=int, default=32)
    parser.add_argument(
        "--ase-branch-predictor",
        choices=("local", "tournament", "bimode", "tage"),
        default="local",
    )

    parser.set_defaults(
        # Default to writing to program.out in the current working directory
        # below, we cd to the simulation output directory

        mem_size="8192MB",
        l1i_size="32kB",
        l1i_assoc=8,
        l1d_size="32kB",
        l1d_assoc=8,
        caches = True
    )

    args = parser.parse_args()
    options = args
    # Always enable caches, DerivO3CPU will not work without it.

    if not options.directory:
        eprint("You must set --directory to the name"
               "of an output directory to create")
        sys.exit(1)

    # Some features are not supported by this script,
    # but are added to parser by
    # Options.addSEOptions and Options.addCommonOptions

    # I check for these here to avoid confusion
    # If you are failing an assertion here,
    # removing the assertion will not make the option work.
    assert (not options.smt)
    assert (options.num_cpus == 1)
    assert (not options.standard_switch)
    assert (not options.repeat_switch)
    assert (not options.take_checkpoints)
    assert (not options.fast_forward)
    assert (not options.l2cache)

    return options


def eprint(*args):
    sys.stderr.write("".join(args))
    sys.stderr.write("\n")


def main(options):
    process = create_process(options)
    run_simulation(options, process)


main(get_options())
