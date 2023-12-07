import os
import subprocess
from typing import List, Optional

class Job:
    def __init__(self, job_name, job_string, parent_jobs = None):
        self.job_name = job_name
        self.job_string = job_string
        self.parent_jobs: Optional[List[Job]] = parent_jobs
        self.slurm_id = None

# Kinda need to know how jobs are dependent in the first place to know how to submit
# which imo defeats the purpose of using slurm dependencies? It just makes sure that
# one job finishes running before the next one starts. 
j1 = Job("j1", "sbatch --wrap='echo j1'")
j2 = Job("j2", "sbatch --wrap='echo j2'", [j1])
j3 = Job("j3", "sbatch --wrap='echo j3'", [j1])
j4 = Job("j4", "sbatch --wrap='echo j4'", [j2, j3])
j5 = Job("j5", "sbatch --wrap='echo j5'")
j6 = Job("j6", "sbatch --wrap='echo j6'", [j4, j5])

def run_job(job: Job) -> int:
    """Take a job and returns the slurm id for the corresponding job"""
    if job.parent_jobs:
        dependency_string = " --dependency=afterany:"
        for parent_job in job.parent_jobs:
            dependency_string += str(parent_job.slurm_id)
            dependency_string += ','
        job.job_string += dependency_string[:-1]
    result = subprocess.run(job.job_string, shell=True, capture_output=True, text=True)
    job.slurm_id = int(result.stdout.split(" ")[-1])
    return job.slurm_id

run_job(j1)
print(j1.slurm_id)
print(j1.job_string)

run_job(j2)
print(j2.slurm_id)
print(j2.job_string)

run_job(j3)
print(j3.slurm_id)
print(j3.job_string)

run_job(j4)
print(j4.slurm_id)
print(j4.job_string)