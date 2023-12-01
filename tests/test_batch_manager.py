import pytest
from clpipe.job_manager import *

SLURMUNCCONFIG: str = "clpipe/batchConfigs/slurmUNCConfig.json"


def test_batch_manager_instantiation():
    batch_manager = BatchManager(SLURMUNCCONFIG)
    assert isinstance(batch_manager, BatchManager)


def test_adding_jobs():
    batch_manager = BatchManager(SLURMUNCCONFIG)
    job1 = Job(1, "echo hi")
    batch_manager.add_job(job1)

    assert len(batch_manager.jobs) == 1
    assert batch_manager.jobs[0].job_name == 1
    assert batch_manager.jobs[0].job_string == "echo hi"

    job2 = Job(2, "additional_job")
    batch_manager.add_job(job2)

    assert len(batch_manager.jobs) == 2
    assert batch_manager.jobs[1].job_name == 2
    assert batch_manager.jobs[1].job_string == "additional_job"


def test_job_string_creation():
    batch_manager = BatchManager(SLURMUNCCONFIG)
    job = Job(1, "test_job_string")
    batch_manager.add_job(job)
    batch_manager.compile_job_strings()
    assert len(batch_manager.submission_list) == 1


def test_parallel_manager_creation():
    parallel_manager = JobManager()
