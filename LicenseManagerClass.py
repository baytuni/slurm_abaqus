import common
import subprocess
from dataclasses import dataclass

@dataclass
class SuspendedJobs:
    job_ids = []
    tokens_per_job = []
    partition_prios = []
    start_times = []


class LicenseManager:


    internal_tokens = 0
    total_tokens = 18
    running_tokens_per_job = []
    running_partition_prios = []
    running_job_ids = []
    running_start_times = []
    borrower_jobs = []
    borrowed_jobs = []
    SUCCESS = 0
    JOBNOTINRECORDS = 'Job is not in the records.'
    JOBALREADYINRECORDS = 'Job is already in the records.'
    NOTENOUGHTOKENS = 'Not enough tokens to grant.'


    def remove_jobs(self,job_id):
        if job_id in self.running_job_ids:
            ind = self.running_job_ids.index(job_id)
            self.running_job_ids.pop(ind)
            self.running_start_times.pop(ind)
            tokens = self.running_tokens_per_job.pop(ind)
            self.internal_tokens -= tokens
            if job_id in self.borrower_jobs:
                ind = self.borrower_jobs.index(job_id)
                self.borrower_jobs.pop(ind)
                suspended_jobs = self.borrowed_jobs.pop(ind)
                for i in range(len(suspended_jobs.job_ids)):
                    self.running_job_ids.append(suspended_jobs.job_ids[i])
                    self.running_tokens_per_job.append(
                                        suspended_jobs.tokens_per_job[i])
                    self.running_start_times.append(
                                        suspended_jobs.start_times[i])
                    self.running_partition_prios.append(
                                        suspended_jobs.partition_prios[i])
                    self.internal_tokens += self.running_tokens_per_job
            return self.SUCCESS

        else:
            return self.JOBNOTINRECORDS


    def add_jobs(self, job_id, tokens, partition_prio, start_time):
        if job_id in self.running_job_ids:
            self.running_tokens_per_job.append(tokens)
            self.running_partition_prios.append(partition_prio)
            self.running_job_ids.append(job_id)
            self.running_start_times.append(start_time)
            self.internal_tokens += tokens
            return self.SUCCESS
        else:
            return self.JOBALREADYINRECORDS
                


    def get_external_tokens(self):
        cmd_to_run = [common.LicenseConstants.LMUTIL_PATH, 'lmstat', '-c', 
                      common.LicenseConstants.LICENSE_PATH, '-a']
        cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)

        with cmd_process.stdout as st:
            for line in iter(st.readline, b''):
                if b'Users of abaqus:' in line:
                    words = line.split()
                    self.total_tokens = int(words[5])
                    return int(words[10])

    def grant_tokens(self, job_id, tokens, partition_prio, start_time):
        available_tokens = (self.total_tokens - self.get_external_tokens() 
                            - self.internal_tokens)
        if tokens <= available_tokens:
            self.add_jobs(job_id, tokens, partition_prio, start_time) 
            return self.SUCCESS
        else:
            return self.borrow_tokens(job_id, tokens, partition_prio, start_time)
        return self.NOTENOUGHTOKENS               

    def borrow_tokens(self,job_id,tokens,partition_prio,start_time):
        candidate_inds = []
        prio_sorted_indices = common.sorted_indicies(
                                self.running_partition_prios)
        for i in prio_sorted_indices:
            if self.running_partition_prios[i] < partition_prio:
                candidate_inds.append(i)

        tokens_released = 0
        release_inds = []

        token_sorted = common.sorted_indicies(self.running_start_times)
        for i in token_sorted:
            if i in candidate_inds:
                tokens_released += self.running_tokens_per_job[i]
                release_inds.append(i)
            if tokens_released >= tokens:
                self.borrower_jobs.append(job_id)
                suspended_jobs = SuspendedJobs()
                for j in release_inds:
                    suspended_jobs.job_ids.append(self.running_job_ids.pop(j))
                    suspended_jobs.tokens_per_job.append(
                                        self.running_tokens_per_job.pop(j))
                    suspended_jobs.partition_prios.append(
                                        self.running_partition_prios.pop(j))
                    suspended_jobs.start_times.append(
                                        self.running_start_times.pop(j))
                self.borrowed_jobs.append(suspended_jobs)
                self.internal_tokens -= tokens_released
                return self.add_jobs(job_id, tokens, partition_prio, 
                                        start_time) 
