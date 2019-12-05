#!/usr/bin/python3 -u

import subprocess
import logging
import os

from constants import LicenseConstants

def get_abaqus_tokens():
       cmd_to_run = [LicenseConstants.LMUTIL_PATH, 'lmstat', '-c', 
                     LicenseConstants.LICENSE_PATH, '-a']
       cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)

       with cmd_process.stdout as st:
            for line in iter(st.readline, b''):
                if b'Users of abaqus:' in line:
                    words = line.split()
                    total_tokens = int(words[5])
                    #used_tokens = int(words[10])
                    return total_tokens #, used_tokens
            return "cannot find any abaqus tokens in flex license manager"

def update_slurm_abaqus_tokens(total_tokens):
    cmd_to_run = ['scontrol', 'show', 'node',
                  f'{LicenseConstants.ABAQUS_CALC_SERVER}']
    cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)
    licenses = []
    with cmd_process.stdout as st:
        for line in iter(st.readline, b''):
            if b'Gres=' in line:
                line = line.decode().replace('\n', '')
                words = line.split('=')
                licenses = words[1]
                licenses = licenses.split(',')
                for i, l in enumerate(licenses):
                    if 'abaqus' in l:
                        l = l.split(':')
                        l[-1] = str(total_tokens)
                        l = ":".join(l)
                        licenses[i] = l                        
                        break
                licenses = ",".join(licenses)
                break
    if licenses:
        cmd_to_run = ['scontrol', 'update', 
                        f'nodename={LicenseConstants.ABAQUS_CALC_SERVER}', 
                        f'Gres={licenses}']            
        cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)

        with cmd_process.stdout as st:
            for line in iter(st.readline, b''):
                # this command should not return anything on success
                if line:
                    return line.decode()
                else:
                    return 0
    else:
        return "couldn't find any licenses to update"

if __name__ == "__main__":
    log_location = '/var/log'
    log_fname = 'SlurmLicenseManager.log'
    log_full_name = os.path.join(log_location, log_fname)
    logging.basicConfig(filename=log_full_name, 
                        format='%(asctime)s - %(message)s', 
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

    total_tokens = get_abaqus_tokens()

    if isinstance(total_tokens, int):
        answer = update_slurm_abaqus_tokens(total_tokens)
    else:
        answer = total_tokens
    if answer:
        logging.error(answer)
    else:
        logging.info(f'{total_tokens} tokens has been updated in slurm.')
