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

"""
This is the RISCV equivalent to `simple.py` (which is designed to run using the
X86 ISA). More detailed documentation can be found in `simple.py`.
"""

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
from m5.objects.BranchPredictor import LTAGE
from m5.objects.FUPool import FUPool
from m5.objects.FuncUnit import OpDesc, FUDesc
from m5.objects.FuncUnitConfig import (
    FP_ALU, IntALU, FP_MultDiv, RdWrPort, IprPort
)

from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
# Utilities included with m5 for configuring common simulations
# from gem5/configs/common
import Options
import Simulation
from Caches import L1_ICache, L1_DCache


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


def create_cpu(options, cpu_id):
    # DerivO3CPU is the configurable out-of-order CPU model supplied by gem5
    the_cpu = DerivO3CPU(cpu_id=cpu_id)
    icache = L1_ICache(size=options.l1i_size, assoc=options.l1i_assoc)
    dcache = L1_DCache(size=options.l1d_size, assoc=options.l1d_assoc)
    ## Constrains stores loads only
    the_cpu.cacheStorePorts = 200
    the_cpu.cacheLoadPorts =200

    # ********************************************************
    #  -- CHANGE HERE THE CPU CONFIGURATION PARAMETERS --    *
    # ********************************************************
    ## possible values "RoundRobin", "Branch", "IQCount", "LSQCount"
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
    # Uncomment only one Branch Predictor at a time!

    # LOCAL BP
    # my_predictor = LocalBP()
    # my_predictor.localPredictorSize = 32
    # my_predictor.BTBEntries = 256
    # the_cpu.branchPred = my_predictor

    # TOURNAMENT BP
    # my_predictor = TournamentBP()
    # my_predictor.localPredictorSize = 32
    # my_predictor.localHistoryTableSize = 256
    # my_predictor.globalPredictorSize = 64
    # my_predictor.choicePredictorSize = 64
    # my_predictor.BTBEntries = 256
    # the_cpu.branchPred = my_predictor

    # BIMODE BP
    # my_predictor = BiModeBP()
    # my_predictor.globalPredictorSize = 64
    # my_predictor.choicePredictorSize = 64
    # my_predictor.BTBEntries = 256
    # the_cpu.branchPred = my_predictor

    # LTAGE BP
    my_predictor = LTAGE()
    my_predictor.BTBEntries = 128
    my_predictor.BTBTagSize = 56
    my_predictor.numThreads = 2
    my_predictor.RASSize = 32

    # TAGE Parameters
    my_predictor.tage.nHistoryTables = 6
    my_predictor.tage.tagTableTagWidths = [0, 7, 7, 8, 8, 9, 9]
    my_predictor.tage.logTagTableSizes = [0, 7, 7, 8, 8, 7, 7]
    my_predictor.tage.logUResetPeriod = 11
    my_predictor.tage.tagTableCounterBits = 3
    my_predictor.tage.tagTableUBits = 2
    # Loop parameters
    my_predictor.loop_predictor.loopTableTagBits = 10
    my_predictor.loop_predictor.loopTableConfidenceBits = 3
    my_predictor.loop_predictor.loopTableAgeBits = 3
    my_predictor.loop_predictor.initialLoopAge = 5
    my_predictor.loop_predictor.logLoopTableAssoc = 4
    my_predictor.loop_predictor.loopTableIterBits = 10
    my_predictor.loop_predictor.logSizeLoopPred = 4
    my_predictor.loop_predictor.withLoopBits = 10
    the_cpu.branchPred = my_predictor

    # ****************************
    # - FETCH STAGE
    # ****************************
    the_cpu.fetchWidth = 4
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
    the_cpu.decodeWidth = 2
    # possible values "Dynamic", "Partitioned", "Threshold"
    the_cpu.smtROBPolicy = "Partitioned"
    the_cpu.smtROBThreshold = 100 
    

    # ****************************
    # - RENAME STAGE
    # ****************************
    the_cpu.numROBEntries = 64
    the_cpu.numIQEntries = 3
    the_cpu.numPhysIntRegs = 80
    the_cpu.numPhysFloatRegs = 64
    the_cpu.renameWidth = 2
    the_cpu.numRobs = 2
    the_cpu.numPhysVecPredRegs = 32
    # most ISAs don't use condition-code regs, so default is 0
    the_cpu.numPhysCCRegs = 0

    # ****************************
    # - DISPATCH/ISSUE STAGE
    # ****************************
    the_cpu.dispatchWidth = 2
    the_cpu.issueWidth = 3

    # ****************************
    # - EXECUTE STAGE
    # ****************************

    # ********************************
    # -- FUNTIONAL UNITS DEFINITION
    # ********************************
    class BOOM_IntALU(IntALU):
        opList = [
            OpDesc(opClass="IntAlu", opLat=1, pipelined=False)
        ]
        count = 3

    class BOOM_IntMultDiv(FUDesc):
        opList = [
            OpDesc(opClass="IntMult", opLat=3, pipelined=False),
            OpDesc(opClass="IntDiv", opLat=8, pipelined=False)
        ]
        count = 3
    class BOOM_FP_ALU(FP_ALU):
        opList = [
            OpDesc(opClass="FloatAdd", opLat=4, pipelined=True),
            OpDesc(opClass="FloatCmp", opLat=4, pipelined=True),
            OpDesc(opClass="FloatCvt", opLat=4, pipelined=True),     
        ]
        count = 3

    class BOOM_FP_MultDiv(FP_MultDiv):
        opList = [
            OpDesc(opClass="FloatMult", opLat=4, pipelined=True),
            OpDesc(opClass="FloatMultAcc", opLat=4, pipelined=True),
            OpDesc(opClass="FloatDiv", opLat=4, pipelined=True),
            OpDesc(opClass="FloatSqrt", opLat=4, pipelined=True),
            OpDesc(opClass="FloatMisc", opLat=4, pipelined=True),
        ]
        count = 3

    class BOOM_SIMD(SIMD_Unit):
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
    class BOOM_PredALU(PredALU):
        opList = [OpDesc(opClass="SimdPredAlu")]
        count = 0

    class BOOM_ReadPort(ReadPort):
        opList = [OpDesc(opClass="MemRead"), OpDesc(opClass="FloatMemRead")]
        count = 3
    class BOOM_WritePort(WritePort):
        opList = [OpDesc(opClass="MemWrite"), OpDesc(opClass="FloatMemWrite")]
        count = 3 
    class BOOM_RdWrPort(RdWrPort):
        opList = [
            OpDesc(opClass="MemRead"),
            OpDesc(opClass="MemWrite"),
            OpDesc(opClass="FloatMemRead"),
            OpDesc(opClass="FloatMemWrite"),
        ]
        count = 3 + 2  


    class BOOM_IprPort(IprPort):
        opList = [OpDesc(opClass="IprAccess", opLat=3, pipelined=False)]
        count = 3    
    
    class BOOMFUPool(FUPool):
        FUList = [
            BOOM_IntALU(),
            BOOM_IntMultDiv(),
            BOOM_FP_ALU(),
            BOOM_FP_MultDiv(),
            BOOM_ReadPort(),
            BOOM_SIMD(),
            BOOM_PredALU(),
            BOOM_WritePort(),
            BOOM_RdWrPort(),
            BOOM_IprPort(),
        ]

    the_cpu.fuPool = BOOMFUPool()

    # ****************************
    # - WRITE/Memory STAGE
    # ****************************
    the_cpu.wbWidth = 2
    the_cpu.LQEntries = 32
    the_cpu.SQEntries = 32
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
    the_cpu.commitWidth = 2
    the_cpu.squashWidth = 2
    # Time buffer size for backwards communication
    the_cpu.backComSize = 5 
    # Time buffer size for forward communication
    the_cpu.forwardComSize = 5
    the_cpu[cpu_id].addPrivateSplitL1Caches(icache, dcache, None, None)
    the_cpu[cpu_id].createInterruptController()
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

    m5.stats.reset()
    m5.trace.disable()

    max_tick = options.abs_max_tick
    if options.rel_max_tick:
        max_tick = options.rel_max_tick
    elif options.maxtime:
        max_tick = int(options.maxtime * 1000 * 1000 * 1000 * 1000)

    eprint("Simulating until tick=%s" % (max_tick))

    real_cpus = [real_cpu_create_function(0)]
    mem_mode = real_cpus[0].memory_mode()

    if warmup_cpu_class:
        warmup_cpus = [warmup_cpu_class(cpu_id=0)]
        warmup_cpus[0].max_insts_any_thread = warmup_instructions
    else:
        warmup_cpus = real_cpus

    system = System(cpu=warmup_cpus,
                    mem_mode=mem_mode,
                    mem_ranges=[AddrRange(start=0x0000000080000000, size=options.mem_size)],
                    cache_line_size=options.cacheline_size,
                    physmem=SimpleMemory())
    system.multi_thread = False
    system.voltage_domain = VoltageDomain(voltage=options.sys_voltage)
    system.clk_domain = SrcClockDomain(clock=options.sys_clock,
                                       voltage_domain=system.voltage_domain)
    system.cpu_voltage_domain = VoltageDomain()
    system.cpu_clk_domain = SrcClockDomain(
        clock=options.cpu_clock,
        voltage_domain=system.cpu_voltage_domain)
    system.cache_line_size = options.cacheline_size
    if warmup_cpu_class:
        for cpu in real_cpus:
            cpu.clk_domain = system.cpu_clk_domain
            cpu.workload = process
            cpu.system = system
            cpu.switched_out = True
            cpu.createThreads()
        system.switch_cpus = real_cpus

    for cpu in system.cpu:
        cpu.clk_domain = system.cpu_clk_domain
        cpu.workload = process
        if options.prog_interval:
            cpu.progress_interval = options.prog_interval
        cpu.createThreads()

    system.workload = SEWorkload.init_compatible(process.executable)
    system.mem_mode = "timing"

    MemClass = Simulation.setMemClass(options)
    system.membus = SystemXBar()
    #system.mem_ctrl = MemCtrl()
    #system.mem_ctrl.dram = DDR3_1600_8x8()
    #for mem_range in system.mem_ranges:
    #    system.mem_ctrl.dram.range = mem_range   
    system.physmem.port = system.membus.mem_side_ports
    system.system_port = system.membus.cpu_side_ports
    # connect caches
    for cpu in system.cpu:
        cpu.icache.mem_side = system.membus.cpu_side_ports
        cpu.dcache.mem_side = system.membus.cpu_side_ports
    ## exit condition for eliminating the boilerplate
    system.exit_on_work_items=True
    system.num_work_ids=2
    system.work_begin_cpu_id_exit=0xc1a0
    system.work_begin_exit_count=1
    system.work_end_exit_count=1
    root = Root(full_system=False, system=system)

    m5.options.outdir = output_dir
    m5.instantiate(None)  # None == no checkpoint
    if warmup_cpu_class:
        eprint("Running warmup with warmup CPU class (%d instrs.)" %
               (warmup_instructions))
        max_tick -= m5.curTick()
        m5.stats.reset()
        eprint("Finished warmup; running real simulation")
        m5.switchCpus(system, real_cpus)
        exit_event = m5.simulate(max_tick)
        eprint("Done simulation @ tick = %s: %s" %
               (m5.curTick(), exit_event.getCause()))
    ## register the trace only for region of interest (ROI)
    eprint("Starting simulation")
    m5.trace.enable()
    exit_event=m5.simulate()
    ## check in case of exception or wrong code
    if exit_event.getCause() !=  "workbegin":
        eprint("Exit ERROR: Done simulation @ tick = %s: %s" %
               (m5.curTick(), exit_event.getCause()))
        return exit_event.getCode()
    eprint("Starting real snippet trace (ROI) @ tick = %s: %s" %
           (m5.curTick(), exit_event.getCause()))
    m5.stats.reset()
    exit_event=m5.simulate()
    ## check in case of exception or wrong code
    if exit_event.getCause() !=  "workend":
        eprint("Exit ERROR: Done simulation @ tick = %s: %s" %
               (m5.curTick(), exit_event.getCause()))
        return exit_event.getCode()
    eprint("Finishing real snippet trace (ROI) @ tick = %s: %s" %
           (m5.curTick(), exit_event.getCause()))
    m5.stats.dump()
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

    parser.set_defaults(
        # Default to writing to program.out in the current working directory
        # below, we cd to the simulation output directory
        output=os.environ["SLTENV_RESULTS_DIR"]+'/program.out',
        errout=os.environ["SLTENV_RESULTS_DIR"]+'/program.err',


        mem_size=4 * 1024 * 1024,
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
#    assert(not options.fastmem)
    assert (not options.standard_switch)
    assert (not options.repeat_switch)
    assert (not options.take_checkpoints)
    assert (not options.fast_forward)
    #assert (not options.maxinsts)
    assert (not options.l2cache)

    return options


def eprint(*args):
    sys.stderr.write("".join(args))
    sys.stderr.write("\n")


def main(options):
    process = create_process(options)
    run_simulation(options, process)


main(get_options())
