#!/bin/bash

################################################################################
#
#  author: Anna L.D. Latour (based on examples from Mate Soos)
#  e-mail: latour@nus.edu.sg
#  date: December 2022
#  project: Identifying Codes
#  call with: qsub encoding_gis_mpi_IC22.pbs
#  
################################################################################

EXPID="IC22"

export PROJECT_DIR="/home/projects/11000744/anna/identifying-codes"

INSTANCE_DIR="${PROJECT_DIR}/instances"
NETWORK_DIR="${PROJECT_DIR}/instances/networks"
SOFTWARE_DIR="${PROJECT_DIR}/software"
SCRIPTS_DIR="${PROJECT_DIR}/scripts"

RESULT_DIR="${PROJECT_DIR}/results/${EXPID}-encoding"

OUTPUT="out-ic"

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

# The sizes of maximum identifiable set that we want to run the experiment on:
k_array=("1 2 3 4 6 8 10 12 16")

encoding="gis"

declare -a config_arr=(
    " "
)

tlimit="3600"
memlimit="4000000"
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
#     "kaustav"
#     "geometric"
# )
# RESULT_DIR="${PROJECT_DIR}/results-test/${EXPID}-encoding"
# INSTANCE_DIR="${PROJECT_DIR}/instances-test"
# k_array=("10")
# tlimit="300"
################
# end testing
################

SERVER=$PBS_O_HOST
WORKDIR="scratch/${PBS_JOBID}_${OMPI_COMM_WORLD_RANK}"
sleep 0
sleep 0
OUTPUT="${OUTPUT}-${EXPID}-${PBS_JOBID}"
TMP_ENC_DIR="encoding"
TMP_INFILE_DIR="in"

# Needed to make the python script run properly:
export PBLIB_DIR="."   # We'll later copy pbencoder from /home/projects/11000744/software/ to here
export PYTHONPATH="${WORKDIR}/x86-64_linux"  # We'll later copy /home/projects/11000744/software/ILOG/cplex/python/3.5/x86-64_linux to ${WORKDIR}
export PYTHONPATH="/home/projects/11000744/software/ILOG/cplex/python/3.5/x86-64_linux/:${PYTHONPATH}"

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

cp ${PROJECT_DIR}/scripts/encoding/identifying_codes.py .
cp ${PROJECT_DIR}/scripts/encoding/ilp_encoding.py .
cp ${PROJECT_DIR}/scripts/encoding/gis_encoding.py .
cp ${PROJECT_DIR}/scripts/encoding/encode_network.py .
cp ${SOFTWARE_DIR}/pbencoder .

