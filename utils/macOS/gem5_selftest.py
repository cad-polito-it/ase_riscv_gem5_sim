#!/usr/bin/env python3
"""Check that a gem5.opt computes RISC-V floating point correctly.

A gem5 built on macOS without gem5_patches/0001 reads every FP source
operand truncated to 16 bits: 1.5 * 2.0 gives a canonical NaN. This test
compiles a few FP operations with the course flags, runs them on gem5 and
compares the results in the Exec trace.

Used by build_gem5.sh, build_app.py and the in-app gem5 update.

Usage: gem5_selftest.py GEM5_OPT --toolchain DIR_WITH_riscv64-elf-gcc
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROGRAM = """
.globl _start
_start:
    li      t0, 0x3FC00000      # 1.5
    fmv.w.x f0, t0
    li      t0, 0x40000000      # 2.0
    fmv.w.x f1, t0
    fmul.s  f2, f0, f1          # 3.0
    fmv.x.w a0, f2
    fcvt.d.s f3, f2
    fadd.d  f4, f3, f3          # 6.0
    fcvt.w.d a1, f4
    li      a7, 93
    ecall
"""
# Instruction in the Exec trace -> expected D= value.
EXPECTED = {"fmv_x_w": 0x40400000, "fcvt_w_d": 6}
FLAGS = ["-march=rv32imafd_zicsr_zifencei", "-mabi=ilp32", "-mno-relax",
         "-nostdlib", "-static"]

CONFIG = """
import sys, m5
from m5.objects import *
system = System(clk_domain=SrcClockDomain(clock="1GHz",
                                          voltage_domain=VoltageDomain()),
                mem_mode="atomic", mem_ranges=[AddrRange("64MB")])
system.cpu = RiscvAtomicSimpleCPU()
system.membus = SystemXBar()
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports
system.cpu.createInterruptController()
system.mem_ctrl = SimpleMemory(range=system.mem_ranges[0],
                               port=system.membus.mem_side_ports)
system.system_port = system.membus.cpu_side_ports
system.workload = SEWorkload.init_compatible(sys.argv[1])
system.cpu.workload = Process(cmd=[sys.argv[1]])
system.cpu.createThreads()
root = Root(full_system=False, system=system)
m5.instantiate()
m5.simulate(100000)
"""


def check(gem5: Path, toolchain: Path, env=None, timeout=120) -> tuple[bool, str]:
    """Return (ok, explanation)."""
    gem5, toolchain = Path(gem5).absolute(), Path(toolchain).absolute()
    with tempfile.TemporaryDirectory(prefix="gem5-selftest-") as tmp:
        tmp = Path(tmp)
        (tmp / "t.s").write_text(PROGRAM)
        (tmp / "config.py").write_text(CONFIG)
        try:
            build = subprocess.run([str(toolchain / "riscv64-elf-gcc"), *FLAGS, "t.s", "-o", "t.elf"],
                                   cwd=tmp, capture_output=True, text=True, env=env)
        except OSError as error:
            return False, f"the RISC-V compiler could not run: {error}"
        if build.returncode:
            return False, f"the test program does not compile:\n{build.stderr.strip()}"
        try:
            run = subprocess.run([str(gem5), "--debug-flags=Exec", f"--outdir={tmp / 'm5out'}",
                                  "config.py", "t.elf"], cwd=tmp, capture_output=True,
                                 text=True, env=env, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            return False, f"gem5 could not run: {error}"
    trace = run.stdout + run.stderr
    found = {}
    for name in EXPECTED:
        match = re.search(rf": {name} .*?D=0x([0-9a-f]+)", trace)
        if match:
            found[name] = int(match.group(1), 16) & 0xFFFFFFFF
    if found.keys() != EXPECTED.keys():
        tail = "\n".join(trace.strip().splitlines()[-5:])
        return False, f"gem5 did not run the test program:\n{tail}"
    wrong = [f"{name} = {found[name]:#x} (expected {value:#x})"
             for name, value in EXPECTED.items() if found[name] != value]
    if wrong:
        return False, ("floating point is broken (1.5 * 2.0 must be 3.0): "
                       + ", ".join(wrong))
    return True, "floating point OK (1.5 * 2.0 = 3.0, 3.0 + 3.0 = 6.0)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("gem5", type=Path)
    parser.add_argument("--toolchain", type=Path, required=True,
                        help="directory containing riscv64-elf-gcc")
    args = parser.parse_args()
    ok, message = check(args.gem5, args.toolchain)
    print(f"gem5 self-test: {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
