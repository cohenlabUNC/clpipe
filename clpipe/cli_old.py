import click

from .outliers_report import get_study_outliers, get_image_confounds





@click.command()
@click.option('--confounds_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="Path to a directory containing subjects and confounds files.")
@click.option('--confounds_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), help="Path to confounds file")
@click.option('--output_file', type=click.Path(dir_okay=False, file_okay=True), help="Path to save outlier count results.")
@click.option('--confound_suffix', help="Confound file to search for, like 'confounds.tsv'", default='confounds.tsv')
def report_outliers(confounds_dir, confounds_file, output_file, 
                    confound_suffix):
    """Generate a confound outliers report."""
    
    if confounds_dir:
        get_study_outliers(confounds_dir, output_file, confound_suffix)
    else:
        get_image_confounds(confounds_file)
