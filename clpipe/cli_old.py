import click
import sys

from .glm_setup import glm_setup as glm_setup_logic
from .glm_l1 import glm_l1_preparefsf as glm_l1_preparefsf_logic,\
    glm_l1_launch_controller
from .glm_l2 import glm_l2_preparefsf as glm_l2_preparefsf_logic
from .fsl_onset_extract import fsl_onset_extract as fsl_onset_extract_logic
from .outliers_report import get_study_outliers, get_image_confounds





@cli.command()
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l1_name',  default=None, required = True,
              help='Name for a given L1 model')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def glm_l1_preparefsf(glm_config_file, l1_name, debug):
    """Propagate an .fsf file template for L1 GLM analysis"""
    
    glm_l1_preparefsf_logic(
        glm_config_file=glm_config_file, l1_name=l1_name, debug=debug)


@cli.command()
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, 
              file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l1_name',  default=None, required = True,
              help='Name for a given L1 model')
@click.option('-test_one', is_flag=True,
              help='Only submit one job for testing purposes.')
@click.option('-submit', is_flag=True,
              help='Flag to submit commands to the HPC.')
@click.option('-debug', is_flag=True, 
              help='Flag to enable detailed error messages and traceback')
def glm_l1_launch(glm_config_file, l1_name, test_one, submit, debug):
    """Launch all prepared .fsf files for L1 GLM analysis"""
    
    glm_l1_launch_controller(glm_config_file=glm_config_file, l1_name=l1_name,
                             test_one=test_one, submit=submit, debug=debug)


@cli.command()
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l2_name',  default=None, required = True,
              help='Name for a given L2 model')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def glm_l2_preparefsf(glm_config_file, l2_name, debug):
    """Propagate an .fsf file template for L2 GLM analysis"""
    glm_l2_preparefsf_logic(glm_config_file=glm_config_file, l2_name=l2_name, debug=debug)
@click.option('-l1_feat_folders_path', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False,
              help='Location of your L1 FEAT folders.')
def glm_apply_mumford_workaround(glm_config_file, l1_feat_folders_path):
    """
    Apply the Mumford registration workaround to L1 FEAT folders. 
    Applied by default in glm-l2-preparefsf.
    """
    if not (glm_config_file or l1_feat_folders_path):
        click.echo("Error: At least one of either option '-glm_config_file' or '-l1_feat_folders_path' required.")
        sys.exit()


@cli.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def glm_onset_extract(config_file, glm_config_file, debug):
    """Convert onset files to FSL's 3 column format"""
    fsl_onset_extract_logic(
        config_file=config_file, glm_config_file=glm_config_file, debug=debug)


@cli.command()
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
