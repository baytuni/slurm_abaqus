#!/usr/bin/env python3
import os
import common
import subprocess
import socket

HOST = socket.gethostname()
PORT = 65432

if __name__ == "__main__":


    if 'SLURM_JOB_ID' in os.environ.keys():
        job_name = os.environ['SLURM_JOB_ID']
        job_partition = os.environ['SLURM_JOB_PARTITION']
        #ntasks = os.environ['SLURM_NTASKS']
        #cpus_per_task = os.environ['SLURM_CPUS_PER_TASK']
        print(os.environ)
    else:
        exit(0)
   

    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(b'REQUEST 435 6 1 2019-11-19T09:12:51')
    response = s.recv(1024)
    print(response.decode())
    if response.decode() == 'SUCCESS':
        print('ACCEPTED')
    else:
        print('REJECTED')
    s.close()


    """ cmd_to_run = ['scontrol', 'show', 'partition=' + job_partition]
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
    exit(0) """