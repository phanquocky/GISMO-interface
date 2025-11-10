#!/bin/bash

################################################################################
#
#  author: Anna Latour (based on examples from Mate Soos)
#  e-mail: latour@nus.edu.sg
#  date: January 2023
#  project: Identifying Codes
#  call with: qsub cplex_mpi_IC25.pbs
#
################################################################################

EXPID="IC25"

PROJECT_DIR="/home/projects/11000744/anna/identifying-codes"

ILP_DIR="${PROJECT_DIR}/instances/ilp"
SOFTWARE_DIR="${PROJECT_DIR}/software"
SCRIPTS_DIR="${PROJECT_DIR}/scripts"

RESULT_DIR="${PROJECT_DIR}/results/${EXPID}-ilp"
OUTPUT="out-ic"
TMP_INFILE_DIR="in"

# The network types that we want to run an experiment on:
networks_arr=(
    "geometric"
    "kaustav"
    "collaboration"
    "infrastructure"
    "power"
    "road"
    "social"
    "webgraph"
)

# The sizes of maximum identifable set that we want to run the experiment on:
k_array=("1 2 3 4 6 8 10 12 16")
config_arr=( 
    ""
)
ilp_config_arr=(
    "config1"
    "config0"
)

tlimit="7200"
cplex_tlimit="7200"
memlimit="4000000"      # Maximum virtual memory for processes, in kilobytes TODO: should this be set to a different value?
numthreads=$((OMPI_COMM_WORLD_SIZE))

ulimit -t unlimited
shopt -s nullglob

# Initialise todo list of jobs to run
rm -f todo
touch todo

################
# testing
################
# networks_arr=(
#     "misc"
#     "kaustav"
#     "infrastructure"
# )
# k_array=( "1" "2")
# RESULT_DIR="${PROJECT_DIR}/results-test/${EXPID}-ilp"
# tlimit="30"
# cplex_tlimit="30"
################
# end testing
################

SERVER=$PBS_O_HOST
WORKDIR="scratch/${PBS_JOBID}_${OMPI_COMM_WORLD_RANK}"
sleep 0
sleep 0
OUTPUT="${OUTPUT}-${EXPID}-${PBS_JOBID}"

# Collect some basic info
thedate=`date "+%Y-%m-%d"`
git_remote_url="$(git --git-dir ${PROJECT_DIR}/.git config --get remote.origin.url)"
git_commit_id="$(git --git-dir ${PROJECT_DIR}/.git log --format="%H" -n 1)"
git_branch="$(git --git-dir ${PROJECT_DIR}/.git rev-parse --abbrev-ref HEAD)"

echo ------------------------------------------------------
echo "Job is running on node ${PBS_NODEFILE}"
echo ------------------------------------------------------
echo "Rank is: ${OMPI_COMM_WORLD_RANK}"
echo "PBS: qsub is running on $PBS_O_HOST"
echo "PBS: originating queue is $PBS_O_QUEUE"
echo "PBS: executing queue is $PBS_QUEUE"
echo "PBS: working directory is $PBS_O_WORKDIR"
echo "PBS: execution mode is $PBS_ENVIRONMENT"
echo "PBS: job identifier is ${PBS_JOBID}"
echo "PBS: job name is $PBS_JOBNAME"
echo "PBS: node file is $PBS_NODEFILE"
echo "PBS: current home directory is $PBS_O_HOME"
echo "PBS: PATH = $PBS_O_PATH"
echo "server      is ${SERVER}"
echo "workdir     is ${WORKDIR}"
echo "servpermdir is ${SERVPERMDIR}"
echo "Output dir  is ${OUTPUT}"

echo "Transferring files from server to compute node"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}" || exit

cp ${SOFTWARE_DIR}/timeout .


