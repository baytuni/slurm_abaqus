#!/usr/bin/python3 -u

import subprocess

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

def update_slurm_abaqus_tokens(total_tokens):
    cmd_to_run = ['scontrol', 'show', 'node',
                  f'{LicenseConstants.ABAQUS_CALC_SERVER}']
    cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)
    licenses = []
    print(str(total_tokens))
    with cmd_process.stdout as st:
        for line in iter(st.readline, b''):
            print(line)
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

if __name__ == "__main__":
    total_tokens = get_abaqus_tokens()
    update_slurm_abaqus_tokens(total_tokens)