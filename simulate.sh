#!/bin/bash

usage () {
	echo "simulate a riscv OoO cpu with gem5"
	echo "./simulate.sh [OPTIONS]"
	echo "OPTIONS: "
	echo "-i path to program folder"
	echo "-gui|-nogui (mutually exclusive) the gem5 is|not going to be visuallized by the pipeline visualizer"
	echo ""
	echo "Example: "
	echo "./simulate ./programs/my_fancy_c_benchmark -nogui"
	echo "it will search in the folder ./programs/my_fancy_c_benchmark"
	echo "for a recipe in a Makefile to compile, and create an executable file called my_fancy_c_benchmark.elf."
	echo "Afterward, it executed the architectural simulation with gem5."
	 
}

## arguments parsing 
gui="-nogui"
program_folder=""
program_folder_opt=false
## GET OPTIONS
while test $# -gt 0; do
case "$1" in 
-i) 
if  ${program_folder_opt} ; then 
echo "Redundant -i program folder arguments"
exit 1
fi 
shift 
if [[ $# -gt 0  &&  ! $1 =~ ^- ]]; then
   program_folder=$1
   program_folder_opt=true 
else
  echo "-i: no argument specified" 
  exit 1
fi
shift
;;
-gui)
gui="-gui"
shift 
;;
-nogui)
gui="-nogui"
shift 
;;
*|-h|help|--help|-help)
usage
exit 0 
;;

esac 
done 

if ! ${program_folder_opt} ; then 
echo "Error in specifying the program folder"
usage
exit 0
fi 

# sourcing what you need
. ./setup_default

export program_folder
export program=$(basename ${program_folder})
echo "Simulating ${program}"

export gui

if [[ ! -d "${RESULTS_DIR}/${program}" ]] ; then 
mkdir ${RESULTS_DIR}/${program}
else 
## clean up 
rm -f ${RESULTS_DIR}/${program}/*
fi 

echo "Compiling program ${program}"
## compilation done by the makefile in the folder 
cd ${program_folder}
if [[ -f "Makefile" ]] ; then 
# if recipe for compiling the program exists
make clean 
make 

if [[ $? -ne 0 ]] ; then 
	echo "Compilation error"
	exit 1
fi 
fi 
cd ${WORK_DIR}

echo "Simulating program ${program}"

gem5_options="--debug-flags=O3PipeView,O3CPUAll  --debug-file=${RESULTS_DIR}/${program}/trace.out --outdir=${RESULTS_DIR}/${program}/ --verbose "

# Debugging options
# --stats-file=FILE            Sets the output file for statistics [Default:   stats.txt]
# --dump-config=FILE           Dump configuration output file [Default: config.ini]

### NOTE : --output=${RESULTS_DIR}/${program}/program.out REMOVE IF YOU WANNNA SEE STDOUT IN TERMINAL 
simulation_script_option="--caches  -c ${program_folder}/${program}.elf --directory=${RESULTS_DIR}/${program}  --errout=${RESULTS_DIR}/${program}/programm.err "  

echo "${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option}" 
${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option}

# Launch Konata 
if [[ "${OSTYPE}" == "linux-gnu" ]] ; then 
if [[ "${gui}" == "-gui"  ]] ; then
	echo "${PATH_KONATA}konata  ${RESULTS_DIR}/${program}/trace.out "
	${PATH_KONATA}konata  ${RESULTS_DIR}/${program}/trace.out 2> /dev/null
fi
else 
echo "Warning! Konata cannot be launched (easily) from WSL"
echo "For windows users, you need to open the Konata application manually and load the trace"
fi 

