#!/usr/bin/env python3

import os
import subprocess
import pickle
import common

import socket

class LicenseManager:

    internal_tokens = 0
    total_tokens = 18
    tokens_per_job = []
    partition_prios = []
    job_ids = []
    start_times = []
    SUCCESS = 0
    FAIL = -1

    def add_jobs(self, job_id, tokens, partition_prio, start_time):
        self.tokens_per_job.append(tokens)
        self.partition_prios.append(partition_prio)
        self.job_ids.append(job_id)
        self.start_times.append(start_time)
        self.internal_tokens += tokens


    def get_external_tokens(self):
        cmd_to_run = [common.LicenseConstants.LMUTIL_PATH, 'lmstat', '-c', 
                      common.LicenseConstants.LICENSE_PATH, '-a']
        cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)

        with cmd_process.stdout as st:
            for line in iter(st.readline, b''):
                if b'Users of abaqus:' in line:
                    words = line.split()
                    self.total_tokens = int(words[5])
                    return int(words[10]) - self.internal_tokens

    def grant_tokens(self, job_id, tokens, partition_prio, start_time):
        available_tokens = (self.total_tokens - self.get_external_tokens() 
                            - self.internal_tokens)
        if tokens <= available_tokens:
            self.add_jobs(job_id, tokens, partition_prio, start_time) 
            return self.SUCCESS
        else:
           candidate_inds = []
           prio_sorted_indices = common.sorted_indicies(self.partition_prios)
           for i in prio_sorted_indices:
               if self.partition_prios[i] < partition_prio:
                   candidate_inds.append(i)
           token_sorted = common.sorted_indicies(self.tokens_per_job)
           tokens_released = 0
           release_inds = []
           for i in token_sorted:
               if i in candidate_inds:
                   tokens_released += self.tokens_per_job[i]
                   release_inds.append(i)
               if tokens_released >= tokens:
                    for j in release_inds:
                        self.job_ids.pop(j)
                        self.tokens_per_job.pop(j)
                        self.partition_prios.pop(j)
                    self.internal_tokens -= tokens_released
                    self.add_jobs(job_id, tokens, partition_prio, start_time) 
                    return self.SUCCESS
        return self.FAIL               



if __name__ == "__main__":
    HOST = socket.gethostname()
    PORT = 65432
    s = socket.socket()
    s.bind((HOST, PORT))
    s.listen()
    conn, _ = s.accept()
    license_manager = LicenseManager()
    while True:
#        try:
            args = conn.recv(1024)
            args = args.decode().split()
            job_id = args[0]
            tokens = int(args[1])
            partition_prio = int(args[2])
            start_time = int(args[3])
            print(job_id, tokens, partition_prio, start_time)
            print(license_manager.internal_tokens, license_manager.total_tokens)
            license_manager.grant_tokens(job_id, tokens, partition_prio, 
                                        start_time)
#        except:
#            s.close()
#            break

    s.close()

