import os
import click
from .config_json_parser import ConfigParser
from .batch_manage import BatchManager, Job
@click.command()
@click.argument('configFile')
@click.argument('subjects', nargs = -1, required = False, default = None)
@click.option('-bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-workingDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-submit/-save', default = False)

def fmriprep_process(configFile=None, subjects=None, bidsDir=None, workingDir=None, outputDir=None, submit = False):
    config = ConfigParser()
    config.config_updater(configFile)

    if os.path.isdir(bidsDir):
        bidsDir = os.path.abspath(bidsDir)
    else:
        raise ValueError('BIDS Directory does not exist')

    if os.path.isdir(workingDir):
        workingDir = os.path.abspath(workingDir)
    else:
        workingDir = os.path.abspath(workingDir)
        os.makedirs(workingDir)

    if os.path.isdir(outputDir):
        outputDir = os.path.abspath(outputDir)
    else:
        outputDir = os.path.abspath(outputDir)
        os.makedirs(outputDir)

    config.setup_directories(bidsDir, workingDir, outputDir)
    singularityString = '''singularity run --cleanenv -B /proj {fmriprepInstance} {bidsDir} {outputDir} participant --participant-label {participantLabels} -w {workingdir}'''
    if subjects is None:
        subjectString = "ALL"
        subList = [o.replace('sub-', '') for o in os.listdir(bidsDir)
         if os.path.isdir(os.path.join(bidsDir, o)) and 'sub-' in o]

    else:
        subjectString = " , ".join(subjects)
        subList = subjects


    batch_manager = BatchManager


    for sub in subList:
        batch_manager.addjob(Job(sub, singularityString.format(
            fmriprepInstance = config.config['FMRIPrepPath'],
            bidsDir = bidsDir,
            outputDir = outputDir,
            workingDir = workingDir,
            participantLabels = sub
            )))

    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()

    config.update_runlog(subjectString,"FMRIprep")
    config.config_json_dump(os.path.join(outputDir, os.path.basename(configFile)))




#Parameters for this function below should be all the options for fmriprep processing
def fmriprep_process_int():

    return 0


