import os
import click
import sys
import logging
from .job_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from .error_handler import exception_handler


@click.command()
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.",
)
@click.option(
    "-bids_dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Which BIDS directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary.",
)
@click.option(
    "-working_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to generate the working directory. If a configuration file is provided with a working directory, this argument is not necessary.",
)
@click.option(
    "-output_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to put the preprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.",
)
@click.option(
    "-log_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to put HPC output files (such as SLURM output files)",
)
@click.option(
    "-submit", is_flag=True, default=False, help="Flag to submit commands to the HPC"
)
@click.option(
    "-debug", is_flag=True, help="Flag to enable detailed error messages and traceback"
)
def qsiprep_process(
    bids_dir=None,
    working_dir=None,
    output_dir=None,
    config_file=None,
    subjects=None,
    log_dir=None,
    submit=False,
    debug=False,
):
    """This command runs a BIDS formatted dataset through qsiprep. Specify subject IDs to run specific subjects. If left blank, runs all subjects."""

    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_fmriprep_directories(bids_dir, working_dir, output_dir, log_dir)
    if not any(
        [
            config.config["QSIprepOptions"]["BIDSDirectory"],
            config.config["QSIprepOptions"]["OutputDirectory"],
            config.config["QSIprepOptions"]["WorkingDirectory"],
            config.config["QSIprepOptions"]["LogDirectory"],
        ]
    ):
        raise ValueError(
            "Please make sure the BIDS, working and output directories are specified in either the configfile or in the command. At least one is not specified."
        )
    singularity_string = (
        """unset PYTHONPATH; {templateflow1} singularity run -B {templateflow2}{bindPaths} {batchcommands} {fmriprepInstance} {bidsDir} {outputDir} participant """
        """--participant-label {participantLabels} -w {workingdir} --fs-license-file {fslicense} {threads} {otheropts}"""
    )

    if config.config["QSIprepOptions"]["TemplateFlowToggle"]:
        template1 = (
            "export SINGULARITYENV_TEMPLATEFLOW_HOME={templateflowpath};".format(
                templateflowpath=config.config["QSIprepOptions"]["TemplateFlowPath"]
            )
        )
        template2 = "${{TEMPLATEFLOW_HOME:-$HOME/.cache/templateflow}}:{templateflowpath},".format(
            templateflowpath=config.config["QSIprepOptions"]["TemplateFlowPath"]
        )
    else:
        template1 = ""
        template2 = ""

    if not subjects:
        subjectstring = "ALL"
        sublist = [
            o.replace("sub-", "")
            for o in os.listdir(config.config["QSIprepOptions"]["BIDSDirectory"])
            if os.path.isdir(
                os.path.join(config.config["QSIprepOptions"]["BIDSDirectory"], o)
            )
            and "sub-" in o
        ]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    batch_manager = BatchManager(
        config.config["BatchConfig"], config.config["QSIprepOptions"]["LogDirectory"]
    )
    batch_manager.update_mem_usage(
        config.config["QSIprepOptions"]["QSIprepMemoryUsage"]
    )
    batch_manager.update_time(config.config["QSIprepOptions"]["QSIprepTimeUsage"])
    batch_manager.update_nthreads(config.config["QSIprepOptions"]["NThreads"])
    batch_manager.update_email(config.config["EmailAddress"])

    if batch_manager.config["ThreadCommandActive"]:
        threads = "--nthreads " + batch_manager.get_threads_command()[1]
    else:
        threads = ""

    for sub in sublist:
        batch_manager.add_job(
            Job(
                "sub-" + sub + "fmriprep",
                singularity_string.format(
                    templateflow1=template1,
                    templateflow2=template2,
                    fmriprepInstance=config.config["QSIprepOptions"]["QSIprepPath"],
                    bidsDir=config.config["QSIprepOptions"]["BIDSDirectory"],
                    outputDir=config.config["QSIprepOptions"]["OutputDirectory"],
                    workingdir=config.config["QSIprepOptions"]["WorkingDirectory"],
                    batchcommands=batch_manager.config["QSIprepBatchCommands"],
                    participantLabels=sub,
                    fslicense=config.config["QSIprepOptions"]["FreesurferLicensePath"],
                    threads=threads,
                    bindPaths=batch_manager.config["SingularityBindPaths"],
                    otheropts=config.config["QSIprepOptions"]["CommandLineOpts"],
                ),
            )
        )

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()
