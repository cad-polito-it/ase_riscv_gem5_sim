#!/bin/bash

program=$1
echo "Evaluating ${program}"
UUID=$(basename "${program%.*}")
individual_folder=${SLTENV_UGP_INDIVIDUALS_FOLDER}/${UUID}
mkdir ${individual_folder}
mv ${program} ${individual_folder}


[[ ! "${individual_folder}/$UGP3_FITNESS_FILE" ]] && UGP3_FITNESS_FILE=${individual_folder}/fitness.out


#rm "${individual_folder}/$UGP3_FITNESS_FILE" 2>/dev/null || true


#${SLTENV_COMPILE_SCRIPT}
#-specs="nosys.specs" 
echo ""$SLTENV_CC_PATH"gcc -O2 -march=rv64gc -ggdb3 -mabi=lp64d  -I./include -I ${SLTENV_GEM5_SRC}/include/gem5/asm/generic -I ${SLTENV_GEM5_SRC}/include  -T./link.ld -nostdlib -nostartfiles  -static -Wall -Wextra -o "${individual_folder}/${UUID}.elf" -X  "${individual_folder}/${program}"  ${SLTENV_GEM5_SRC}/util/m5/src/abi/riscv/m5op.S"
"$SLTENV_CC_PATH"gcc -O2 -march=rv64gc -ggdb3 -mabi=lp64d  -I./include -I ${SLTENV_GEM5_SRC}/include/gem5/asm/generic -I ${SLTENV_GEM5_SRC}/include  -T./link.ld -nostdlib -nostartfiles  -static -Wall -Wextra -o "${individual_folder}/${UUID}.elf" -X  "${individual_folder}/${program}"  ${SLTENV_GEM5_SRC}/util/m5/src/abi/riscv/m5op.S  || exit 1


## maximize the system.cpu.ipc   0.112504   # IPC: Instructions Per Cycle ((Count/Cycle))
${SLTENV_EVALUATOR_SCRIPT} ${individual_folder}/${UUID}.elf ${individual_folder}/$UGP3_FITNESS_FILE

## fake evaluator (random number between 0 and 1)
#bc -l <<< "scale=3 ; ${RANDOM}/32767" > ${individual_folder}/$UGP3_FITNESS_FILE



cp -f ${individual_folder}/$UGP3_FITNESS_FILE ${SLTENV_WORK_DIR}
