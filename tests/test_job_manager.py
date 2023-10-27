import pytest
from clpipe.job_manager import *

SLURMUNCCONFIG: str = "clpipe/batchConfigs/slurmUNCConfigSnakeCase.json"


def test_batch_manager_instantiation():
    batch_manager = JobManagerFactory.get(batch_config=os.path.abspath(SLURMUNCCONFIG))
    assert isinstance(batch_manager, BatchJobManager)

    batch_manager.add_job(1, "echo hi")
    assert len(batch_manager.job_queue) == 1

    batch_manager.add_job(2, "echo test")
    assert len(batch_manager.job_queue) == 2

    batch_manager.print_jobs()
    batch_manager.submit_jobs()

    assert len(batch_manager.job_queue) == 0


def test_local_manager_instantiation():
    batch_manager = JobManagerFactory.get()
    assert isinstance(batch_manager, LocalJobManager)

    batch_manager.add_job(1, "echo local")
    assert len(batch_manager.job_queue) == 1

    batch_manager.add_job(2, "echo running")
    assert len(batch_manager.job_queue) == 2

    batch_manager.print_jobs()
    batch_manager.submit_jobs()

    assert len(batch_manager.job_queue) == 0
