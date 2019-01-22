import os

import click

from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser


@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None)
@click.option('-bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-workingDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-outputDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-logOutputDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-submit/-save', default=False)
def fmriprep_process(configfile=None, subjects=None, bidsdir=None, workingdir=None, outputdir=None, logoutputdir=None,
                     submit=False):
    config = ConfigParser()
    config.config_updater(configfile)
    if logoutputdir is not None:
        if os.path.isdir(logoutputdir):
            logoutputdir = os.path.abspath(logoutputdir)
        else:
            logoutputdir = os.path.abspath(logoutputdir)
            os.makedirs(logoutputdir, exist_ok=True)
    else:
        logoutputdir = outputdir + "/batchOutput"
        os.makedirs(logoutputdir, exist_ok=True)

    config.setup_fmriprep_directories(bidsdir, workingdir, outputdir)
    config.validate_config()

    singularity_string = '''singularity run --cleanenv -B {bindPaths} {fmriprepInstance} {bidsDir} {outputDir} participant'''\
        '''--participant-label {participantLabels} -w {workingdir} --fs-license-file {fslicense} --nthreads {threads}'''

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(bidsdir)
                   if os.path.isdir(os.path.join(bidsdir, o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    batch_manager = BatchManager(config.config['BatchConfig'], logoutputdir)
    batch_manager.update_mem_usage(config.config['FMRIPrepMemoryUsage'])
    for sub in sublist:
        batch_manager.addjob(Job("sub-" + sub + "fmriprep", singularity_string.format(
            fmriprepInstance=config.config['FMRIPrepPath'],
            bidsDir=bidsdir,
            outputDir=outputdir,
            workingdir=workingdir,
            participantLabels=sub,
            fslicense=config.config['FreesurferLicensePath'],
            threads=batch_manager.get_threads_command()[1],
            bindPaths=batch_manager.config['SingularityBindPaths']
        )))

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
        config.update_runlog(subjectstring, "FMRIprep")
        config.config_json_dump(outputdir, configfile)
    else:
        batch_manager.print_jobs()
