import os
import glob
import logging
import sys
import shutil
import click
import pandas as pd

from .error_handler import exception_handler
from .config_json_parser import GLMConfigParser

PREPARE_FSF_COMMAND_NAME = "l2_preparefsf"
APPLY_MUMFORD_COMMAND_NAME = "apply_mumford_workaournd"


@click.command(PREPARE_FSF_COMMAND_NAME)
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l2_name',  default=None, required = True,
              help='Name for a given L2 model')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def glm_l2_preparefsf_cli(glm_config_file, l2_name, debug):
    """Propagate an .fsf file template for L2 GLM analysis"""
    glm_l2_preparefsf(glm_config_file=glm_config_file, l2_name=l2_name, debug=debug)


@click.command(APPLY_MUMFORD_COMMAND_NAME)
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = False,
              help='Location of your GLM config file.')
@click.option('-l1_feat_folders_path', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False,
              help='Location of your L1 FEAT folders.')
def glm_apply_mumford_workaround_cli(glm_config_file, l1_feat_folders_path):
    """
    Apply the Mumford registration workaround to L1 FEAT folders. 
    Applied by default in glm-l2-preparefsf.
    """
    if not (glm_config_file or l1_feat_folders_path):
        click.echo("Error: At least one of either option '-glm_config_file' or '-l1_feat_folders_path' required.")
        sys.exit()


def glm_l2_preparefsf(glm_config_file=None, l2_name=None, debug=None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    glm_config = GLMConfigParser(glm_config_file)

    l2_block = [x for x in glm_config.config['Level2Setups'] if x['ModelName'] == str(l2_name)]
    if len(l2_block) is not 1:
        raise ValueError("L2 model not found, or multiple entries found.")

    l2_block = l2_block[0]
    glm_setup_options = glm_config.config['GLMSetupOptions']

    _glm_l2_propagate(l2_block, glm_setup_options)


def _glm_l2_propagate(l2_block, glm_setup_options):
    sub_tab = pd.read_csv(l2_block['SubjectFile'])
    with open(l2_block['FSFPrototype']) as f:
        fsf_file_template=f.readlines()

    output_ind = [i for i,e in enumerate(fsf_file_template) if "set fmri(outputdir)" in e]
    image_files_ind = [i for i,e in enumerate(fsf_file_template) if "set feat_files" in e]
    regstandard_ind = [i for i, e in enumerate(fsf_file_template) if "set fmri(regstandard)" in e]


    sub_tab = sub_tab.loc[sub_tab['L2_name'] == l2_block['ModelName']]

    fsf_names = sub_tab.fsf_name.unique()

    if not os.path.exists(l2_block['FSFDir']):
        os.mkdir(l2_block['FSFDir'])

    for fsf in fsf_names:
        try:
            new_fsf = fsf_file_template
            target_dirs = sub_tab.loc[sub_tab["fsf_name"] == fsf].feat_folders
            counter = 1
            logging.info("Creating " + fsf)
            for feat in target_dirs:
                if not os.path.exists(feat):
                    raise FileNotFoundError("Cannot find "+ feat)
                else:
                    _apply_mumford_workaround(feat)
                    # if os.path.exists(os.path.join(feat, "reg_standard")):
                    #     shutil.rmtree(os.path.join(feat, "reg_standard"))
                    # shutil.copy(os.path.join(os.environ["FSLDIR"], 'etc/flirtsch/ident.mat'), os.path.join(feat, "reg/example_func2standard.mat"))
                    # shutil.copy(os.path.join(feat, 'mean_func.nii.gz'), os.path.join(feat, "reg/standard.nii.gz"))
                    new_fsf[image_files_ind[counter - 1]] = "set feat_files(" + str(counter) + ") \"" + os.path.abspath(
                        feat) + "\"\n"
                    counter = counter + 1

            out_dir = os.path.join(l2_block['OutputDir'], fsf + ".gfeat")
            new_fsf[output_ind[0]] = "set fmri(outputdir) \"" + os.path.abspath(out_dir) + "\"\n"
            out_fsf = os.path.join(l2_block['FSFDir'],
                                   fsf + ".fsf")

            if glm_setup_options['ReferenceImage'] is not "":
                new_fsf[regstandard_ind[0]] = "set fmri(regstandard) \"" + os.path.abspath(glm_setup_options['ReferenceImage']) + "\"\n"

            with open(out_fsf, "w") as fsf_file:
                fsf_file.writelines(new_fsf)

        except Exception as err:
            logging.exception(err)


def glm_apply_mumford_workaround(glm_config_file=None, l1_feat_folders_path=None):
    if glm_config_file:
        glm_config = GLMConfigParser(glm_config_file)
        l1_feat_folders_path = glm_config["Level1Setups"]["OutputDir"]
    print(f"Applying Mumford workaround to: {l1_feat_folders_path}")

    logging.info(f"Applying Mumford workaround to: {l1_feat_folders_path}")
    for l1_feat_folder in os.scandir(l1_feat_folders_path):
        if os.path.isdir(l1_feat_folder):
            print(f"Processing L1 FEAT folder: {l1_feat_folder.path}")
            _apply_mumford_workaround(l1_feat_folder)

    print(f"Finished applying Mumford workaround.")


def _apply_mumford_workaround(l1_feat_folder):
    """
    When using an image registration other than FSL's, such as fMRIPrep's, this work-around is
    necessary to run FEAT L2 analysis in FSL.

    See: https://mumfordbrainstats.tumblr.com/post/166054797696/feat-registration-workaround
    """
    for mat in glob.glob(os.path.join(l1_feat_folder, "reg", "*.mat")):
        os.remove(mat)

    reg_standard_path = os.path.join(l1_feat_folder, "reg_standard")
    if os.path.exists(reg_standard_path):
        logging.info(f"Removing: {reg_standard_path}")
        shutil.rmtree(os.path.join(l1_feat_folder, "reg_standard"))

    try:
        logging.info("Copying identity matrix")
        shutil.copy(os.path.join(os.environ["FSLDIR"], 'etc/flirtsch/ident.mat'), os.path.join(l1_feat_folder, "reg/example_func2standard.mat"))
        logging.info("Copying mean func image")
        shutil.copy(os.path.join(l1_feat_folder, 'mean_func.nii.gz'), os.path.join(l1_feat_folder, "reg/standard.nii.gz"))
    except FileNotFoundError as e:
        print(e, "- skipping")