# Create list of files to process
files_arr=()
for subdir in ${networks_arr[@]}; do
    for network_file in ${NETWORK_DIR}/${subdir}/*; do
        if [[ $network_file == *.gz ]]; then
            files_arr+=( ${network_file} )
        fi
    done
done

echo "Created file list:"
for file in ${files_arr[@]}; do
    echo $file
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
mkdir -p ${TMP_ENC_DIR}
mkdir -p ${TMP_INFILE_DIR}
at_enc=0
at_cnfg=0
numjobs=0
mylinesperjob=0

# Create todo

echo "encoding ${encoding}"

# Create a directory to temporarily store the created cnf files, before we
# move them to a more appropriate directory. This is necessary because of
# the integration of the generation of encodings for different values of k
# inside the script

fin_out_dir="${OUTPUT}/${encoding}"
mkdir -p "${fin_out_dir}" || exit


for cnfg in "${config_arr[@]}"; do

    for file in ${files_arr[@]}; do

        for k in ${k_array[@]}; do
            mylinesperjob=0
            # Get network file name
            basefilename="$(basename -- ${file})"

            # Get the subdirectory in which to find the file
            parentdir="$(dirname ${file})"
            networktype="${parentdir%"${parentdir##*[!/]}"}" # extglob-free multi-trailing-/ trim
            networktype="${networktype##*/}"

            tmp_out_dir="${fin_out_dir}/config${at_cnfg}/k${k}/${networktype}"
            mkdir -p "${tmp_out_dir}" || exit


            # create dir on the server to store the script's output and the timeout files,
            # and to create the subdirectories for storing the cnf files generated by the script:
            echo "mkdir -p ${tmp_out_dir}" >> todo
            # create dir inside project directory to permanently store the script's output and timeout files
            echo "mkdir -p ${RESULT_DIR}/${encoding}/config${at_cnfg}/k${k}/${networktype}" >> todo
            # create dir inside project directory to permanently store the ilp encoding
            echo "mkdir -p ${INSTANCE_DIR}/${encoding}/config${at_cnfg}/k${k}/${networktype}" >> todo
            mylinesperjob=$((mylinesperjob+3))

            # Copy the input file to a temporary directory to avoid clashing servers (not sure if this is necessary)
            echo "cp $file ${TMP_INFILE_DIR}/${basefilename}" >> todo
            echo "gzip -d ${TMP_INFILE_DIR}/${basefilename}" >> todo
            mylinesperjob=$((mylinesperjob+2))

            basefilename="${basefilename%.*}"

            # Create base name for output files
            baseout="${OUTPUT}/${encoding}/config${at_cnfg}/k${k}/${networktype}/${basefilename}"
            encout="${basefilename}.gcnf"


            # Specify the command with which we will call the solver
            command="/usr/bin/time --verbose -o ${baseout}.timeout.out python encode_network.py --network ${TMP_INFILE_DIR}/${basefilename} --encoding ${encoding} -k ${k} --two_step --out_dir ${tmp_out_dir} --out_file ${encout} ${cnfg}"

            # ----------------------------------------------------------------------
            # Write some basic info to output file
            echo "echo \"c \" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c ==============================================================================\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c \" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Experiment info\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c ------------------------------------------------------------------------------\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Network:            ${basefilename}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Network type:       ${networktype}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c k:                  ${k}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Time limit:         ${tlimit} s\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Memory limit:       ${memlimit}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Encoding:           ${encoding}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Command:            ${command}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c \" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c \" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Admin\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c ------------------------------------------------------------------------------\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Date:               ${thedate}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c This file:          ${baseout}.encoder.out\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c EXPID:              ${EXPID}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c JOBID:              ${PBS_JOBID}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Project directory:  ${PROJECT_DIR}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Repository:         ${git_remote_url}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Branch:             ${git_branch}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c Commit:             ${git_commit_id}\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c \" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c ==============================================================================\" >> ${baseout}.encoder.out" >> todo
            echo "echo \"c \" >> ${baseout}.encoder.out" >> todo
            # ----------------------------------------------------------------------
            mylinesperjob=$((mylinesperjob+27))

            # Add call to todo list
            echo "${command} >> ${baseout}.encoder.out 2>&1" >> todo
            mylinesperjob=$((mylinesperjob+1))

            #copy back result
            echo "xz ${baseout}.encoder.out*" >> todo
            echo "xz ${baseout}.timeout*" >> todo
            echo "rm -f core.*" >> todo
            echo "rm -f ${TMP_INFILE_DIR}/${basefilename}" >> todo
            mylinesperjob=$((mylinesperjob+4))

            echo "mv ${baseout}.encoder.out* ${RESULT_DIR}/${encoding}/config${at_cnfg}/k${k}/${networktype}/" >> todo
            echo "mv ${baseout}.timeout* ${RESULT_DIR}/${encoding}/config${at_cnfg}/k${k}/${networktype}/"  >> todo
            mylinesperjob=$((mylinesperjob+2))

            echo "[ ! -f ${tmp_out_dir}/k${k}/${encout} ] || gzip ${tmp_out_dir}/k${k}/${encout} && mv ${tmp_out_dir}/k${k}/${encout}.gz ${INSTANCE_DIR}/${encoding}/config${at_cnfg}/k${k}/${networktype}/" >> todo
            mylinesperjob=$((mylinesperjob+1))
            numjobs=$((numjobs+1))
        done
    done
    let at_cnfg=at_cnfg+1
done


echo "Copying todo"
cp todo /home/projects/11000744/anna/identifying-codes/scripts/

# lines: 5+28+1+4+3 = 41
# mylinesperjob=41

# create per-core todos
echo "numjobs = ${numjobs}"
echo "numthreads = ${numthreads}"
numper=$((numjobs/numthreads))
echo "numper = ${numper}"
remain=$((numjobs-numper*numthreads))
echo "remain = ${remain}"
if [[ $remain -ge 1 ]]; then
    numper=$((numper+1))
    echo "(updated) numper = ${numper}"
fi
remain=$((numjobs-numper*(numthreads-1)))
echo "(updated) remain= ${remain}"

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
    echo "myi ${myi} has mystart ${mystart}"
    mystart=$((mystart + numper))
    echo "myi ${myi} has updated mystart ${mystart}"
    if [[ $myi -lt $((numthreads-1)) ]]; then
        echo "${myi} less than $((numthreads-1))"
        if [[ $mystart -gt $((numjobs+numper)) ]]; then
            echo "${mystart} greater than $((numjobs+numper))"
            sleep 0
        else
            echo "${mystart} lte $((numjobs+numper))"
            if [[ $mystart -lt $numjobs ]]; then
                echo "${mystart} less than ${numjobs}"
                myp=$((numper*mylinesperjob))
                mys=$((mystart*mylinesperjob))
                head -n $mys todo | tail -n $myp >> todo_$myi.sh
            else
                echo "${mystart} gte ${numjobs}"
                #we are at boundary, e.g. numjobs is 100, numper is 3, mystart is 102
                #we must only print the last numper-(mystart-numjobs) = 3-2 = 1
                mys=$((mystart*mylinesperjob))
                p=$(( numper-mystart+numjobs ))
                if [[ $p -gt 0 ]]; then
                    myp=$((p*mylinesperjob))
                    head -n $mys todo | tail -n $myp >> todo_$myi.sh
                fi
            fi
        fi
    else
        if [[ $remain -gt 0 ]]; then
            echo "remain ${remain} gt 0"
            mys=$((mystart*mylinesperjob))
            mr=$((remain*mylinesperjob))
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
rm -f pbencoder
rm -f identifying_codes.py
rm -f ilp_encoding.py
rm -f gis_encoding.py
rm -f encode_network.py
rm -rf x86-64_linux/
# rm -f todo*
cd ..
rm -f ${WORKDIR}

exit 0
