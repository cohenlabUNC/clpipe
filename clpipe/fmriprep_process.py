import click

@click.command()
@click.argument('configFile')
@click.option('-bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-workingDir', type=click.Path(dir_okay=True, file_okay=False))
def fmriprep_process(bidsDirectory, workingDir, configFile):

    return 0


#Parameters for this function below should be all the options for fmriprep processing
def fmriprep_process_int():

    return 0


c