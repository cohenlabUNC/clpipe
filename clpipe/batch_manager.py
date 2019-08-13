import click
import json
from pkg_resources import resource_stream
import os
import sys

#Todo: We need to update the batch manager to be more flexible, so as to allow for no-quotes, no equals, and to not have various options
# for example, BIAC doesn't have time or number of cores as options.

class BatchManager:

    def __init__(self, batchsystemConfig, outputDirectory=None):
        self.jobs = []
        if os.path.exists(os.path.abspath(batchsystemConfig)):
            with os.open(os.path.abspath(batchsystemConfig)) as bat_config:
                self.config = json.load(bat_config)
        else:
            with resource_stream(__name__, "batchConfigs/" + batchsystemConfig) as bat_config:
                self.config = json.load(bat_config)

        self.submissionlist = []
        if outputDirectory is None:
            outputDirectory = '.'
        self.outputDir = os.path.abspath(outputDirectory)
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
            temp = header.format(jobid=job.jobID)
            if self.config['NoQuotes']:
                temp = temp + job.jobString
            else:
                temp = temp + '"' + job.jobString + '"'
            self.submissionlist.append(temp)


    def createsubmissionhead(self):
        head = [self.config['SubmissionHead']]
        for e in self.config['SubmissionOptions']:
            temp = e['command'] + ' ' + e['args']
            head.append(temp)
        for e in self.config['SubOptionsEqual']:
            temp = e['command'] + '=' + e['args']
            head.append(temp)

        head.append(self.config['MemoryCommand'].format(
            mem =self.config['MemoryDefault']))
        if self.config['TimeCommandActive']:
            head.append(self.config['TimeCommand'].format(
                time = self.config['TimeDefault']))
        if self.config['ThreadCommandActive']:
            head.append(self.config['NThreadsCommand'].format(
                nthreads = self.config['NThreads']
            ))
        if self.config['JobIDCommandActive']:
            head.append(self.config['JobIDCommand'].format(
                jobid = '{jobid}'))
        if self.config['OutputCommandActive']:
            head.append(self.config['OutputCommand'].format(
                output =os.path.abspath(os.path.join(self.outputDir, 'Output-{jobid}.out'))))
        head.append(self.config['CommandWrapper'])

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