# Create list of files to process
files_arr=()
for ilp_config in ${ilp_config_arr}; do
    for k in ${k_array[@]}; do
        for subdir in ${networks_arr[@]}; do
            for ilp_file in ${ILP_DIR}/${ilp_config}/k${k}/${subdir}/*; do
                if [[ $ilp_file == *.gz ]]; then
                    files_arr+=( ${ilp_file} )
                fi
            done
        done
    done
done
files_arr=( $(shuf --random-source=<(yes 42) -e "${files_arr[@]}") )

echo "Shuffled file list:"
for file in ${files_arr[@]}; do
    echo $file
done

# Create todo list of jobs to run
rm -f todo
touch todo
mkdir -p ${OUTPUT}
mkdir -p ${TMP_INFILE_DIR}
at_config=0
numjobs=0
linesperjob=0

# Create todo

for file in ${files_arr[@]}; do
    echo "file ${file}"
    linesperjob=0
    # Get network file name
    basefilename="$(basename -- ${file})"

    # Get the subdirectory in which to find the file
    parentdir="$(dirname ${file})"
    networktype="${parentdir%"${parentdir##*[!/]}"}" # extglob-free multi-trailing-/ trim
    networktype="${networktype##*/}"
    k_dir="$(dirname ${parentdir})"
    k="${k_dir##*/}"
    k="${k:1}"
    ilp_configdir="$(dirname ${k_dir})"
    ilp_config="${ilp_configdir##*/}"

    tmp_fin_dir="${TMP_INFILE_DIR}/${ilp_config}/k${k}/${networktype}"
    echo "creating directory ${tmp_fin_dir}."
    if [ ! -d "${tmp_fin_dir}" ]; then
        mkdir -p "${tmp_fin_dir}" || exit
    fi

    # create dir on server to temporarily store script output files and timeout files
    echo "mkdir -p ${OUTPUT}/${ilp_config}/k${k}/${networktype}" >> todo
    # create dir in project directory to permanently store script output files and timeout files
    echo "mkdir -p ${RESULT_DIR}/${ilp_config}/k${k}/${networktype}/" >> todo
    # copy input file to the server
    echo "cp ${file} ${tmp_fin_dir}/${basefilename}" >> todo
    echo "gzip -d ${tmp_fin_dir}/${basefilename}" >> todo
    linesperjob=$((linesperjob+4))

    basefilename="${basefilename%.*}"
        
    # Create base name for output files
    baseout="${OUTPUT}/${ilp_config}/k${k}/${networktype}/${basefilename}"

    # Create CPLEX running script
    cplex_input="${tmp_fin_dir}/${basefilename}.opl"
    rm -f $cplex_input
    touch $cplex_input
    echo "read \"${tmp_fin_dir}/${basefilename}\";" >> $cplex_input
    echo "set workmem 4096" >> $cplex_input
    echo "set timelimit 7200" >> $cplex_input
    echo "opt" >> $cplex_input
    echo "display solution variables -" >> $cplex_input
    echo "display solution objective" >> $cplex_input

    # Specify the command with which we will call the solver
    command="/usr/bin/time --verbose -o ${baseout}.timeout.out /home/projects/11000744/software/ILOG/cplex/bin/x86-64_linux/cplex -f ${cplex_input}"

    # ----------------------------------------------------------------------
    # Write some basic info to output file
    echo "echo \"c \" >> ${baseout}.solver.out" >> todo
    echo "echo \"c ==============================================================================\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c \" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Experiment info\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c ------------------------------------------------------------------------------\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Benchmark:          ${basefilename}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Networktype:        ${networktype}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c k:                  ${k}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Time limit:         ${tlimit}s\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Memory limit:       ${memlimit}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c ILP configuration:  ${ilp_config}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Encoding:           independent support\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Command:            ${command}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c \" >> ${baseout}.solver.out" >> todo
    echo "echo \"c \" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Admin\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c ------------------------------------------------------------------------------\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Date:               ${thedate}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c This file:          ${baseout}.solver.out\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c EXPID:              ${EXPID}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c JOB_ID:             ${PBS_JOBID}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Project directory:  ${PROJECT_DIR}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Repository:         ${git_remote_url}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Branch:             ${git_branch}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c Commit:             ${git_commit_id}\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c \" >> ${baseout}.solver.out" >> todo
    echo "echo \"c ==============================================================================\" >> ${baseout}.solver.out" >> todo
    echo "echo \"c \" >> ${baseout}.solver.out" >> todo
    # ----------------------------------------------------------------------
    linesperjob=$((linesperjob+28))

    # Add call to todo list
    echo "${command} >> ${baseout}.solver.out 2>&1" >> todo
    linesperjob=$((linesperjob+1))

    #copy back result
    echo "xz ${baseout}.solver.out*" >> todo
    echo "xz ${baseout}.timeout*" >> todo
    echo "rm -f core.*" >> todo
    echo "rm -f ${basefilename}*" >> todo
    echo "rm -f ${tmp_fin_dir}/${basefilename}" >> todo
    linesperjob=$((linesperjob+5))

    echo "mv ${baseout}.solver.out* ${RESULT_DIR}/${ilp_config}/k${k}/${networktype}/" >> todo
    echo "mv ${baseout}.timeout* ${RESULT_DIR}/${ilp_config}/k${k}/${networktype}/"  >> todo
    linesperjob=$((linesperjob+2))

    numjobs=$((numjobs+1))
