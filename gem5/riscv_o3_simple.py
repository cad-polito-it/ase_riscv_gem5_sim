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
from m5.objects import Cache
from common import SimpleOpts
from m5 import trace

#from  RiscvCPU  import *

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
    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange(options.mem_size)]
    system.cpu = RiscvO3CPU() 
    system.cpu.createInterruptController()
    system.cpu.mmu.pma_checker.uncacheable=system.mem_ranges[0]
    system.membus = SystemXBar()
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports
    system.cpu.icache_port = system.membus.cpu_side_ports
    system.cpu.dcache_port = system.membus.cpu_side_ports
    ## port connections 
    system.system_port = system.membus.cpu_side_ports
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
    exit_event = m5.simulate()
    # check in case of exception or wrong code
    if exit_event.getCause() !=  "workbegin":
        eprint("Exit ERROR: Done simulation @ tick = %s: %s" %
               (m5.curTick(), exit_event.getCause()))
        return exit_event.getCode()
    eprint("Starting trace in ROI (Region Of Interest) @ tick = %s: %s" %
           (m5.curTick(), exit_event.getCause()))
    m5.stats.reset()
    m5.trace.enable()
    exit_event=m5.simulate()
    # check in case of exception or wrong code
    if exit_event.getCause() !=  "workend":
        eprint("Exit ERROR: Done simulation @ tick = %s: %s" %
               (m5.curTick(), exit_event.getCause()))
        return exit_event.getCode()
    eprint("Finishing trace in ROI (Region Of Interest) @ tick = %s: %s" %
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
