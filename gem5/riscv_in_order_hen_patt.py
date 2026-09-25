# Copyright (c) 2012-2013 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2006-2008 The Regents of The University of Michigan
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

# Simple test script
#
# "m5 test.py"

import argparse
import sys
import os

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import addToPath, fatal, warn
from gem5.isas import ISA
from gem5.runtime import get_runtime_isa

addToPath("../")

from common import Options
from common import Simulation
from common import CacheConfig
from common import CpuConfig
from common import ObjectList
from common import MemConfig
from common.FileSystemConfig import config_filesystem
from common.Caches import *
from common.cpu2000 import *

# Functional units latencies. In order:
# - Integer ALU and Memory access address calculation
# - Integer Multiplication
# - Integer Division
# - Float ALU
# - Float Multiplication
# - Float Division

# The latency specifies the number of cycles it takes for the
# functional unit to execute an instruction after it is issued.
# The INTEGER_ALU_LATENCY controls also the latency of the memory
# address calculation
INTEGER_ALU_LATENCY = 1
INTEGER_MUL_LATENCY = 1
INTEGER_DIV_LATENCY = 1
FLOAT_ALU_LATENCY = 2
FLOAT_MUL_LATENCY = 7
FLOAT_DIV_LATENCY = 8

# A pipelined unit has an issue latency of one cycle. A non-pipelined unit's
# issue latency equals its operation latency, so it must finish before the next
# operation can enter that unit.



def get_process(args):
    """Interprets provided args and returns a list of processes"""

    inputs = None
    outputs = None
    errouts = None
    pargs = None

    workload = args.cmd
    if args.input != "":
        inputs = args.input
    if args.output != "":
        outputs = args.output
    if args.errout != "":
        errouts = args.errout
    if args.options != "":
        pargs = args.options

    process = Process(pid=100)
    process.executable = workload
    process.cwd = os.getcwd()
    process.gid = os.getgid()

    if args.env:
        with open(args.env, "r") as f:
            process.env = [line.rstrip() for line in f]

    if pargs is not None:
        process.cmd = [workload] + pargs.split()
    else:
        process.cmd = [workload]
    if inputs is not None:
        process.input = inputs
    if outputs is not None:
        process.output = outputs
    if errouts is not None:
        process.errout = errouts

    return process


parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)
parser.add_argument("--ase-int-alu-latency", type=int, default=INTEGER_ALU_LATENCY)
parser.add_argument("--ase-int-mul-latency", type=int, default=INTEGER_MUL_LATENCY)
parser.add_argument("--ase-int-div-latency", type=int, default=INTEGER_DIV_LATENCY)
parser.add_argument("--ase-float-alu-latency", type=int, default=FLOAT_ALU_LATENCY)
parser.add_argument("--ase-float-mul-latency", type=int, default=FLOAT_MUL_LATENCY)
parser.add_argument("--ase-float-div-latency", type=int, default=FLOAT_DIV_LATENCY)
parser.add_argument("--ase-int-alu-pipelined", choices=("on", "off"), default="on")
parser.add_argument("--ase-int-mul-pipelined", choices=("on", "off"), default="on")
parser.add_argument("--ase-int-div-pipelined", choices=("on", "off"), default="on")
parser.add_argument("--ase-float-alu-pipelined", choices=("on", "off"), default="on")
parser.add_argument("--ase-float-mul-pipelined", choices=("on", "off"), default="on")
parser.add_argument("--ase-float-div-pipelined", choices=("on", "off"), default="off")
parser.add_argument("--ase-forwarding", choices=("auto", "on", "off"), default="auto")
parser.add_argument("--ase-cache-stalls", choices=("auto", "on", "off"), default="auto")
parser.add_argument("--ase-memory-mode", choices=("direct", "cache"), default="direct")
parser.add_argument("--ase-instruction-memory-latency", type=int, default=1)
parser.add_argument("--ase-data-read-latency", type=int, default=1)
parser.add_argument("--ase-data-write-latency", type=int, default=1)
parser.add_argument("--ase-cache-latency", type=int, default=2)
parser.add_argument("--ase-memory-latency", type=int, default=30)

