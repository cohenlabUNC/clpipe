from typing import List
from dataclasses import dataclass, field
from pathlib import Path
import json

# Move this into Option


@dataclass
class ParallelManagerConfig(Option):
    """
    Config dataclass for ParallelManager
    """

    submission_head = field(default="sbatch --no-requeue", metadata={"required": True})
    submission_options = field(
        default=[{"command": "-n", "args": "1"}], metadata={"required": True}
    )
    sub_options_equal = field(default=[], metadata={"required": True})
    n_threads_command = field(
        default="--cpus-per-task={nthreads}", metadata={"required": True}
    )
    n_threads = field(default="1", metadata={"required": True})
    memory_command = field(default="--mem={mem}", metadata={"required": True})
    memory_default = field(default="1000", metadata={"required": True})
    time_command = field(default="--time={time}", metadata={"required": True})
    time_default = field(default="1:0:0", metadata={"required": True})
    job_id_command = field(default='--job-name="{jobid}"', metadata={"required": True})
    output_command = field(default="--output={output}", metadata={"required": True})
    command_wrapper = field(default='--wrap="{cmdwrap}"', metadata={"required": True})
    email_address = field(default="", metadata={"required": True})
    email_command = field(
        default="--mail-user {email} --mail-type=FAIL", metadata={"required": True}
    )
    fmri_prep_batch_commands = field(
        default="-e --no-home", metadata={"required": True}
    )
    no_quotes = field(default=False, metadata={"required": True})
    time_command_active = field(default=True, metadata={"required": True})
    thread_command_active = field(default=True, metadata={"required": True})
    job_id_command_active = field(default=True, metadata={"required": True})
    output_command_Active = field(default=True, metadata={"required": True})
    singularity_bind_paths = field(
        default="/proj,/pine,/work,/nas02,/nas", metadata={"required": True}
    )

    @classmethod
    def from_default(cls, config_type="unc"):
        defaults = {
            "unc": {
                "submission_head": field(default="sbatch --no-requeue"),
                "submission_options": field(default=[{"command": "-n", "args": "1"}]),
                "singularity_bind_paths": field(
                    default="/proj,/pine,/work,/nas02,/nas"
                ),
            },
            "pitt": {
                "submission_head": field(default="bq"),
                "submission_options": field(default=[]),
                "time_command_active": field(default=False),
                "thread_command_active": field(default=False),
                "job_id_command_active": field(default=False),
                "output_command_active": field(default=False),
                "singularity_bind_paths": field(default="/proj,/pine,/nas02,/nas"),
            },
        }
        return cls(**defaults.get(config_type, {}))
