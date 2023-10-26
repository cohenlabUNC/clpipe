import pytest
from clpipe.job_manager import *

SLURMUNCCONFIG: str = "clpipe/batchConfigs/slurmUNCConfig.json"


def test_batch_manager_instantiation():
    batch_manager = JobManagerFactory.get(SLURMUNCCONFIG)
    assert isinstance(batch_manager, BatchJobManager)
