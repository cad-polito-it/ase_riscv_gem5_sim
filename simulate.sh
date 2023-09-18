#!/bin/bash

# Command line parameters
# 1. Program folder
# 2. -gui/-nogui = launch Konata



if [[ $# -ne 2 ]] ; then 
echo "Wrong number of parameters"
echo "Usage  $0 path_to_program_folder -gui/-nogui" 
exit 1
fi 

. ./setup_default

export program_folder=$1
export program=$(basename ${program_folder})
echo "Simulating ${program}"

export gui=$2

if [[ ! -d "${RESULTS_DIR}/${program}" ]] ; then 
mkdir ${RESULTS_DIR}/${program}
fi 

echo "Compiling program ${program}"
## compilation done by the makefile in the folder 
cd ${program_folder}
make clean 
make 
cd ${WORK_DIR}

echo "Simulating program ${program}"

gem5_options="--debug-flags=O3PipeView,O3CPUAll  --debug-file=${RESULTS_DIR}/${program}/trace.out --outdir=${RESULTS_DIR}/${program}/ --verbose "

# Debugging options
# --stats-file=FILE            Sets the output file for statistics [Default:   stats.txt]
# --dump-config=FILE           Dump configuration output file [Default: config.ini]

### NOTE : --output=${RESULTS_DIR}/${program}/program.out REMOVE IF YOU WANNNA SEE STDOUT IN TERMINAL 
simulation_script_option="--caches  -c ${program_folder}${program}.elf --directory=${RESULTS_DIR}/${program}  --errout=${RESULTS_DIR}/${program}/programm.err "  


echo "${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option}" 
${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option}

# Launch Konata 
if [[ ${gui} == "-gui" ]] ; then
	${PATH_KONATA}konata  ${RESULTS_DIR}/${program}/trace.out &
fi

