#!/bin/bash
#SBATCH -J testJob
#SBATCH -N 1
#SBATCH --begin=now
#SBATCH -J Abaqus_JOB-CHECKPOINT
#SBATCH --ntasks=2
#SBATCH --mem-per-cpu=2048
#SBATCH --open-mode=append
#SBATCH --time-min=00:02:00
###  Load the Environment
### In many cases you only need to worry about the following two lines
INPUT=SGT-800_C1_TM_IronHorse_Master_LIN_LC6
JOBNAME=$INPUT
FREQ=1
ABQVER=6142
###  Copying files to CHK folder (global scratch file system)
unset SLURM_GTIDS
CHK_DIR=/usrfem/Scratch_global
USRNAME=$(whoami)
TIMESTMP=$(date +%Y%m%d%H%M)
JOBNAME=${SLURM_JOB_ID}_${JOBNAME}_${USRNAME}
ABQDIR=/usrfem/femsys/abaqus/Commands
if ! [ -d $CHK_DIR/$JOBNAME ]; then
	mkdir $CHK_DIR/$JOBNAME
	cp $INPUT.inp $CHK_DIR/$JOBNAME/
fi

cd $CHK_DIR/$JOBNAME
if [[ -f Res_$INPUT.sta ]]; then
	rm -f *.lck
        $ABQDIR/abq${ABQVER} restartjoin originalodb=$INPUT restartodb=Res_$INPUT history
	for i in res mdl stt prt sim sta com cid 023 dat msg
	do
		mv Res_$INPUT.$i $INPUT.$i
	done
fi
###  Run the Parallel Program
if [[ -f $INPUT.sta ]]  || [[ -f Res_$INPUT.sta ]]; then
	echo "*Heading" > Res_$INPUT.inp
	cat $INPUT.sta | gawk -v freq=$FREQ '{if($3 !~/U/){print "*Restart, read, step="$1",inc="$2", write, overlay, frequency="freq}}' | tail -1 >> Res_$INPUT.inp
	 $ABQDIR/abq${ABQVER} job=Res_$JOBNAME input=Res_$INPUT.inp oldjob=$JOBNAME cpus=$SLURM_NTASKS -verbose 3 standard_parallel=all mp_mode=mpi interactive
else
	$ABQDIR/abq${ABQVER} job=$JOBNAME input=$INPUT.inp  cpus=$SLURM_NTASKS -verbose 3 standard_parallel=all  mp_mode=mpi interactive
fi
###  Transfer output files back to the project folder
cp *.dat $SLURM_SUBMIT_DIR/
cp *.msg $SLURM_SUBMIT_DIR/
cp *.sta $SLURM_SUBMIT_DIR/
