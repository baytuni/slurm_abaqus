#!/usr/bin/env python3
import os
from scheduler_classes import LicenseManager
import common
import subprocess


if __name__ == "__main__":
    if 'SLURM_JOB_ID' in os.environ.keys():
        job_name = os.environ['SLURM_JOB_ID']
        job_partition = os.environ['SLURM_JOB_PARTITION']
    else:
        exit(0)


    cmd_to_run = ['scontrol', 'show', 'partition=' + job_partition]
    cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)
    partition_prio = 0
    with cmd_process.stdout as st:
        for line in iter(st.readline, b''):
            if b'PriorityTier' in line:
                words = line.split()
                word = words[1].split('=')
                partition_prio = int(word[1])
    print ('Test')
    print('print ' + 'partition priority=' + partition_prio)
    exit(0)