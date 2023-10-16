import os
import click
from .config_json_parser import ClpipeConfigParser
from .batch_manager import BatchManager, Job
import logging


@click.command()
@click.option(
    "-config_file",
    required=False,
    type=click.Path(exists=False, dir_okay=False, file_okay=True),
    default=None,
    help="A config file. Optional if you have a batch_config specified",
)
@click.option(
    "-batch_config",
    type=click.Path(exists=False, dir_okay=False, file_okay=True),
    help="A batch config file. Optional if a batch_config is provided in the supplied config file.",
)
@click.option(
    "-log_dir",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help="Where to put the test output. Defaults to current working directory",
    default=os.getcwd(),
)
@click.option(
    "-submit", is_flag=True, default=False, help="Flag to submit commands to the HPC"
)
def test_batch_setup(config_file=None, batch_config=None, log_dir=None, submit=None):
    config = ClpipeConfigParser()
    config.config_updater(config_file)
    if batch_config is not None:
        config.config["BatchConfig"] = batch_config

    batch_manager = BatchManager(config.config["BatchConfig"], os.path.abspath(log_dir))
    batch_manager.update_email(config.config["EmailAddress"])
    os.makedirs(os.path.abspath(log_dir), exist_ok=True)
    submission_string = 'python3 -c \\"print(\\\\\\"Hello Cluster\\\\\\")\\"'
    test_IDs = ["Test-" + str(i) for i in range(10)]

    for ID in test_IDs:
        batch_manager.addjob(Job(ID, submission_string))

    batch_manager.compilejobstrings()

    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()
