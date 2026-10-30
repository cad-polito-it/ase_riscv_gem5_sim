# syntax=docker/dockerfile:1
#
# ASE RISC-V + gem5 simulation environment (RISC-V GNU toolchain + gem5 RISCV/opt).
# Works on amd64 (Intel/AMD, Windows, Linux) and arm64 (Apple Silicon): build natively on each.
#
#   docker build -t ase-riscv-gem5:local -f docker/Dockerfile .
#
# Build args (all optional):
#   GEM5_BRANCH   gem5 branch of cad-polito-it/gem5 (must match ase_studio_branches.json, "stable")
#   GEM5_JOBS     parallel jobs for the gem5 build; gem5 needs ~2 GB RAM per job (default 3)
#   TOOLCHAIN_JOBS parallel jobs for the toolchain build (default: all CPUs)

############################ RISC-V GNU toolchain ############################
FROM ubuntu:22.04 AS toolchain-build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        autoconf automake autotools-dev curl python3 python3-pip python3-tomli \
        libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf \
        libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake \
        libglib2.0-dev libslirp-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Network hiccups are common on slow connections: use HTTP/1.1, shallow clones and retries.
RUN git config --global http.version HTTP/1.1 \
    && for i in 1 2 3 4 5; do \
         git clone --depth 1 https://github.com/riscv-collab/riscv-gnu-toolchain.git /src/riscv-gnu-toolchain && break; \
         rm -rf /src/riscv-gnu-toolchain; sleep 10; \
       done \
    && test -d /src/riscv-gnu-toolchain/.git
WORKDIR /src/riscv-gnu-toolchain
ARG TOOLCHAIN_JOBS=0
RUN ./configure --prefix=/opt/riscv --enable-multilib \
    && make -j"$([ "${TOOLCHAIN_JOBS}" -gt 0 ] && echo "${TOOLCHAIN_JOBS}" || nproc)" \
    # Shrink the image: 2.6 GB -> ~0.5 GB. Target libraries lose only debug info; host
    # binaries (compiler, assembler, linker) are stripped. Order matters: use the unstripped
    # tool for the target libraries first.
    && (find /opt/riscv/riscv64-unknown-elf/lib /opt/riscv/lib -name '*.a' \
         -exec /opt/riscv/bin/riscv64-unknown-elf-strip --strip-debug {} \; 2>/dev/null || true) \
    && (find /opt/riscv/bin /opt/riscv/libexec /opt/riscv/riscv64-unknown-elf/bin -type f \
         -exec strip --strip-unneeded {} \; 2>/dev/null || true) \
    && rm -rf /opt/riscv/share/man /opt/riscv/share/info /opt/riscv/share/doc \
    # smoke test: the course builds RISC-V assembly with -nostdlib; also link a C program
    && printf '.globl _start\n_start:\n li a0,0\n li a7,93\n ecall\n' > /tmp/t.s \
    && /opt/riscv/bin/riscv64-unknown-elf-gcc -O0 -mcmodel=medlow -march=rv32imafd_zicsr_zifencei \
         -mabi=ilp32 -mno-relax -nostdlib -o /tmp/t.elf /tmp/t.s \
    && printf 'int main(void){return 0;}\n' > /tmp/t.c \
    && /opt/riscv/bin/riscv64-unknown-elf-gcc /tmp/t.c -o /tmp/t64

################################### gem5 ####################################
FROM ubuntu:22.04 AS gem5-build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git m4 scons zlib1g zlib1g-dev libprotobuf-dev protobuf-compiler \
        libprotoc-dev libgoogle-perftools-dev python3-dev python3-tk libboost-all-dev \
        pkg-config virtualenv python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ARG GEM5_BRANCH=stable
RUN git config --global http.version HTTP/1.1 \
    && for i in 1 2 3 4 5; do \
         git clone --depth 1 --branch "${GEM5_BRANCH}" --single-branch https://github.com/cad-polito-it/gem5.git /opt/gem5 && break; \
         rm -rf /opt/gem5; sleep 10; \
       done \
    && test -d /opt/gem5/.git
WORKDIR /opt/gem5
ARG GEM5_JOBS=3
# BuildKit builds independent stages in parallel; toolchain + gem5 compiling together exceed
# 8 GB of RAM (the linker gets killed). Depend on the finished toolchain so they run one at a time.
RUN --mount=type=bind,from=toolchain-build,source=/opt/riscv,target=/mnt/toolchain-built true
RUN virtualenv -p python3.10 /opt/venv && /opt/venv/bin/pip install scons==4 \
    && . /opt/venv/bin/activate \
    && PYTHON=/usr/bin/python3.10 PYTHON_CONFIG=/usr/bin/python3.10-config \
       scons build/RISCV/gem5.opt -j"${GEM5_JOBS}" \
    # keep only the final binary, stripped of debug info (483 MB -> ~28 MB)
    && strip build/RISCV/gem5.opt \
    && mv build/RISCV/gem5.opt /opt/gem5.opt && rm -rf build && mkdir -p build/RISCV \
    && mv /opt/gem5.opt build/RISCV/gem5.opt

################################### final ###################################
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-tk make git socat ca-certificates \
        libmpc3 libmpfr6 libgmp10 libexpat1 zlib1g libprotobuf23 libgoogle-perftools4 libpython3.10 \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'
# Several small layers (instead of one huge one): on a flaky connection Docker restarts only
# the layer that failed.
COPY --from=toolchain-build /opt/riscv/bin /opt/riscv/bin
COPY --from=toolchain-build /opt/riscv/libexec /opt/riscv/libexec
COPY --from=toolchain-build /opt/riscv/riscv64-unknown-elf /opt/riscv/riscv64-unknown-elf
COPY --from=toolchain-build /opt/riscv/lib /opt/riscv/lib
COPY --from=toolchain-build /opt/riscv/share /opt/riscv/share
COPY --from=toolchain-build /opt/riscv/include /opt/riscv/include
COPY --from=gem5-build /opt/gem5 /opt/gem5
# setup_default of the simulator repo honours these overrides (GEM5_SRC needs its trailing slash)
ENV RISCV_TOOLCHAIN_PATH=/opt/riscv/bin \
    GEM5_INSTALLATION_PATH=/opt/gem5/build/RISCV/gem5.opt \
    GEM5_SRC=/opt/gem5/ \
    HOME=/tmp
COPY docker/ase-sim docker/ase-studio /usr/local/bin/
RUN chmod +x /usr/local/bin/ase-sim /usr/local/bin/ase-studio \
    && /opt/gem5/build/RISCV/gem5.opt --help >/dev/null \
    && /opt/riscv/bin/riscv64-unknown-elf-gcc --version >/dev/null
# The simulator repository (with its ase_studio submodule) is mounted here.
WORKDIR /work
