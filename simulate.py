#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Behnam Farnaghinejad <behnam.farnaghinejad@polito.it>
# SPDX-License-Identifier: GPL-2.0-only
"""Unified RISC-V CPU simulation CLI using ASE Studio's backend."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add ase_studio module to path
repo_root = Path(__file__).parent.resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ase_studio.simulator import simulate, run_command


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="simulate.py",
        description="Simulate a RISC-V CPU with gem5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./simulate.py                              # Interactive mode: select program
  ./simulate.py -i ./programs/my_program     # Non-interactive: simulate specific program
  ./simulate.py -s ./setup_default_vm        # Use alternate setup file
        """,
    )

    parser.add_argument(
        "-i",
        dest="program",
        metavar="PATH",
        help="Path to program folder (non-interactive mode)",
    )

    parser.add_argument(
        "-s", "--setup",
        dest="setup",
        metavar="PATH",
        default="./setup_default",
        help="Path to setup file (default: ./setup_default)",
    )

    args = parser.parse_args()

    root = Path.cwd()
    setup_file = Path(args.setup).resolve()
    results_dir = root / "results"
    programs_dir = root / "programs"

    # Validate setup file
    if not setup_file.exists():
        print(f"\033[31mERROR: Setup file {args.setup} not found\033[0m", file=sys.stderr)
        return 1

    # Determine program folder
    program_folder = None

    if args.program:
        # Non-interactive mode
        program_folder = Path(args.program).resolve()
        if not program_folder.is_dir():
            print(f"\033[31mError: Program folder not found: {args.program}\033[0m", file=sys.stderr)
            return 1
    else:
        # Interactive mode: show menu
        programs = sorted([d for d in programs_dir.iterdir() if d.is_dir()])

        if not programs:
            print("\033[31mNo programs in your workspace.\033[0m", file=sys.stderr)
            return 1

        print("Select a program in programs:")
        for i, prog in enumerate(programs, 1):
            print(f"  {i}) {prog.name}")

        try:
            choice = input("Enter choice (number): ").strip()
            choice_int = int(choice)
            if 1 <= choice_int <= len(programs):
                program_folder = programs[choice_int - 1]
            else:
                print("Invalid choice", file=sys.stderr)
                return 1
        except (ValueError, IndexError, EOFError):
            print("Invalid choice", file=sys.stderr)
            return 1

    if program_folder is None:
        print("\033[31mError in specifying the program folder\033[0m", file=sys.stderr)
        return 1

    program_name = program_folder.name
    print(f"Simulating {program_name}")

    # Compilation step
    print(f"Compiling program {program_name}")
    makefile = program_folder / "Makefile"

    if makefile.exists():
        # Load setup environment for compilation
        import os
        import subprocess
        command = ["bash", "-c", 'source "$1" >/dev/null; env -0', "simulate", str(setup_file)]
        result = subprocess.run(command, cwd=root, capture_output=True)
        env = os.environ.copy()
        for item in result.stdout.split(b"\0"):
            if b"=" in item:
                key, value = item.split(b"=", 1)
                env[key.decode(errors="ignore")] = value.decode(errors="replace")

        env["program"] = program_name

        # Run make clean
        clean_rc, clean_output = run_command(["make", "clean"], program_folder, env)

        # Run make
        rc, output = run_command(["make"], program_folder, env)

        if rc != 0:
            print("\033[31mCompilation error\033[0m")
            print(output)
            return 1

    # Simulation step
    print(f"Simulating program {program_name}")
    result = simulate(program_folder, root, setup_file, results_dir)

    if not result["ok"]:
        print("\033[31mSimulation error\033[0m")
        print(result["output"])
        return 1

    print(result["output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
