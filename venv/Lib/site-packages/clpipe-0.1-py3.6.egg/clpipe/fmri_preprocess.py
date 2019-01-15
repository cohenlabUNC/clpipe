import os
import click
from .config_json_parser import ConfigParser
from .batch_manage import BatchManager, Job
@click.command()
@click.argument('configFile', default = None, required = False)
@click.argument('subjects', nargs = -1, required = False, default = None)
@click.option('-bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-workingDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-outputDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-submit/-save', default = False)

def fmriprep_process(configfile=None, subjects=None, bidsdir=None, workingdir=None, outputdir=None, submit = False):
    config = ConfigParser()
    config.config_updater(configfile)

    if bidsdir is not None:
        if os.path.isdir(bidsdir):
            bidsdir = os.path.abspath(bidsdir)
        else:
            raise ValueError('BIDS Directory does not exist')
    else:
        bidsdir = config.config['BIDSDirectory']

    if workingdir is not None:
        if os.path.isdir(workingdir):
            workingdir = os.path.abspath(workingdir)
        else:
            workingdir = os.path.abspath(workingdir)
            os.makedirs(workingdir)
    else:
        workingdir = config.config['WorkingDirectory']

    if bidsdir is not None:
        if os.path.isdir(outputdir):
            outputdir = os.path.abspath(outputdir)
        else:
            outputdir = os.path.abspath(outputdir)
            os.makedirs(outputdir)
    else:
        outputdir = config.config['OutputDirectory']

    config.setup_directories(bidsdir, workingdir, outputdir)

    config.validate_config()
    singularityString = '''singularity run --cleanenv -B /proj {fmriprepInstance} {bidsDir} {outputDir} participant --participant-label {participantLabels} -w {workingdir}'''

    if not subjects:
        subjectString = "ALL"
        subList = [o.replace('sub-', '') for o in os.listdir(bidsdir)
         if os.path.isdir(os.path.join(bidsdir, o)) and 'sub-' in o]
    else:
        subjectString = " , ".join(subjects)
        subList = subjects


    batch_manager = BatchManager(config.config['BatchConfig'])


    for sub in subList:
        batch_manager.addjob(Job("sub-"+sub+"fmriprep", singularityString.format(
            fmriprepInstance = config.config['FMRIPrepPath'],
            bidsDir = bidsdir,
            outputDir = outputdir,
            workingdir = workingdir,
            participantLabels = sub
            )))

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()

    config.update_runlog(subjectString,"FMRIprep")
    config.config_json_dump(outputdir, configfile)






