import json
from pkg_resources import resource_stream
import os

from .utils import get_logger
from clpipe.config.parallel import ParallelConfig

# TODO: We need to update the batch manager to be more flexible,
# so as to allow for no-quotes, no equals, and to not have various options
# for example, BIAC doesn't have time or number of cores as options.

LOGGER_NAME = "batch-manager"
OUTPUT_FORMAT_STR = "Output-{jobid}-jobid-%j.out"
JOB_ID_FORMAT_STR = "{jobid}"
MAX_JOB_DISPLAY = 5
DEFAULT_BATCH_CONFIG_PATH = "slurmUNCConfig.json"


class ParallelManager:
    """
    Handles the creation and submission of batch jobs.
    """

    def __init__(
        self,
        batch_system_config: os.PathLike,
        output_directory=None,
        debug=False,
        mem_use=None,
        time=None,
        threads=None,
        email=None,
    ):
        self.jobs = []
        self.debug = debug
        self.logger = get_logger(LOGGER_NAME, debug=debug)

        if os.path.exists(os.path.abspath(batch_system_config)):
            self.logger.debug(f"Using batch config at: {batch_system_config}")
            with open(os.path.abspath(batch_system_config)) as bat_config:
                self.config = json.load(bat_config)
        else:
            with resource_stream(
                __name__, "batchConfigs/" + batch_system_config
            ) as bat_config:
                self.config = json.load(bat_config)

        self.submission_list = []
        if output_directory is None:
            self.logger.warning(
                ("No output directory provided " "- defauling to current directory")
            )
            output_directory = "."
        self.logger.info(f"Batch job output path: {output_directory}")
        self.output_dir = os.path.abspath(output_directory)
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
            self.logger.debug(f"Created batch output directory at: {output_directory}")

        self.config = ParallelConfig()
        self.config.mem_use = mem_use
        self.config.time = time
        self.config.threads = threads
        self.config.email = email

        self.create_submission_head()

    def update_mem_usage(self, mem_use):
        self.config.mem_use = mem_use

    def update_time(self, time):
        self.config.time = time

    def update_nthreads(self, threads):
        self.config.threads = threads

    def update_email(self, email):
        self.config.email = email

    def addjob(self, job):
        self.jobs.append(job)

    def add_job(self, job):
        return self.addjob(job)

    def compilejobstrings(self):
        header = self.createsubmissionhead()
        for job in self.jobs:
            temp = header.format(jobid=job.jobID, cmdwrap=job.jobString)
            self.submission_list.append(temp)

    def compile_job_strings(self):
        return self.compilejobstrings()

    def createsubmissionhead(self):
        head = [self.config["SubmissionHead"]]
        for e in self.config["SubmissionOptions"]:
            temp = e["command"] + " " + e["args"]
            head.append(temp)
        for e in self.config["SubOptionsEqual"]:
            temp = e["command"] + "=" + e["args"]
            head.append(temp)

        head.append(
            self.config["MemoryCommand"].format(mem=self.config["MemoryDefault"])
        )
        if self.config["TimeCommandActive"]:
            head.append(
                self.config["TimeCommand"].format(time=self.config["TimeDefault"])
            )
        if self.config["ThreadCommandActive"]:
            head.append(
                self.config["NThreadsCommand"].format(nthreads=self.config["NThreads"])
            )
        if self.config["JobIDCommandActive"]:
            head.append(self.config["JobIDCommand"].format(jobid=JOB_ID_FORMAT_STR))
        if self.config["OutputCommandActive"]:
            head.append(
                self.config["OutputCommand"].format(
                    output=os.path.abspath(
                        os.path.join(self.output_dir, OUTPUT_FORMAT_STR)
                    )
                )
            )
        if self.config["EmailAddress"]:
            head.append(
                self.config["EmailCommand"].format(email=self.config["EmailAddress"])
            )
        head.append(self.config["CommandWrapper"])

        return " ".join(head)

    def create_submission_head(self):
        return self.createsubmissionhead()

    def submit_jobs(self):
        self.logger.info(f"Submitting {len(self.submission_list)} job(s).")
        self.logger.debug(f"Memory usage: {self.config['MemoryDefault']}")
        self.logger.debug(f"Time usage: {self.config['TimeDefault']}")
        self.logger.debug(f"Number of threads: {self.config['NThreads']}")
        self.logger.debug(f"Email: {self.config['EmailAddress']}")
        for job in self.submission_list:
            os.system(job)

    def print_jobs(self):
        job_count = len(self.submission_list)

        if job_count == 0:
            output = "No jobs to run."
        else:
            output = "Jobs to run:\n\n"
            for index, job in enumerate(self.submission_list):
                output += "\t" + job + "\n\n"
                if (
                    index == MAX_JOB_DISPLAY - 1
                    and job_count > MAX_JOB_DISPLAY
                    and not self.debug
                ):
                    output += f"\t...and {job_count - 5} more job(s).\n"
                    break
            output += "Re-run with the '-submit' flag to launch these jobs."
        self.logger.info(output)

    def get_threads_command(self):
        return [self.config["NThreadsCommand"], self.config["NThreads"]]


# Would take manager
class JobRunner:
    def __init__(self, method: str) -> None:
        """
        Initializes a JobRunner object.

         Args:
             method (str): "Parallel / Local"
             The method to be used for running the job.
        """
        self.job_queue = []
        self.method = method

        if method == "parallel":
            self.job_manager = ParallelManager()
        else:
            self.job_manager = None

    def add_job(self, job):
        self.job_queue.append(job)


# Top job container
class JobQueue:
    def __init__(self) -> None:
        pass

    def add_job():
        pass


class Job:
    pass


# These go in container
class ParallelJob:
    def __init__(self, jobID, jobString):
        self.jobID = jobID
        self.jobString = jobString


class LocalJob:
    pass


# Both parallel config and jobs are passed into JobQueue to be run
