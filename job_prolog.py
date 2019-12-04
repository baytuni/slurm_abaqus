#!/usr/bin/python3 -u
import os
import subprocess
import socket
import logging

from constants import LicenseConstants

HOST = LicenseConstants.SLURM_CONTROL_SERVER 
PORT = LicenseConstants.LICENSE_MANAGER_PORT

log_fname = 'debug.log'
logging.basicConfig(filename=log_fname, 
                    format='%(asctime)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.info('Prolog started')
if 'SLURM_JOB_ID' in os.environ.keys():
    job_id = os.environ['SLURM_JOB_ID']
    logging.info(os.environ)
    job_partition = os.environ['SLURM_JOB_PARTITION']
    #ntasks = os.environ['SLURM_NTASKS']
    #cpus_per_task = os.environ['SLURM_CPUS_PER_TASK']
else:
    exit(0)


s = socket.socket()
s.connect((HOST, PORT))
s.send(bytes(f'REQUEST {job_id}','utf-8'))
response = s.recv(1024)
logging.info(response.decode())
if response.decode() == 'SUCCESS':
    pass
else:
    logging.info('REJECTED')
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