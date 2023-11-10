import pytest
from clpipe.job_manager import *

SLURMUNCCONFIG: str = "clpipe/batchConfigs/slurmUNCConfigSnakeCase.json"


def test_batch_manager_instantiation(scatch_dir):
    batch_manager = JobManagerFactory.get(
        batch_config=os.path.abspath(SLURMUNCCONFIG), output_directory=scatch_dir
    )
    assert isinstance(batch_manager, BatchJobManager)

    batch_manager.add_job(1, "echo hi")
    assert len(batch_manager.job_queue) == 1

    batch_manager.add_job(2, "echo test")
    assert len(batch_manager.job_queue) == 2

    batch_manager.print_jobs()
    batch_manager.submit_jobs()

    assert len(batch_manager.job_queue) == 0


def test_local_manager_instantiation(scatch_dir, capsys):
    local_manager = JobManagerFactory.get(output_directory=scatch_dir)
    assert isinstance(local_manager, LocalJobManager)

    local_manager.add_job(1, "echo local")
    assert len(local_manager.job_queue) == 1

    local_manager.add_job(2, "echo running")
    assert len(local_manager.job_queue) == 2

    local_manager.print_jobs()
    process1, process2 = local_manager.submit_jobs()

    assert process1.stdout.decode("utf-8") == "local\n"
    assert process2.stdout.decode("utf-8") == "running\n"

    assert len(local_manager.job_queue) == 0
