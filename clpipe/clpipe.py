import os
import logging
import json
from pathlib import Path
from typing import List
from pkg_resources import resource_stream

import clpipe.config_json_parser
import clpipe.utils

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(level=logging.INFO)

class App:
    def __init__(self, config_file=None, name="", submit=False, distribute=False, debug=False):
        self.name = name
        self.distribute = distribute
        self.submit = submit
        self.debug = debug
        self.cluster = None

        if not config_file:
            raise ValueError("No config file provided")
        else:
            self.configParser = clpipe.config_json_parser.ClpipeConfigParser()
            self.configParser.config_updater(config_file)
            self.config = self.configParser.config
            self.config_file = Path(config_file)

        if self.distribute:
            self.cluster = Cluster(self.config["BatchConfig"])

    def run():
        pass


class BIDSApp:
    def __init__(self, bids_dir, subjects=None, config_file=None, name="", submit=False, distribute=False, debug=False):
        super.__init__(name=name, config_file=config_file, distribute=distribute, debug=debug)

        self.jobs: JobList = None
        self.bids_dir = bids_dir

        self.subjects_to_process = clpipe.utils._get_subjects(self.bids, subjects)

    def build_jobs(self):
        pass

    def run(self):
        if self.distribute:
            self.cluster.distribute(self.jobs)
        else:
            self.jobs.run_jobs()

class Job:
    def __init__(self, name="", log_dir=None):
        self.name = name
        self.log_dir = log_dir
        self._setup_logger()
        
    def _setup_logger(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}{self.name}")
        self.logger.setLevel(logging.INFO)
        
        # Create log handler
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)

        # Create log formatter to add to handler
        c_format = logging.Formatter(LOG_FORMAT)
        c_handler.setFormatter(c_format)
        
        # Add handler to logger
        self.logger.addHandler(c_handler)

    def _setup_file_logger(self):
        if self.log_dir:
            # Create log handler
            f_handler = logging.FileHandler(self.log_dir / f'{self.name}.log')
            f_handler.setLevel(logging.DEBUG)
            
            # Create log format
            f_format = logging.Formatter(LOG_FORMAT)
            f_handler.setFormatter(f_format)

            # Add handler to the logger
            self.logger.addHandler(f_handler)
        else:
            raise ValueError()

    def setup(self):
        pass

    def run(self):
        pass

    def get_cmd_string(self):
        return None

    def __call__(self):
        self.setup()
        self.run()

class ClusterConfig:
    def __init__(self, batchsystemConfig, outputDirectory=None):
        if os.path.exists(os.path.abspath(batchsystemConfig)):
            with os.open(os.path.abspath(batchsystemConfig)) as bat_config:
                self.config = json.load(bat_config)
        else:
            with resource_stream(__name__, "batchConfigs/" + batchsystemConfig) as bat_config:
                self.config = json.load(bat_config)

        if outputDirectory is None:
            outputDirectory = '.'
        self.outputDir = os.path.abspath(outputDirectory)
        if not os.path.isdir(outputDirectory):
            os.makedirs(outputDirectory)

        self.create_submission_head()

    def generate_submission_string(self, job_id, job_string):
        return self.header.format(jobid=job_id, cmdwrap=job_string)

    def update_mem_usage(self, mem_use):
        self.config['MemoryDefault'] = mem_use

    def update_time(self, time):
        self.config['TimeDefault'] = time

    def update_nthreads(self, threads):
        self.config['NThreads'] = threads

    def update_email(self, email):
        self.config['EmailAddress'] = email

    def get_threads_command(self):
        return [self.config['NThreadsCommand'], self.config['NThreads']]

    def create_submission_head(self):
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
                output =os.path.abspath(os.path.join(self.outputDir, 'Output-{jobid}-jobid-%j.out'))))
        if self.config["EmailAddress"]:
            head.append(self.config['EmailCommand'].format(
                email=self.config["EmailAddress"]))
        head.append(self.config['CommandWrapper'])

        self.header_template = " ".join(head)

class JobList:
    def __init__(self, jobs: List):
        self.jobs = jobs

    def add_job(self, job: Job):
        self.jobs.append(job)

    def run_jobs(self):
        for job in self.jobs:
            job.run()

class Cluster:
    def __init__(self, cluster_config: ClusterConfig=None):
        self.cluster_config = cluster_config
        self.cmd_string = None

    def distribute(self, joblist: JobList):
        for job in joblist.jobs:
            cmd_string = job.get_cmd_string()
            if cmd_string:
                self.submission_cmd = self.cluster_config.generate_submission_string(job.name, job.cmd_string)
                os.system(self.submission_cmd)
            else:
                raise NotImplementedError("Job must implement get_cmd_string() to distribute.")

