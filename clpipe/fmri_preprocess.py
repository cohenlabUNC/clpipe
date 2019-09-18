import os
import click
import sys
import logging
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
from .error_handler import exception_handler


@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-bids_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which BIDS directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary.')
@click.option('-working_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to generate the working directory. If a configuration file is provided with a working directory, this argument is not necessary.')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the preprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files (such as SLURM output files)')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def fmriprep_process(bids_dir=None, working_dir=None, output_dir=None, config_file=None, subjects=None,log_dir=None,submit=False, debug=False):
    """This command runs a BIDS formatted dataset through fMRIprep. Specify subject IDs to run specific subjects. If left blank, runs all subjects."""

    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ConfigParser()
    config.config_updater(config_file)
    config.setup_fmriprep_directories(bids_dir, working_dir, output_dir, log_dir)
    if not any([config.config['FMRIPrepOptions']['BIDSDirectory'], config.config['FMRIPrepOptions']['OutputDirectory'],
                config.config['FMRIPrepOptions']['WorkingDirectory'],
                config.config['FMRIPrepOptions']['LogDirectory']]):
        raise ValueError(
            'Please make sure the BIDS, working and output directories are specified in either the configfile or in the command. At least one is not specified.')

    singularity_string = '''unset PYTHONPATH; singularity run -B {bindPaths} {batchcommands} {fmriprepInstance} {bidsDir} {outputDir} participant ''' \
                         '''--participant-label {participantLabels} -w {workingdir} --fs-license-file {fslicense} {threads} {otheropts}'''

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['FMRIPrepOptions']['BIDSDirectory'])
                   if os.path.isdir(os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    batch_manager = BatchManager(config.config['BatchConfig'], config.config['FMRIPrepOptions']['LogDirectory'])
    batch_manager.update_mem_usage(config.config['FMRIPrepOptions']['FMRIPrepMemoryUsage'])
    batch_manager.update_time(config.config['FMRIPrepOptions']['FMRIPrepTimeUsage'])
    batch_manager.update_nthreads(config.config['FMRIPrepOptions']['NThreads'])
    batch_manager.update_email(config.config["EmailAddress"])

    if batch_manager.config['ThreadCommandActive']:
        threads = '--nthreads ' + batch_manager.get_threads_command()[1]
    else:
        threads = ''

    for sub in sublist:
        batch_manager.addjob(Job("sub-" + sub + "fmriprep", singularity_string.format(
            fmriprepInstance=config.config['FMRIPrepOptions']['FMRIPrepPath'],
            bidsDir=config.config['FMRIPrepOptions']['BIDSDirectory'],
            outputDir=config.config['FMRIPrepOptions']['OutputDirectory'],
            workingdir=config.config['FMRIPrepOptions']['WorkingDirectory'],
            batchcommands=batch_manager.config["FMRIPrepBatchCommands"],
            participantLabels=sub,
            fslicense=config.config['FMRIPrepOptions']['FreesurferLicensePath'],
            threads= threads,
            bindPaths=batch_manager.config['SingularityBindPaths'],
            otheropts=config.config['FMRIPrepOptions']['CommandLineOpts']
        )))

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
        config.update_runlog(subjectstring, "FMRIprep")
        config.config_json_dump(config.config['FMRIPrepOptions']['OutputDirectory'], config_file)
    else:
        batch_manager.print_jobs()
