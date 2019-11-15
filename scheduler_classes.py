import os
import subprocess
import pickle
import common

class LicenseManager:

    internal_tokens = 0
    total_tokens = 18
    tokens_per_job = {}
    partition_prios = {}
    SUCCESS = 0
    FAIL = -1

    def get_external_tokens(self):
        cmd_to_run = [common.LicenseConstants.LMUTIL_PATH, 'lmstat', '-c', 
                      common.LicenseConstants.LICENSE_PATH, '-a']
        cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)

        with cmd_process.stdout as st:
            for line in iter(st.readline, b''):
                if b'Users of abaqus:' in line:
                    words = line.split()
                    self.total_tokens = words[5]
                    return int(words[10]) - self.internal_tokens

    def grant_tokens(jobid, tokens, partition_prio):
        available_tokens = (self.total_tokens - self.get_external_tokens() 
                            - self.internal_tokens):
        if tokens <= available_tokens:
            self.tokens_per_job[jobid] = tokens
            self.internal_tokens += tokens
            self.partition_prios[jobid] = partition_prio
            self.partition_prios = sorted(self.partition_prios.items(),
                                        key=lambda kv: kv[1])
            return self.SUCCESS
        else:
            sorted()
            for prio in self.partition_prios.values():
                if prio 

            return self.FAIL

class Jobs:
    
    job_ids = []
    partition_prios = []
    tokens_used = []

    def add_job(self, jobid, partition_prio, tokens):
        self.job_ids.append(jobid)
        self.partition_prios.append(partition_prio)
        self.tokens_used.apend(tokens)
    
