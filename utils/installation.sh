#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR="${WORK_DIR}/tools"
UTILS_DIR="${WORK_DIR}/utils"
OS="$(uname -s)"
ARCH="$(uname -m)"
ASE_STUDIO_REPOSITORY="https://github.com/cad-polito-it/ase-studio.git"
BRANCH_CONFIG="${WORK_DIR}/ase_studio_branches.json"
if [[ ! -f "${BRANCH_CONFIG}" ]]; then
    echo "Missing ASE Studio branch configuration: ${BRANCH_CONFIG}" >&2
    exit 1
fi
GEM5_REQUIRED_BRANCH="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["gem5"])' "${BRANCH_CONFIG}")"
export GEM5_REQUIRED_BRANCH
export WORK_DIR ROOT_DIR UTILS_DIR OS ARCH

usage() {
    cat <<'EOF'
Usage: ./utils/installation.sh COMMAND

Commands:
  toolchain   Install only the RISC-V GNU toolchain
  gem5        Install only the gem5 simulator
  ase-studio  Install ASE Studio and its native GTK launcher
  all-ase     Install toolchain, gem5, and ASE Studio
EOF
}

choose_command() {
    echo "Choose what to install:"
    select choice in \
        "All with ASE Studio (recommended)" \
        "ASE Studio only" \
        "RISC-V toolchain only" \
        "gem5 only" \
        "Cancel"; do
        case "${REPLY}" in
            1) CHOSEN_COMMAND="all-ase"; return ;;
            2) CHOSEN_COMMAND="ase-studio"; return ;;
            3) CHOSEN_COMMAND="toolchain"; return ;;
            4) CHOSEN_COMMAND="gem5"; return ;;
            5) exit 0 ;;
            *) echo "Enter a number from 1 to 5." >&2 ;;
        esac
    done
}

detect_distribution() {
    if [[ "${OS}" != "Linux" ]]; then
        echo "Unsupported operating system: ${OS}" >&2
        exit 1
    fi
    if command -v lsb_release >/dev/null 2>&1; then
        DISTRO="$(lsb_release -is)"
        VERSION="$(lsb_release -rs)"
    elif [[ -r /etc/os-release ]]; then
        # shellcheck disable=SC1091
        source /etc/os-release
        DISTRO="${ID:-}"
        VERSION="${VERSION_ID:-}"
    else
        echo "Could not determine the Linux distribution." >&2
        exit 1
    fi
    case "${DISTRO,,}" in
        ubuntu) DISTRO="Ubuntu" ;;
        fedora) DISTRO="Fedora" ;;
        arch|manjarolinux|manjaro) DISTRO="Arch" ;;
        *) echo "Unsupported Linux distribution: ${DISTRO}" >&2; exit 1 ;;
    esac
    MAJOR="${VERSION%%.*}"
    MINOR="${VERSION#*.}"
    export DISTRO MAJOR MINOR
}

component_target_exists() {
    local compiler
    case "$1" in
        toolchain)
            for compiler in "${ROOT_DIR}"/riscv-toolchain/bin/riscv*-gcc; do
                [[ -x "${compiler}" ]] && return 0
            done
            return 1
            ;;
        gem5) [[ -x "${ROOT_DIR}/gem5/build/RISCV/gem5.opt" ]] ;;
        *) return 1 ;;
    esac
}

install_native_component() {
    local component="$1"
    local script_name="${component}"
    [[ "${component}" == "toolchain" ]] && script_name="riscv-toolchain"
    if component_target_exists "${component}"; then
        echo "${component} is already installed; skipping."
        return
    fi
    local base="${UTILS_DIR}/${OS}/${DISTRO}/${script_name}"
    if [[ ! -f "${base}_dep.sh" || ! -f "${base}_install.sh" ]]; then
        echo "No ${component} installer is available for ${DISTRO}." >&2
        exit 1
    fi
    echo "Installing ${component} dependencies..."
    sudo -E bash "${base}_dep.sh"
    echo "Installing ${component}..."
    bash "${base}_install.sh"
}

install_ase_studio_dependencies() {
    case "${DISTRO}" in
        Ubuntu)
            sudo apt-get update
            sudo apt-get install -y git python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
            ;;
        Fedora)
            local manager="dnf"
            command -v dnf5 >/dev/null 2>&1 && manager="dnf5"
            sudo "${manager}" install -y git python3-gobject gtk3 webkit2gtk4.1
            ;;
        Arch)
            sudo pacman -Syu --needed --noconfirm git python-gobject gtk3 webkit2gtk-4.1
            ;;
    esac
}

install_ase_studio() {
    install_ase_studio_dependencies
    if [[ ! -f "${WORK_DIR}/ase_studio/install.sh" ]]; then
        if [[ -f "${WORK_DIR}/.gitmodules" ]]; then
            git -C "${WORK_DIR}" submodule update --init --recursive ase_studio
        else
            git clone "${ASE_STUDIO_REPOSITORY}" "${WORK_DIR}/ase_studio"
        fi
    else
        echo "Using the existing ASE Studio checkout."
    fi
    bash "${WORK_DIR}/ase_studio/install.sh"
}

set_setup_export() {
    local key="$1"
    local line="$2"
    local setup="${WORK_DIR}/setup_default"
    if grep -q "^export ${key}=" "${setup}"; then
        sed -i "s|^export ${key}=.*|${line}|" "${setup}"
    else
        printf '\n%s\n' "${line}" >> "${setup}"
    fi
}

update_setup_default() {
    local frontend="$1"
    set_setup_export RISCV_TOOLCHAIN_PATH 'export RISCV_TOOLCHAIN_PATH="${WORK_DIR}/tools/riscv-toolchain/bin"'
    set_setup_export CC 'export CC="${RISCV_TOOLCHAIN_PATH}/riscv64-unknown-elf-gcc"'
    set_setup_export OBJDUMP 'export OBJDUMP="${RISCV_TOOLCHAIN_PATH}/riscv64-unknown-elf-objdump"'
    set_setup_export CC_INSTALLATION_PATH 'export CC_INSTALLATION_PATH="${RISCV_TOOLCHAIN_PATH}/"'
    set_setup_export GEM5_INSTALLATION_PATH 'export GEM5_INSTALLATION_PATH="${WORK_DIR}/tools/gem5/build/"'
    set_setup_export GEM5_SRC 'export GEM5_SRC="${WORK_DIR}/tools/gem5"'
    if [[ "${frontend}" == "ase" ]]; then
        set_setup_export PIPELINE_VISUALIZER 'export PIPELINE_VISUALIZER="${WORK_DIR}/ase-studio.sh"'
    fi
}

command="${1:-}"
if [[ -z "${command}" ]]; then
    if [[ -t 0 ]]; then
        CHOSEN_COMMAND=""
        choose_command
        command="${CHOSEN_COMMAND}"
    else
        usage
        exit 2
    fi
fi
case "${command}" in
    toolchain|gem5|ase-studio|all-ase) ;;
    -h|--help|help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

mkdir -p "${ROOT_DIR}"
detect_distribution
case "${command}" in
    toolchain) install_native_component toolchain; update_setup_default none ;;
    gem5) install_native_component gem5; update_setup_default none ;;
    ase-studio) install_ase_studio; update_setup_default ase ;;
    all-ase)
        install_native_component toolchain
        install_native_component gem5
        install_ase_studio
        update_setup_default ase
        ;;
esac

echo "Installation completed successfully."
