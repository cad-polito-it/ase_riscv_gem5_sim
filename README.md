# ASE: SIMULATING AN OoO RISC-V CPU WITH GEM

This README provides instructions for simulating a program, disassembling an ELF file, and visualizing the pipeline using gem5 and Konata.

## Downloading Konata
To download Konata, visit the Konata releases page on GitHub: https://github.com/shioyadan/Konata/releases

Download the appropriate Konata executable for your operating system. Konata is available for various platforms, including Windows, macOS, and Linux.

## Simulating a Program

To simulate a program, follow these steps:

1. Navigate to the project directory.

2. Run the `simulate.sh` script with the desired program as an argument:

```bash
./simulate.sh programs/sanity_test/ -nogui
```

You can specify with `-gui `or `-nogui `the automatic opening of the Konata simulation.

This will produce an ELF (Executable and Linkable Format) file in the `programs/sanity_test/` directory.

## Disassembling the ELF File

To disassemble the ELF file and inspect program counter (PC) and addresses, follow these steps:

1. Use the following command to disassemble the ELF file and append the output to a log file (e.g., `log.txt`):
```bash
/software/riscv_toolchain/bin/riscv64-unknown-elf-objdump -d sanity_test.elf > log.txt
```
2. Open the `log.txt` file and locate the PC (Program Counter) of the `main` function. Make note of this value.

3. Search for the corresponding PC value in the `trace.out` file. This will help you find the TICK value associated with the PC.

## Setting up gem5 to Capture Trace


TODO tick not supported anymore 
TODO add support for roi simulation 
To set up gem5 to capture a trace from a specific TICK value, follow these steps:

1. Export the TICK value as an environment variable, replacing, for example, `"137400"` with the desired TICK value:

```bash
export TICKS_START="137400"
```

2. From this TICK value onward, gem5 will start saving the trace to the `trace.out` file.

## Visualizing the Pipeline with Konata

To visualize the pipeline, follow these steps:

1. Load the `trace.out` file onto Konata, a tool for visualizing gem5 traces.

2. Use Konata's interface to visualize and analyze the pipeline behavior of your simulated program.

These instructions should help you simulate, disassemble, and visualize a program's execution using gem5 and Konata.


























































































