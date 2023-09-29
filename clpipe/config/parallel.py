from typing import List
from dataclasses import dataclass, field
from pathlib import Path
import json


# Questions:

# Frozen dataclasses
# Do I need to add string literals after every attribute created here?


@dataclass
class ParallelManagerConfig:
    """
    Config dataclass for ParallelManager
    """

    SubmissionHead: str
    SubmissionOptions: list = [{"command": "-n", "args": "1"}]
    SubOptionsEqual: list = []
    NThreadsCommand: str = "--cpus-per-task={nthreads}"
    NThreads: str = "1"
    MemoryCommand: str = "--mem={mem}"
    MemoryDefault: str = "1000"
    TimeCommand: str = "--time={time}"
    TimeDefault: str = "1:0:0"
    JobIDCommand: str = '--job-name="{jobid}"'
    OutputCommand: str = "--output={output}"
    CommandWrapper: str = '--wrap="{cmdwrap}"'
    EmailAddress: str = ""
    EmailCommand: str = "--mail-user {email} --mail-type=FAIL"
    FMRIPrepBatchCommands: str = "-e --no-home"
    NoQuotes: bool = False
    TimeCommandActive: bool = True
    ThreadCommandActive: bool = True
    JobIDCommandActive: bool = True
    OutputCommandActive: bool = True
    SingularityBindPaths: str = "/proj,/pine,/work,/nas02,/nas"

    # This is the best way I could figure out to use one dataclass but use different
    # default configs.
    # This is example config
    # unc_config = ParallelManagerConfig.from_default("unc")
    @classmethod
    def from_default(cls, config_type="unc"):
        defaults = {
            "unc": {
                "SubmissionHead": "sbatch --no-requeue",
                "SubmissionOptions": [{"command": "-n", "args": "1"}],
                "SingularityBindPaths": "/proj,/pine,/work,/nas02,/nas",
            },
            "pitt": {
                "SubmissionHead": "bq",
                "SubmissionOptions": [],
                "TimeCommandActive": False,
                "ThreadCommandActive": False,
                "JobIDCommandActive": False,
                "OutputCommandActive": False,
                "SingularityBindPaths": "/proj,/pine,/nas02,/nas",
            },
        }
        return cls(**defaults.get(config_type, {}))

    @classmethod
    def from_json(cls, json_file_path):
        with open(json_file_path, "r") as file:
            config_data = json.load(file)
        return cls(**config_data)
