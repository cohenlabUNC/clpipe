import os

import click

from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None)
@click.option('-targetDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-targetSuffix')
@click.option('-outputDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-outputSuffix')
@click.option('-logOutputDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-submit/-save', default=False)
@click.option('-batch/-single', default=True)
def fmri_postprocess(configfile=None, subjects=None, targetdir=None, targetsuffix = None,  outputdir=None, outputsuffix = None, logoutputdir=None,
                     submit=False, batch=True):
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

    config.setup_postprocessing(targetdir, targetsuffix, outputdir, outputsuffix)
    config.validate_config()

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(targetdir)
                   if os.path.isdir(os.path.join(targetdir, o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    submission_string = '''fmri_postprocess -configfile={config} -targetDir={targetDir} -targetSuffix={targetSuffix} '''\
                        '''-outputDir={outputDir} -outputSuffix={outputSuffix} -logOutputDir={logOutputDir} -submit -single {sub}'''



    if batch:
        batch_manager = BatchManager(config.config['batchConfig'])
        for sub in subjects:
            sub_string_temp = submission_string.format(
                config = configfile,
                targetDir = targetdir,
                targetSuffix = targetsuffix,
                outputDir = outputdir,
                outputSuffix = outputsuffix,
                logOutputDir=logoutputdir,
                sub = sub
            )
            batch_manager.addjob(Job(sub, sub_string_temp))
        if submit:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
            config.update_runlog(subjectstring, "PostProcessing")
            config.config_json_dump(outputdir, configfile)
        else:
            click.echo(batch_manager.print_jobs())
    else:
        for sub in subjects:
            _fmri_postprocess()


def _fmri_postprocess():
    return 0