done

echo "Copying todo"
cp todo /home/projects/11000744/anna/identifying-codes/scripts/

# lines: 3+28+1+5+2 = 39
# linesperjob=39

# create per-core todos
echo "Lines per job: ${linesperjob}"
echo "numjobs: ${numjobs}"

numper=$((numjobs/numthreads))
remain=$((numjobs-numper*numthreads))
if [[ $remain -ge 1 ]]; then
    numper=$((numper+1))
fi
remain=$((numjobs-numper*(numthreads-1)))

mystart=0
for ((myi=0; myi < numthreads ; myi++))
do
    rm -f todo_$myi.sh
    touch todo_$myi.sh
    echo "#!/bin/bash" > todo_$myi.sh
    echo "ulimit -t $tlimit" >> todo_$myi.sh
    echo "ulimit -v $memlimit" >> todo_$myi.sh
    echo "ulimit -c 0" >> todo_$myi.sh
    echo "set -x" >> todo_$myi.sh
    typeset -i myi
    typeset -i numper
    typeset -i mystart
    mystart=$((mystart + numper))
    if [[ $myi -lt $((numthreads-1)) ]]; then
        if [[ $mystart -gt $((numjobs+numper)) ]]; then
            sleep 0
        else
            if [[ $mystart -lt $numjobs ]]; then
                myp=$((numper*linesperjob))
                mys=$((mystart*linesperjob))
                head -n $mys todo | tail -n $myp >> todo_$myi.sh
            else
                #we are at boundary, e.g. numjobs is 100, numper is 3, mystart is 102
                #we must only print the last numper-(mystart-numjobs) = 3-2 = 1
                mys=$((mystart*linesperjob))
                p=$(( numper-mystart+numjobs ))
                if [[ $p -gt 0 ]]; then
                    myp=$((p*linesperjob))
                    head -n $mys todo | tail -n $myp >> todo_$myi.sh
                fi
            fi
        fi
    else
        if [[ $remain -gt 0 ]]; then
            mys=$((mystart*linesperjob))
            mr=$((remain*linesperjob))
            head -n $mys todo | tail -n $mr >> todo_$myi.sh
        fi
    fi
    echo "exit 0" >> todo_$myi.sh
    chmod +x todo_$myi.sh
done
# echo "Done."

# Execute todos
echo "This is MPI exec number $OMPI_COMM_WORLD_RANK"
rm -f ${OUTPUT}/out_${OMPI_COMM_WORLD_RANK}
./todo_${OMPI_COMM_WORLD_RANK}.sh > ${OUTPUT}/out_${OMPI_COMM_WORLD_RANK}
echo "Finished waiting $OMPI_COMM_WORLD_RANK"

# Clean up
rm -f timeout
rm -f todo*
cd ..
rm -f ${WORKDIR}

exit 0
