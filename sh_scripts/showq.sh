#!/bin/bash
export SACCT_FORMAT="jobid,jobname,partition,avevmsize,avecpu,ntasks,alloccpus,elapsed,state,exitcode,TRESUsageInTot,TRESUsageOutTot"
sacct $@ --format=${SACCT_FORMAT}
