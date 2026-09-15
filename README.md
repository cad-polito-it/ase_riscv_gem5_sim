# Architetture dei Sistemi di Elaborazione@Politecnico di Torino: SIMULATING A RISC-V CPU WITH GEM5

This README provides an environment for simulating a program on a parametrizable RISC-V CPU and visualize the pipeline. You can see the flow in the Figure below.


![flow](.images/gem5_workflow.png "Simulation flow")

## Table of contest
- [Architetture dei Sistemi di Elaborazione@Politecnico di Torino: SIMULATING A RISC-V CPU WITH GEM5](#architetture-dei-sistemi-di-elaborazionepolitecnico-di-torino-simulating-a-risc-v-cpu-with-gem5)
  - [Table of contest](#table-of-contest)
  - [Setup the environment](#setup-the-environment)
    - [Prerequisites](#prerequisites)
    - [Installing a Risc-V toolchain, the cross-compiler](#installing-a-risc-v-toolchain-the-cross-compiler)
    - [Installing Gem5, the Architectural Simulator](#installing-gem5-the-architectural-simulator)
    - [Installing Konata, the Pipeline Visualizer](#installing-konata-the-pipeline-visualizer)
  - [HOWTO - Simulate a Program](#howto---simulate-a-program)
  - [HOWTO - Visualize the Pipeline with Konata](#howto---visualize-the-pipeline-with-konata)
  - [Contributors](#contributors)

## Setup the environment 
First of all, you need to clone the repository with the following command, for SSH:
```
$ git clone --branch ase_studio --recurse-submodules git@github.com:cad-polito-it/ase_riscv_gem5_sim.git
```
For HTTPS:
```
$ git clone --branch ase_studio --recurse-submodules https://github.com/cad-polito-it/ase_riscv_gem5_sim.git
```

### Prerequisites
In order to simulate a program, you need the following three tools:
- A Risc-V cross compiler
- An architectural simulator
- A pipeline visualizer

Installation guidelines are provided for each of the aforementioned tools.
In case you are using LABINF PCs, you can skip the installation part.

An important file for the simulation flow is the [```setup_default```](./setup_default).
In this file you need to specify you installation paths for different tools.
For example:
```
export CC="/usr/bin/riscv64-linux-gnu-gcc-10"
export GEM5_INSTALLATION_PATH="/mnt/d/gem5_simulator/build/"
export GEM5_SRC="/mnt/d/gem5_simulator/gem5/"
```
The ```CC``` is the cross compiler, and it is installed in ```/usr/bin```. Meanwhile the Architectural Simulator (Gem5) is installed in ```/mnt/d/gem5_simulator/build```, while its soruce are at ```/mnt/d/gem5_simulator/gem5```.

In the repository, you have different ```setup_default``` files, each one for a specific configuration (LABINF, VM, or your native installation). You can choose the one that fits your needs. For example, if you want to use the LABINF configuration, you can copy the corresponding file ```setup_default_labinf``` to ```setup_default```:
```bash 
$ cp setup_default.labinf setup_default
```

### Installation 

In the repository, you can find a script named [```installation.sh```](./utils/installation.sh) (in the utils folder) that can help you to download the cross-compiler, the gem5 simulator and generate the ```setup_default``` file. You can run it with the following command:

```bash
$ ./utils/installation.sh
```
It will install the cross-compiler, gem5 and the pipeline visualizer in a default folder  named ```./tools/```. 

**It automatically updates the ```setup_default``` file with the correct paths.**

Check the following installation guidelines for each tool for the necessary dependencies and requirements before running the ```installation.sh``` script.
#### Installing a Risc-V toolchain, the cross-compiler

You can compile from scratch the toolchain and the necessary dependencies for Risc-V following [these instructions](https://github.com/riscv-collab/riscv-gnu-toolchain).


#### Installing Gem5, the Architectural Simulator

Start by cloning gem5 from this repository:
```
$ git clone --branch fix/minor-store-source-version https://github.com/cad-polito-it/gem5
```

To install Gem5 and the necessary dependencies, you can follow the README of that repo as well as these [instructions](https://www.gem5.org/documentation/general_docs/building).

Just remember that you need the following Gem5 characteristics to install:
- ISA = RISCV.
- variant = opt.

#### Installing the Gem5 Pipeline Visualizer
$\color{Red}\Huge{\textsf{This section is for the In order Architecture}}$

To install the Gem5 Pipeline Visualizer, you can follow these [instructions](https://github.com/cad-polito-it/gem5_visualizer).

You need to install Qt 6.8.3 (**VERY IMPORTANT**) from [here](https://www.qt.io/download-qt-installer). 
You can follow [these instructions](https://doc.qt.io/qt-6/gettingstarted.html) for the installation.

Make sure to install the desktop version and the needed libraries, as well cmake as shown in the following:

![custom](.images/custom.png "Custom QT installation")
![what](.images/qt_what.png "What to select in the QT installation")

After installing Qt, you need to set the ```QT_INSTALLATION_DIR``` environment variable to point to the Qt installation directory. By default should be like the following:
```bash
export QT_INSTALLATION_DIR="/opt/Qt/6.8.3/gcc_64"
```

Then, you can run the ```installation.sh``` script that will download and compile the Gem5 Pipeline Visualizer.

#### Installing Konata, the Pipeline Visualizer

$\color{Red}\Huge{\textsf{This section is for the Out of Order (OoO) Architecture}}$

To download Konata, visit the Konata's [repository](https://github.com/shioyadan/Konata/releases)

Download the appropriate Konata release for your operating system. Konata is available for various platforms, including Windows, macOS, and Linux.

Unzip the release, inside you will find an executable named ```konata``` or ```konata.exe``` (**OS dependent!**).

**Be aware**: You need load the trace manually

## HOWTO - Simulate a Program

To simulate a program, run the `simulate.sh` script with the desired program as an argument, and the desired configuration file:  
```bash
./simulate.sh -i ./programs/sanity_test/ -nogui --setup ./setup_default
```

You can specify with `-gui `or `-nogui `the automatic opening of the Pipeline visualizer.

This will produce an ELF (Executable and Linkable Format) file in the `programs/sanity_test/` directory.
Afterward, the ELF is passed to the Architectural Simulator, and program-related statistics (```stats.txt```) and trace (```trace.out```)are dumped in ```./results/sanity_test/```

You can execute the script in interactive mode:
```bash
./simulate.sh -setup ./setup_default
```

## HOWTO - Add a new program
For adding a new program, you can follow the steps below:
1. Copy an existing folder in the `programs/` directory, e.g., `programs/program_1/` and rename it to `programs/program_2/`.
2. Modify the source code (assembly or c files) in the `program_2/` folder.
3. Modify the `Makefile` in the `program_2/` folder if necessary (add new source files). In the following line (line 23):
    ```makefile
    ASM = ./program2.s # Removed ./program1.s
    ```

## ASE Studio (Experimental)

ASE Studio is a lightweight teaching IDE distributed in the `ase_studio`
submodule. It uses GTK WebKit and the existing RISC-V compiler/gem5
configuration in `setup_default`; Qt is not required. When cloning this
repository, initialize the submodule as well:

```bash
git clone --branch ase_studio --recurse-submodules https://github.com/cad-polito-it/ase_riscv_gem5_sim.git
cd ase_riscv_gem5_sim
git submodule update --init --recursive
```

On Ubuntu or Debian, install the native GUI dependencies and the per-user
application launcher, then start Studio:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
./ase_studio/install.sh
./ase-studio.sh
```

The local server listens only on `127.0.0.1` and is displayed inside a native
application window without a browser address bar.
The installer adds ASE Studio to the current user's Linux application menu
using `ase_studio/frontend/icon.png`. No terminal or Ctrl+C is needed for
normal launching.
See [ase_studio/README.md](ase_studio/README.md) for the one-time submodule
publishing workflow and later update procedure.
Projects remain directories under `programs/`. Open an assembly project, edit
its source, then select **Run** to save, build with its existing
Makefile, run gem5, and view the real trace in the Pipeline tab. Build and gem5
output are shown in **Log Output**; generated traces and statistics stay in
`results/<project>/`.

Use **CPU Configuration** to choose an in-order or out-of-order (O3) CPU, set
integer/floating-point operation latencies, control in-order forwarding, and
select a memory model.
**Direct memory** has no cache and applies independent fixed response
delays to instruction reads, data reads, and data writes; normal CPU request and
return pipeline cycles still apply. Setting all three Direct-memory latencies
to one cycle is the zero-wait teaching model; MinorCPU's internal timing-port
plumbing is removed from this view while real hazard stalls remain.
**L1 caches + main
memory** models real cache hits and misses using the configured cache sizes,
line size, hit latency, and deterministic main-memory latency. The Studio fixes
the simulated clock at 1 GHz, so one nanosecond of memory delay is one CPU cycle.
Settings are saved per project
in `.ase-studio.json`. **Delete**
requires both confirmation and typing the project name; simulation results are
kept separately under `results/`.

The included first-version teaching suite targets the in-order CPU.
`demo_01_in_order` introduces the five stages; paired `hazard_raw_*` projects
compare forwarding on and off; and the load-use, structural, and control-flow
projects isolate other hazards. `memory_direct_1_cycle`, `memory_direct`, and
`memory_cache` compare zero-wait direct memory, fixed direct-memory latency,
and cache hit/miss behavior. `variables_watch` demonstrates scalar/vector
memory monitoring, including an unchanged variable, while `floating_point`
exercises floating-point ALU, multiply, divide, load, and store operations.
The Pipeline tab shows the configured stage diagram, instruction addresses,
and a cycle-numbered grid. Real waits are displayed as gray `S` cells;
functional-unit occupancy keeps its execution-stage color.

The green **Update** button appears at startup only when the configured Git
remote has a newer fast-forward update. Its result is shown in **Log Output**.
For safety, Studio will not pull while the working tree contains uncommitted
changes. Parent updates also initialize the pinned `ase_studio` submodule
revision. The gear button beside the theme control stores machine-local
RISC-V toolchain, gem5, ISA, variant, and maximum visible pipeline-cycle
settings in `.ase-studio-env.json`; portable paths may use `$HOME`, `$USER`, or
`$ASE_STUDIO_ROOT`. Reset it to return to `setup_default`. **Run Step**
rebuilds and records a real gem5 trace, then reveals one
clock cycle per click; the resizable register panel shows PC plus integer and
floating-point updates for both trace formats. Register values can be viewed as
binary, hexadecimal, signed or unsigned integers, or IEEE-754 single-precision
floating-point values. Drag the pipeline with the left or middle mouse button
to pan it. Closing the native window uses an action-titled confirmation and
shuts down the local server, so no terminal or Ctrl+C is needed.

Each successful **Submit** archive also contains the hidden
`.ase-submission.json` manifest. It records the UTC submission time and
SHA-256 hashes and sizes for the assembly source and exported pipeline CSV,
so instructors can compare submitted contents without opening every file.

Studio keeps only the mandatory text entry declaration (`.section .text`,
`.globl _start`, `_start:`) and final `End:`/exit syscall lines read-only. All
other lines—including an optional data section before the entry point—remain
editable. No Studio-specific markers are written to assembly files.

## Contributors
- Francesco Angione (francesco.angione@polito.it)
- Nicola di Gruttola giardino (nicola.digruttola@polito.it)
- Behnam Farnaghinejad (behnam.farnaghinejad@polito.it)
- Gabriele Filipponi (gabriele.filipponi@polito.it)
- Giorgio Insinga (giorgio.insinga@polito.it)
- Annachiara Ruospo (annachiara.ruospo@polito.it)
- Antonio Porsia (antonio.porsia@polito.it)

Feel free to contribute with issues and pull requests or contact us!