args = parser.parse_args()

if args.cmd:
    process = get_process(args)
else:
    print("No workload specified. Exiting!\n", file=sys.stderr)
    sys.exit(1)

(CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(args)
CPUClass.numThreads = 1

mp0_path = process.executable
system = System(
    cpu=[CPUClass(cpu_id=0)],
    mem_mode=test_mem_mode,
    mem_ranges=[AddrRange(args.mem_size)],
    cache_line_size=args.cacheline_size,
)

system.multi_thread = False

# Create a top-level voltage domain
system.voltage_domain = VoltageDomain(voltage=args.sys_voltage)

# Create a source clock for the system and set the clock period
system.clk_domain = SrcClockDomain(
    clock=args.sys_clock, voltage_domain=system.voltage_domain
)

# Create a CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Create a separate clock domain for the CPUs
system.cpu_clk_domain = SrcClockDomain(
    clock=args.cpu_clock, voltage_domain=system.cpu_voltage_domain
)

# All cpus belong to a common cpu_clk_domain, therefore running at a common
# frequency.

system.cpu[0].clk_domain = system.cpu_clk_domain

def minorMakeOpClassSet(op_classes):
    """Make a MinorOpClassSet from a list of OpClass enum value strings"""

    def boxOpClass(op_class):
        return MinorOpClass(opClass=op_class)

    return MinorOpClassSet(opClasses=[boxOpClass(o) for o in op_classes])


system.cpu[0].executeInputWidth = 1
system.cpu[0].executeInputBufferSize = 1
system.cpu[0].decodeInputBufferSize = 1
system.cpu[0].executeIssueLimit = 2
system.cpu[0].executeMemoryIssueLimit = 1
system.cpu[0].decodeToExecuteForwardDelay = 1
system.cpu[0].enableIdling = False
# A configured latency of one cycle is represented by the pipeline stage
# itself. Direct-1 uses MinorCPU's original wide fetch request so a cache-line
# boundary does not introduce a fake memory delay. Slower Direct
# memory requests words independently, while cache mode follows real lines.
fetch_width = (4 if args.ase_memory_mode == "direct"
               and args.ase_instruction_memory_latency > 1
               else args.cacheline_size if args.ase_memory_mode == "cache"
               else 512)
system.cpu[0].fetch1LineWidth = fetch_width
system.cpu[0].fetch1LineSnapWidth = (fetch_width if fetch_width == 4
                                     else args.cacheline_size)
system.cpu[0].enableForwarding = args.ase_forwarding != "off"

#############################################################################
# MODIFIABLE PART #
#############################################################################

# Functional units indices
# 0: Integer ALU, Memory access address calculation
# 1: Integer Multiplication
# 2: Integer Division
# 3: Float ALU
# 4: Float Multiplication
# 5: Float Division

# The parameter opLat is the latency of the functional unit, i.e., the number of cycles it takes for the
# functional unit to execute an instruction after it is issued.
system.cpu[0].executeFuncUnits.funcUnits[0].opLat = args.ase_int_alu_latency
system.cpu[0].executeFuncUnits.funcUnits[1].opLat = args.ase_int_mul_latency
system.cpu[0].executeFuncUnits.funcUnits[2].opLat = args.ase_int_div_latency
system.cpu[0].executeFuncUnits.funcUnits[3].opLat = args.ase_float_alu_latency
system.cpu[0].executeFuncUnits.funcUnits[4].opLat = args.ase_float_mul_latency
system.cpu[0].executeFuncUnits.funcUnits[5].opLat = args.ase_float_div_latency
# The parameter issueLat controls the issue latency of the functional unit, i.e., the number of cycles
# until another instruction can be issued to the functional unit after an instruction has already been issued.
system.cpu[0].executeFuncUnits.funcUnits[0].issueLat = (1 if args.ase_int_alu_pipelined == "on" else args.ase_int_alu_latency)
system.cpu[0].executeFuncUnits.funcUnits[1].issueLat = (1 if args.ase_int_mul_pipelined == "on" else args.ase_int_mul_latency)
system.cpu[0].executeFuncUnits.funcUnits[2].issueLat = (1 if args.ase_int_div_pipelined == "on" else args.ase_int_div_latency)
system.cpu[0].executeFuncUnits.funcUnits[3].issueLat = (1 if args.ase_float_alu_pipelined == "on" else args.ase_float_alu_latency)
system.cpu[0].executeFuncUnits.funcUnits[4].issueLat = (1 if args.ase_float_mul_pipelined == "on" else args.ase_float_mul_latency)
system.cpu[0].executeFuncUnits.funcUnits[5].issueLat = (1 if args.ase_float_div_pipelined == "on" else args.ase_float_div_latency)


# The parameter timings is a list of MinorFUTiming objects, each of which specifies the latency of the
# functional unit for a specific operation class. The parameter srcRegsRelativeLats specifies the
# relative latency of the source registers for each operation class. The parameter extraAssumedLat should
# not be touched.
system.cpu[0].executeFuncUnits.funcUnits[0].timings = [
    MinorFUTiming(
        description="Int",
        opClasses=minorMakeOpClassSet(["IntAlu"]),
        srcRegsRelativeLats=[0, 0],
    ),
    MinorFUTiming(
        description="Mem",
        opClasses=minorMakeOpClassSet(
            ["MemRead", "MemWrite", "FloatMemRead", "FloatMemWrite"]
        ),
        srcRegsRelativeLats=[1, 0],
        extraAssumedLat=0,
    ),
]

system.cpu[0].executeFuncUnits.funcUnits[4].timings = [
    MinorFUTiming(
        description="FloatMult",
        opClasses=minorMakeOpClassSet(["FloatMult"]),
        srcRegsRelativeLats=[0, 0],
        extraCommitLat=0,
    ),
]
# The parameter cantForwardFromFUIndices specifies the indices of the functional units from which the
# functional unit cannot forward results.
system.cpu[0].executeFuncUnits.funcUnits[5].cantForwardFromFUIndices = [3, 4]
system.cpu[0].executeFuncUnits.funcUnits[5].timings[0].srcRegsRelativeLats = [
    0
]
system.cpu[0].executeFuncUnits.funcUnits[5].timings[0].extraAssumedLat = 1

system.cpu[0].executeFuncUnits.funcUnits[4].cantForwardFromFUIndices = [3, 5]
system.cpu[0].executeFuncUnits.funcUnits[4].timings[0].srcRegsRelativeLats = [
    0
]

system.cpu[0].executeFuncUnits.funcUnits[3].cantForwardFromFUIndices = [4, 5]
system.cpu[0].executeFuncUnits.funcUnits[3].timings[0].srcRegsRelativeLats = [
    0
]

if args.ase_forwarding != "auto":
    function_units = system.cpu[0].executeFuncUnits.funcUnits[:6]
    # In MinorCPU a relative source latency is the number of cycles before
    # write-back in which a dependent instruction may consume a forwarded
    # result.  The previous configuration used zero for both modes, so the
    # checkbox could not change scheduling.  With forwarding enabled, expose
    # the producer result one cycle before write-back (or earlier for longer
    # functional units); with it disabled, dependents wait for write-back.
    blocked_sources = [] if args.ase_forwarding == "on" else list(range(6))
    for function_unit in function_units:
        function_unit.cantForwardFromFUIndices = blocked_sources
        for timing in function_unit.timings:
            # Decode is one stage ahead of execution.  A relative latency of
            # one lets a dependent enter that stage on the producer's final
            # execution cycle; blocking the producer FU forces write-back.
            timing.srcRegsRelativeLats = [1] if args.ase_forwarding == "on" else [0]
            if args.ase_forwarding == "off":
                # The customized scoreboard records producer readiness at FU
                # completion.  Add the E->M/W register-file distance only for
                # non-forwarded results so consumers cannot issue at E.
                timing.extraAssumedLat = int(timing.extraAssumedLat) + 1

##################################################################
# END OF MODIFIABLE PART #
##################################################################

system.cpu[0].workload = process

system.cpu[0].createThreads()

MemClass = Simulation.setMemClass(args)

system.membus = SystemXBar()
system.membus.clk_domain = system.clk_domain
system.membus.forward_latency = 1 if args.ase_memory_mode == "cache" else 0
system.membus.frontend_latency = 1 if args.ase_memory_mode == "cache" else 0
system.membus.header_latency = 1 if args.ase_memory_mode == "cache" else 0
system.membus.response_latency = 1 if args.ase_memory_mode == "cache" else 0
system.system_port = system.membus.cpu_side_ports

if args.ase_memory_mode == "cache":
    CacheConfig.config_cache(args, system)
    # A deterministic backing store makes the configured miss penalty a
    # stable teaching parameter. Cache hit/miss behavior is still modeled by
    # gem5's timing caches; only DRAM row/bank variability is omitted.
    system.mem_ctrls = [SimpleMemory(
        range=system.mem_ranges[0], latency=f"{args.ase_memory_latency}ns",
        latency_var="0ns", bandwidth="1000GiB/s")]
    system.mem_ctrls[0].port = system.membus.mem_side_ports
else:
    # MinorCPU normally requires caches through the common configuration
    # helper, but its timing ports can connect directly to deterministic
    # memory.  Independent delay elements model instruction reads, data
    # reads, and data writes without pretending that a large cache is RAM.
    system.cpu[0].createInterruptController()
    # One architectural cycle is already occupied by F or M. These delays
    # therefore model only cycles beyond that stage rather than adding a
    # hidden extra cycle to every access.
    instruction_latency = max(0, args.ase_instruction_memory_latency - 1)
    data_read_latency = max(0, args.ase_data_read_latency - 1)
    data_write_latency = max(0, args.ase_data_write_latency - 1)
    system.instruction_delay = SimpleMemDelay(
        read_resp=f"{instruction_latency}ns", clk_domain=system.clk_domain)
    system.data_delay = SimpleMemDelay(
        read_resp=f"{data_read_latency}ns",
        write_resp=f"{data_write_latency}ns",
        clk_domain=system.clk_domain)
    system.cpu[0].icache_port = system.instruction_delay.cpu_side_port
    system.cpu[0].dcache_port = system.data_delay.cpu_side_port
    system.instruction_delay.mem_side_port = system.membus.cpu_side_ports
    system.data_delay.mem_side_port = system.membus.cpu_side_ports
    system.cpu[0].mmu.connectWalkerPorts(
        system.membus.cpu_side_ports, system.membus.cpu_side_ports)
    system.cpu[0].connectUncachedPorts(
        system.membus.cpu_side_ports, system.membus.mem_side_ports)
    system.mem_ctrls = [SimpleMemory(
        range=system.mem_ranges[0], latency="0ns", latency_var="0ns",
        bandwidth="1000GiB/s")]
    system.mem_ctrls[0].port = system.membus.mem_side_ports
config_filesystem(system, args)

system.workload = SEWorkload.init_compatible(mp0_path)

if args.wait_gdb:
    system.workload.wait_for_remote_gdb = True

root = Root(full_system=False, system=system)

if args.ase_memory_mode == "cache":
    # Configure the Cache SimObjects themselves. ``icache_port`` and
    # ``dcache_port`` are only PortRef connections; assigning latency fields
    # to those references creates unused Python attributes and leaves gem5's
    # cache parameters at their defaults.
    for cache in (system.cpu[0].icache, system.cpu[0].dcache):
        cache.data_latency = args.ase_cache_latency
        cache.tag_latency = args.ase_cache_latency
        cache.response_latency = args.ase_cache_latency
        cache.clk_domain = system.clk_domain

Simulation.run(args, root, system, FutureClass)
