import os
import click
import sys
import logging
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
from .error_handler import exception_handler

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help = 'Which BIDS directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary.')
@click.option('-workingDir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to generate the working directory. If a configuration file is provided with a working directory, this argument is not necessary.')
@click.option('-outputDir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to put the preprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-logOutputDir', type=click.Path(dir_okay=True, file_okay=False),help='Where to put HPC output files (such as SLURM output files). If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC')
@click.option('-debug', is_flag = True, help = 'Flag to enable detailed error messages and traceback')
def fmriprep_process(bidsdir=None, workingdir=None, outputdir=None, configfile=None, subjects=None,  logoutputdir=None,
                     submit=False, debug=False):
    """This command runs a BIDS formatted dataset through fMRIprep. Specify subject IDs to run specific subjects. If left blank, runs all subjects."""

    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = ConfigParser()
    config.config_updater(configfile)
    config.setup_fmriprep_directories(bidsdir, workingdir, outputdir)
    config.validate_config()
    if not any([config.config['FMRIPrepOptions']['BIDSDirectory'], config.config['FMRIPrepOptions']['OutputDirectory'], config.config['FMRIPrepOptions']['WorkingDirectory']]):
        raise ValueError('Please make sure the BIDS, working and output directories are specified in either the configfile or in the command. At least one is not specified.')
    if logoutputdir is not None:
        if os.path.isdir(logoutputdir):
            logoutputdir = os.path.abspath(logoutputdir)
        else:
            logoutputdir = os.path.abspath(logoutputdir)
            os.makedirs(logoutputdir, exist_ok=True)
    else:
        logoutputdir = os.path.join(config.config['FMRIPrepOptions']['OutputDirectory'], "batchOutput")
        os.makedirs(logoutputdir, exist_ok=True)


    singularity_string = '''unset PYTHONPATH; singularity run -B {bindPaths} -e --no-home {fmriprepInstance} {bidsDir} {outputDir} participant '''\
        '''--participant-label {participantLabels} -w {workingdir} --fs-license-file {fslicense} --nthreads {threads}'''

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['FMRIPrepOptions']['BIDSDirectory'])
                   if os.path.isdir(os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    batch_manager = BatchManager(config.config['BatchConfig'], logoutputdir)
    batch_manager.update_mem_usage(config.config['FMRIPrepOptions']['FMRIPrepMemoryUsage'])
    for sub in sublist:
        batch_manager.addjob(Job("sub-" + sub + "fmriprep", singularity_string.format(
            fmriprepInstance=config.config['FMRIPrepOptions']['FMRIPrepPath'],
            bidsDir=config.config['FMRIPrepOptions']['BIDSDirectory'],
            outputDir=config.config['FMRIPrepOptions']['OutputDirectory'],
            workingdir=config.config['FMRIPrepOptions']['WorkingDirectory'],
            participantLabels=sub,
            fslicense=config.config['FMRIPrepOptions']['FreesurferLicensePath'],
            threads=batch_manager.get_threads_command()[1],
            bindPaths=batch_manager.config['SingularityBindPaths'],
        )))

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
        config.update_runlog(subjectstring, "FMRIprep")
        config.config_json_dump(config.config['FMRIPrepOptions']['OutputDirectory'], configfile)
    else:
        batch_manager.print_jobs()
