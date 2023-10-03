import json
from pkg_resources import resource_stream
import os

from .utils import get_logger
from clpipe.config.parallel import ParallelManagerConfig

# TODO: We need to update the batch manager to be more flexible,
# so as to allow for no-quotes, no equals, and to not have various options
# for example, BIAC doesn't have time or number of cores as options.

LOGGER_NAME = "parallel-manager"
OUTPUT_FORMAT_STR = "Output-{jobid}-jobid-%j.out"
JOB_ID_FORMAT_STR = "{jobid}"
MAX_JOB_DISPLAY = 5
DEFAULT_BATCH_CONFIG_PATH = "slurmUNCConfig.json"


class JobRunner:
    pass


class ParallelRunner(JobRunner):
    """
    Handles the creation and submission of batch jobs.
    """

    # How to work with parallel_system_config? JSON dump into dataclass?
    # need to figure out how to JSON dump - look at how Will did it in options.
    # for now just working with
    def __init__(
        self,
        parallel_system_config: os.PathLike,
        output_directory=None,
        debug=False,
        mem_use=None,
        time=None,
        threads=None,
        email=None,
    ):
        self.debug = debug
        self.logger = get_logger(LOGGER_NAME, debug=debug)

        # if os.path.exists(os.path.abspath(parallel_system_config)):
        #     self.logger.debug(f"Using batch config at: {parallel_system_config}")
        #     with open(os.path.abspath(parallel_system_config)) as bat_config:
        #         self.config = json.load(bat_config)
        # else:
        #     with resource_stream(
        #         __name__, "batchConfigs/" + parallel_system_config
        #     ) as bat_config:
        #         self.config = json.load(bat_config)

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

        self.config = ParallelManagerConfig.load(
            os.path.abspath(parallel_system_config)
        )

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

    def compilejobstrings(self):
        header = self.create_submission_head()
        for job in self.job_queue:
            temp = header.format(job_id=job.job_id, cmdwrap=job.job_string)
            self.submission_list.append(temp)

    def compile_job_strings(self):
        return self.compilejobstrings()

    def createsubmissionhead(self):
        head = [self.config.SubmissionHead]
        for e in self.config.SubmissionOptions:
            temp = e["command"] + " " + e["args"]
            head.append(temp)
        for e in self.config.SubOptionsEqual:
            temp = e["command"] + "=" + e["args"]
            head.append(temp)

        head.append(self.config.MemoryCommand.format(mem=self.config.MemoryDefault))
        if self.config.TimeCommandActive:
            head.append(self.config.TimeCommand.format(time=self.config.TimeDefault))
        if self.config.ThreadCommandActive:
            head.append(
                self.config.NThreadsCommand.format(nthreads=self.config.NThreads)
            )
        if self.config.JobIDCommandActive:
            head.append(self.config.JobIDCommand.format(jobid=JOB_ID_FORMAT_STR))
        if self.config.OutputCommandActive:
            head.append(
                self.config.OutputCommand.format(
                    output=os.path.abspath(
                        os.path.join(self.output_dir, OUTPUT_FORMAT_STR)
                    )
                )
            )
        if self.config.EmailAddress:
            head.append(self.config.EmailAddress.format(email=self.config.EmailAddress))
        head.append(self.config.CommandWrapper)

        return " ".join(head)

    def create_submission_head(self):
        return self.createsubmissionhead()

    def submit_jobs(self):
        self.logger.info(f"Submitting {len(self.submission_list)} job(s).")
        self.logger.debug(f"Memory usage: {self.config.MemoryDefault}")
        self.logger.debug(f"Time usage: {self.config.TimeDefault}")
        self.logger.debug(f"Number of threads: {self.config.NThreads}")
        self.logger.debug(f"Email: {self.config.EmailAddress}")
        for job in self.submission_list:
            os.system(job)

    def get_threads_command(self):
        return [self.config.NThreadsCommand, self.config.NThreads]


# Would take manager
class JobManager:
    def __init__(self, method: str) -> None:
        """
        Initializes a JobRunner object.

         Args:
             method (str): "Parallel / Local"
             The method to be used for running the job.
        """
        self.job_queue = []
        if method == "parallel":
            self.job_runner = ParallelRunner()
        else:
            self.job_runner = LocalRunner()

    def add_job(self, job_id, job_string):
        self.job_queue.append(Job(job_id, job_string))

    def submit_jobs(self):
        # Method to submit and run jobs from appropriate manager.
        self.job_manager.submit_jobs()

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


class LocalRunner(JobRunner):
    pass


class Job:
    def __init__(self, job_id, job_string):
        self.job_id = job_id
        self.job_string = job_string
