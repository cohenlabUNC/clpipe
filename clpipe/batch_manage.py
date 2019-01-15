import click
import json
from pkg_resources import resource_stream
import os
import sys
class BatchManager:

    def __init__(self, batchsystemConfig):
        self.jobs = []
        self.config = json.load(resource_stream(__name__, "batchConfigs/" + batchsystemConfig))
        self.submissionlist = []


    def addjob(self, job):
        self.jobs.append(job)

    def compilejobstrings(self):
        header = self.createsubmissionhead()
        for job in self.jobs:
            self.submissionlist.append(header.format(jobid =job.jobID) + '"'+ job.jobString+'"')

    def createsubmissionhead(self):
        head = []
        head.append(self.config['SubmissionHead'])
        for e in self.config['SubmissionOptions']:
            temp = e['command']+' '+e['args']
            head.append(temp)
        for e in self.config['SubOptionsEqual']:
            temp = e['command'] + '=' + e['args']
            head.append(temp)
        head.append(self.config['JobIDCommand']+'='+'{jobid}')
        head.append(self.config['OutputCommand']+'='+'Output-{jobid}.out')
        head.append(self.config['CommandWrapper']+'=')
        return " ".join(head)

    def submit_jobs(self):
        for job in self.submissionlist:
            os.system(job)

    def print_jobs(self):
        for job in self.submissionlist:
            click.echo(job)

class Job:

    def __init__(self, jobID, jobString):
        self.jobID = jobID
        self.jobString = jobString