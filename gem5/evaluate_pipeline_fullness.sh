#!/usr/bin/bash


if [[ $# -eq 3 ]] ; then 
	echo "error in number of parameters for gem5 simulation " >&2
	exit 1
fi

program=$1
fitness_file=$2
SLTENV_RESULTS_DIR=$(dirname ${program}) 
## debug start first tick of interest --debug-start=0 -m 500 end tick , ,O3CPUAll  for every detail in debug flag
# --debug-start=732500  where the snippet starts
gem5_options="--debug-flags=O3PipeView,O3CPUAll --debug-file=${SLTENV_RESULTS_DIR}/trace.out"
#simulation_scipt_option="  --cpu-type=detailed --caches -c ./ "

## select output dir 
gem5_options=${gem5_options}" --outdir=${SLTENV_RESULTS_DIR} --verbose "
## select stout file 

## select stderr file

## verbose / quiet 

##--stats-file=FILE       Sets the output file for statistics [Default:   stats.txt]

# --dump-config=FILE      Dump configuration output file [Default: config.ini]

simulation_script_option="--caches  -c ${program} --directory=${SLTENV_RESULTS_DIR}   --dist"  

##simulation
echo "${SLTENV_GEM5_INSTALLATION_PATH}/${SLTENV_ISA}/gem5.${SLTENV_VARIANT} ${gem5_options} ${SLT_GEM5_SIMULATION_SCRIPT} ${simulation_script_option}" 
${SLTENV_GEM5_INSTALLATION_PATH}/${SLTENV_ISA}/gem5.${SLTENV_VARIANT} ${gem5_options} ${SLT_GEM5_SIMULATION_SCRIPT} ${simulation_script_option} 
status=$?

echo "Status for simulation ${status}"
if [[ ${status} -eq 0  ]] ; then 
#value=$(cat ${SLTENV_RESULTS_DIR}/stats.txt | grep "system.cpu.cpi" | grep -Eo "[[:digit:]]+\.[[:digit:]]{6}" )
value=$(cat ${SLTENV_RESULTS_DIR}/stats.txt | grep "system.cpu.ipc" | grep -Eo "[[:digit:]]+\.[[:digit:]]{6}" )
echo ${value} > ${fitness_file}
else  
echo "0.000" > ${fitness_file}
fi
echo "Fitness for ${program}"
echo ""
