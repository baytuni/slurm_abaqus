from constants import AbaqusConstants, LicenseConstants
import subprocess
import time
from math import floor


def sorted_indicies(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)


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
    JOBDOESNTEXIST = 'Job doesn\'t exist'
    PARTITIONDOESNTEXIST = 'Partition doesn\'t exist'

    def calculate_abaqus_tokens(self, ncpus):
        return floor(5 * ncpus ** 0.422)

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
                    runnable_job_id = suspended_jobs.job_ids[i]
                    runnable_job_tokens = suspended_jobs.tokens_per_job[i] 
                    answer = self.reserve_release_tokens(runnable_job_id, 
                                                        runnable_job_tokens)
                    if answer != self.SUCCESS:
                        continue
                    self.running_job_ids.append(runnable_job_id)
                    self.running_tokens_per_job.append(runnable_job_tokens)
                    self.running_start_times.append(
                                        suspended_jobs.start_times[i])
                    self.running_partition_prios.append(
                                        suspended_jobs.partition_prios[i])
                    self.internal_tokens += self.running_tokens_per_job

            return self.SUCCESS
        else:
            return self.JOBNOTINRECORDS


    def add_jobs(self, job_id, tokens, partition_prio, start_time):
        self.running_tokens_per_job.append(tokens)
        self.running_partition_prios.append(partition_prio)
        self.running_job_ids.append(job_id)
        self.running_start_times.append(start_time)
        self.internal_tokens += tokens

    def get_external_tokens(self):
        cmd_to_run = [LicenseConstants.LMUTIL_PATH, 'lmstat', '-c', 
                      LicenseConstants.LICENSE_PATH, '-a']
        cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)

        with cmd_process.stdout as st:
            for line in iter(st.readline, b''):
                if b'Users of abaqus:' in line:
                    words = line.split()
                    self.total_tokens = int(words[5])
                    return int(words[10])

    def grant_tokens(self, job_id):
        if (job_id in self.running_job_ids):
            return self.JOBALREADYINRECORDS

        job_dict = self.read_jobs(job_id)
        start_time = job_dict['SubmitTime']
        start_time = time.strptime(start_time,'%Y-%m-%dT%H:%M:%S')
        partition_name = job_dict['Partition']
        partition_prio = self.get_partition_prio(partition_name)
        ntasks = int(job_id['NumTasks'])
        tokens = self.calculate_abaqus_tokens(ntasks)
    
        available_tokens = (self.total_tokens - self.get_external_tokens())

        if tokens <= available_tokens:            
            self.add_jobs(job_id, tokens, partition_prio, start_time) 
            return self.reserve_release_tokens(tokens,job_id)
        else:
            return self.borrow_tokens(job_id, tokens, partition_prio, 
                                      start_time)

    def borrow_tokens(self,job_id,tokens_needed,partition_prio,start_time):
        #Collect low prio job indices in candidate_inds
        candidate_inds = []
        prio_sorted_indices = sorted_indicies(
                                self.running_partition_prios)
        for i in prio_sorted_indices:
            if self.running_partition_prios[i] < partition_prio:
                candidate_inds.append(i)

        # Sort using start times because slurm does the same
        releasable_tokens = 0
        released_tokens = 0
        release_inds = []
        time_sorted_inds = sorted_indicies(self.running_start_times)
        for i in time_sorted_inds:
            if i in candidate_inds:
                releasable_tokens += self.running_tokens_per_job[i]
                release_inds.append(i)

        if releasable_tokens >= tokens_needed:
            self.borrower_jobs.append(job_id)
            suspended_jobs = SuspendedJobs()
            for j in release_inds:
                suspended_job_id = self.running_job_ids.pop(j)
                answer = self.reserve_release_tokens(suspended_job_id) 
                if answer != self.SUCCESS:
                    continue

                suspended_jobs.job_ids.append(suspended_job_id)
                popped_tokens = self.running_tokens_per_job.pop(j)
                suspended_jobs.tokens_per_job.append(popped_tokens)
                suspended_jobs.partition_prios.append(
                                self.running_partition_prios.pop(j))
                suspended_jobs.start_times.append(
                                    self.running_start_times.pop(j))
                released_tokens += popped_tokens
                if releasable_tokens >= tokens_needed:
                    break

            self.borrowed_jobs.append(suspended_jobs)
            self.internal_tokens -= released_tokens

            self.add_jobs(job_id, tokens_needed, partition_prio, start_time) 
            return self.SUCCESS
        else:
            return self.NOTENOUGHTOKENS
    
    def reserve_release_tokens(self, tokens, job_id=0):
        license_line = (LicenseConstants.SACCT_ABAQUS_LICENSE_SERVER_STRING +
                        f':{tokens}')
        cmd_to_run = ['scontrol', 'update', f'jobid={job_id}',
                       f'Licenses={license_line}']
        cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)

        with cmd_process.stdout as st:
            for line in iter(st.readline, b''):
                # this command should not return anything on success
                if line:
                    return line.decode()
                else:
                    return self.SUCCESS        

    def read_jobs(self, job_id):
        job_dict = self.scontrol_to_dict('job', job_id)
        if job_dict:
            return job_dict
        else:
            return self.JOBDOESNTEXIST

    def get_partition_prio(self,partition_name):
        partition_dict = self.scontrol_to_dict('partition', partition_name)
        if partition_dict:
            return int(partition_dict['PriorityTier'])
        else:
            return self.PARTITIONDOESNTEXIST

    def scontrol_to_dict(self,entity,name):
        cmd_to_run = ['scontrol', 'show', f'{entity}', f'{name}']
        cmd_process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE)
        return_dict = {}
        shell_output = cmd_process.stdout.read()
        properties = shell_output.decode().replace('\n','').split()
        for p in properties:
            if p:
                p = p.split('=')
                key = p[0]
                value = p[1]
                return_dict[key] = value
        return return_dict 

