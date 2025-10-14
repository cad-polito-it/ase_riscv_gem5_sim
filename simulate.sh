#!/bin/bash

usage () {
	echo "simulate a riscv cpu with gem5"
	echo "./simulate.sh [OPTIONS]"
	echo "OPTIONS: "
	echo "-s path to the setup file (default ./setup_default)"
	echo "-i path to program folder"
	echo "-gui|-nogui (mutually exclusive) the gem5 is|not going to be visuallized by the pipeline visualizer"
	echo ""
	echo "Example: "
	echo "./simulate.sh ./programs/my_fancy_c_benchmark -nogui"
	echo "it will search in the folder ./programs/my_fancy_c_benchmark"
	echo "for a recipe in a Makefile to compile, and create an executable file called my_fancy_c_benchmark.elf."
	echo "Afterward, it executed the architectural simulation with gem5."
	 
}

## arguments parsing 
use_gui=false
program_folder=""
program_folder_opt=false
interactive=true
setup_file="./setup_default"
## GET OPTIONS
while test $# -gt 0; do
case "$1" in 
-i) 
if  ${program_folder_opt} ; then 
echo -e "\e[31mRedundant -i program folder arguments \e[0m"
exit 1
fi 
shift 
if [[ $# -gt 0  &&  ! $1 =~ ^- ]]; then
   program_folder=$1
   program_folder_opt=true 
else
  echo -e "\e[31m-i: no argument specified \e[0m"
  exit 1
fi
interactive=false
shift
;;
-gui)
use_gui=true
interactive=false
shift 
;;
-nogui)
use_gui=false
interactive=false
shift 
;;
-s|--setup)
shift
if [[ $# -gt 0  &&  ! $1 =~ ^- ]]; then
   setup_file=$1
   if [[ ! -f "${setup_file}" ]] ; then
   echo -e "\e[31mERROR:Setup file ${setup_file} not found \e[0m" 
   exit 1
   fi
fi
shift
# let's keep the script still interactive
interactive=true
;;
*|-h|help|--help|-help)
usage
exit 0 
;;

esac 
done 


if ${interactive} ; then

programs=`find ./programs/ -mindepth 1 -maxdepth 1  -type d  | xargs -I{}  basename {} | sort`

if [ -z "${programs}" ]; then
echo -e "\e[31mNo programs in your workspace.\e[0m" >&2
exit 1
fi
echo "Select an program in programs:"
select program in ${programs}; do
if [ -z "${program}" ]; then
echo "wrong choice" >&2
else
break
fi
done	
program_folder=./programs/${program}
program_folder_opt=true


# ask for intersections
read -p "Use GUI [yN]: " -n 1 -r
[[ $REPLY =~ ^[Yy]$ ]] && use_gui=true || use_gui=false
echo

fi # interactive

if ! ${program_folder_opt} ; then 
echo -e "\e[31mError in specifying the program folder\e[0m"
usage
exit 1
fi 

# sourcing what you need
source ${setup_file}

export program_folder
export program=$(basename ${program_folder})
echo "Simulating ${program}"


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
	echo -e "\e[31mCompilation error\e[0m"
	exit 1
fi 
fi 
cd ${WORK_DIR}

echo "Simulating program ${program}"

if ${GEM5_CPU_IN_ORDER} ; then

gem5_options="--debug-flags=MinorGUI --outdir=${RESULTS_DIR}/${program}/ --verbose "
simulation_script_option="--caches  --cpu-type MinorCPU --l1d_size 8388608 --l1i_size 8388608 --cacheline_size 512 --cpu-clock 1MHz --sys-clock 10GHz -c ${program_folder}/${program}.elf    "   #--directory=${RESULTS_DIR}/${program}

echo "${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option}" 
${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option} | tee ${RESULTS_DIR}/${program}/gem5_inorder.log

trace_out_file=${RESULTS_DIR}/${program}/gem5_inorder.log
else
# OoO CPU
gem5_options="--debug-flags=O3PipeView,O3CPUAll  --debug-file=${RESULTS_DIR}/${program}/trace.out --outdir=${RESULTS_DIR}/${program}/ --verbose "
simulation_script_option="--caches  -c ${program_folder}/${program}.elf --directory=${RESULTS_DIR}/${program}  --errout=${RESULTS_DIR}/${program}/programm.err "  

echo "${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option}" 
${GEM5_INSTALLATION_PATH}/${GEM5_ISA}/gem5.${GEM5_VARIANT} ${gem5_options} ${GEM5_SIMULATION_SCRIPT} ${simulation_script_option} 

trace_out_file=${RESULTS_DIR}/${program}/trace.out
fi

if [[ $? -ne 0 ]] ; then 
	echo -e "\e[31mSimulation error\e[0m"
	exit 1
fi

# Launch Pipeline visualizer
if ${use_gui}; then
	echo "${PIPELINE_VISUALIZER} ${trace_out_file}"
	${PIPELINE_VISUALIZER} ${trace_out_file} 2> /dev/null
fi

