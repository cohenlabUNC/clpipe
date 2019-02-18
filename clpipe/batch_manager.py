import click
import json
from pkg_resources import resource_stream
import os
import sys



class BatchManager:

    def __init__(self, batchsystemConfig, outputDirectory=None):
        self.jobs = []
        self.config = json.load(resource_stream(__name__, "batchConfigs/" + batchsystemConfig))
        self.submissionlist = []
        if outputDirectory is None:
            outputDirectory = '.'
        self.outputDir = outputDirectory
        if not os.path.isdir(outputDirectory):
            os.makedirs(outputDirectory)

    def update_mem_usage(self, mem_use):
        self.config['MemoryDefault'] = mem_use

    def update_time(self, time):
        self.config['TimeDefault'] = time

    def update_nthreads(self, threads):
        self.config['NThreads'] = threads

    def addjob(self, job):
        self.jobs.append(job)

    def compilejobstrings(self):
        header = self.createsubmissionhead()
        for job in self.jobs:
            self.submissionlist.append(header.format(jobid=job.jobID) + '"' + job.jobString + '"')

    def createsubmissionhead(self):
        head = [self.config['SubmissionHead']]
        for e in self.config['SubmissionOptions']:
            temp = e['command'] + ' ' + e['args']
            head.append(temp)
        for e in self.config['SubOptionsEqual']:
            temp = e['command'] + '=' + e['args']
            head.append(temp)

        head.append(self.config['MemoryCommand'] + self.config['MemoryDefault'])
        head.append(self.config['TimeCommand'] + self.config['TimeDefault'])
        head.append(self.config['NThreadsCommand'] + '=' + self.config['NThreads'])
        head.append(self.config['JobIDCommand'] + '=' + '"{jobid}"')
        head.append(
            self.config['OutputCommand'] + '=' + os.path.abspath(os.path.join(self.outputDir, 'Output-{jobid}.out')))
        head.append(self.config['CommandWrapper'] + '=')
        return " ".join(head)

    def submit_jobs(self):
        for job in self.submissionlist:
            os.system(job)

    def print_jobs(self):
        for job in self.submissionlist:
            click.echo(job)

    def get_threads_command(self):
        return [self.config['NThreadsCommand'], self.config['NThreads']]


class Job:

    def __init__(self, jobID, jobString):
        self.jobID = jobID
        self.jobString = jobString
