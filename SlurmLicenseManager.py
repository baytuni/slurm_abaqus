#!/usr/bin/python3 -u

import os
import sys
from LicenseManagerClass import LicenseManager
import time
import socket
import logging

log_location = '/var/log'
#log_location = '.'
log_fname = 'SlurmLicenseManager.log'
log_full_name = os.path.join(log_location, log_fname)
logging.basicConfig(filename=log_full_name, 
                    format='%(asctime)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
HOST = socket.gethostname()
PORT = 65432

s = socket.socket()
logging.info('Socket Created')
s.bind((HOST, PORT))
logging.info('Socket bound to port:' + str(PORT))
s.listen()
logging.info('License Manager is listening')
license_manager = LicenseManager()
while True:
    try:
        conn, addrs = s.accept()
        if addrs[0] != socket.gethostbyname(HOST):
            logging.warning('Only connections from the head node allowed.')
            logging.error(f'{addrs[0]}, {socket.gethostbyname(HOST)}')
            conn.send(bytes('Connection not allowed'))
            conn.close()
            continue
            
        logging.info(f'Connection from {addrs} has been established.')
        args = conn.recv(1024)
        args = args.decode().split()
        request_type = args[0]
        job_id = args[1]
        #tokens = int(args[2])
        #partition_prio = int(args[3])
        #start_time = args[4]
        #start_time = time.strptime(start_time,'%Y-%m-%dT%H:%M:%S')

        if request_type == 'REQUEST':
            logging.info(f'License Request has been received')
            print(license_manager.internal_tokens, 
                    license_manager.total_tokens)
            answer = license_manager.grant_tokens(job_id) 
            if answer == license_manager.SUCCESS:
                conn.send(b'SUCCESS')
                logging.info(f'{tokens} tokens granted for jobid={job_id}.\n'
                              f'Currently {license_manager.internal_tokens}'
                              f' tokens are being used out of '
                              f'{license_manager.total_tokens}')
            else:
                conn.send(bytes(answer,'utf8'))
                logging.warning(f'License denied for jobid={job_id}. {answer}')
        elif request_type == 'REMOVE':
                answer = license_manager.remove_jobs(job_id)
                if answer == license_manager.SUCCESS:
                    logging.info(f'jobid={job_id} removed, licenses are released')
                    conn.send(b'SUCCESS')
                else:
                    logging.warning(f'jobid={job_id} doesn\'t exist in the records')
                    conn.send(bytes(answer,'utf8')) 

        conn.close()
    except(KeyboardInterrupt,SystemExit,SystemError):
        logging.info('Closing the socket')
        s.close()
        break
    except:
        logging.error('Unexpected error:' + sys.exc_info()[0])
        break
        

s.close()
exit(0)

