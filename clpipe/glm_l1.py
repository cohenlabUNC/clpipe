import os
import glob
import logging
from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import sys
from .error_handler import exception_handler
import nibabel as nib


def glm_l1_preparefsf(glm_config_file=None, l1_name=None, debug=None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    glm_config = GLMConfigParser(glm_config_file)

    l1_block = [x for x in glm_config.config['Level1Setups'] if x['ModelName'] == str(l1_name)]
    if len(l1_block) is not 1:
        raise ValueError("L1 model not found, or multiple entries found.")

    l1_block = l1_block[0]
    glm_setup_options = glm_config.config['GLMSetupOptions']

    _glm_l1_propagate(l1_block, glm_setup_options)


def _glm_l1_propagate(l1_block, glm_setup_options):
    with open(l1_block['FSFPrototype']) as f:
        fsf_file_template=f.readlines()

    output_ind = [i for i,e in enumerate(fsf_file_template) if "set fmri(outputdir)" in e]
    image_files_ind = [i for i,e in enumerate(fsf_file_template) if "set feat_files" in e]
    ev_file_inds = [i for i,e in enumerate(fsf_file_template) if "set fmri(custom" in e]
    confound_file_ind = [i for i,e in enumerate(fsf_file_template) if "set confoundev_files(1)" in e]
    regstandard_ind = [i for i, e in enumerate(fsf_file_template) if "set fmri(regstandard)" in e]
    tps_inds = [i for i, e in enumerate(fsf_file_template) if "set fmri(npts)" in e]
    if l1_block['ImageIncludeList'] is not "" and l1_block['ImageExcludeList'] is not "":
        raise ValueError("Only one of ImageIncludeList and ImageExcludeList should be non-empty")

    image_files = glob.glob(os.path.join(l1_block['TargetDirectory'], "**", "*"+l1_block['TargetSuffix']), recursive = True)

    if l1_block['ImageIncludeList'] is not "":
        image_files = [file_path for file_path in image_files if os.path.basename(file_path) in l1_block['ImageIncludeList']]
        base_names = [os.path.basename(file_path) for file_path in image_files]

        files_not_found = [file for file in base_names if file not in l1_block['ImageIncludeList']]
        if len(files_not_found):
            logging.warning("Did not find the following files: " + str(files_not_found))

    if l1_block['ImageExcludeList'] is not "":
        image_files = [file_path for file_path in image_files if
                       os.path.basename(file_path) not in l1_block['ImageExcludeList']]

    image_files = [file for file in image_files if
                         "task-" + glm_setup_options["TaskName"] in file]

    if not os.path.exists(l1_block['FSFDir']):
        os.mkdir(l1_block['FSFDir'])
    for file in image_files:
        try:
            logging.info("Creating FSF File for " + file)
            img_data = nib.load(file)
            total_tps = img_data.shape[3]
            ev_conf = _get_ev_confound_mat(file, l1_block)
            out_dir = os.path.join(l1_block['OutputDir'],os.path.basename(file).replace(l1_block["TargetSuffix"], ".feat"))
            out_fsf = os.path.join(l1_block['FSFDir'],
                                   os.path.basename(file).replace(l1_block["TargetSuffix"], ".fsf"))
            new_fsf = fsf_file_template

            new_fsf[tps_inds[0]] = "set fmri(npts) " + str(total_tps) + "\n"
            new_fsf[output_ind[0]] = "set fmri(outputdir) \"" + os.path.abspath(out_dir) + "\"\n"
            new_fsf[image_files_ind[0]] = "set feat_files(1) \"" + os.path.abspath(file) + "\"\n"

            if glm_setup_options['ReferenceImage'] is not "":
                new_fsf[regstandard_ind[0]] = "set fmri(regstandard) \"" + os.path.abspath(glm_setup_options['ReferenceImage']) + "\"\n"
            if l1_block['ConfoundSuffix'] is not "":
                new_fsf[confound_file_ind[0]] = "set confoundev_files(1) \"" + os.path.abspath(ev_conf['Confounds'][0]) + "\"\n"

            for i, e in enumerate(ev_conf['EVs']):
                new_fsf[ev_file_inds[i]] = "set fmri(custom" + str(i +1) + ") \"" + os.path.abspath(e) + "\"\n"



            with open(out_fsf, "w") as fsf_file:
                fsf_file.writelines(new_fsf)

        except Exception as err:
            logging.exception(err)


def _get_ev_confound_mat(file_name, l1_block):

    file_prefix = os.path.basename(file_name).replace(l1_block["TargetSuffix"], "")
    EV_files = [glob.glob(os.path.join(l1_block["EVDirectory"],"**",file_prefix + EV), recursive=True) for EV in l1_block['EVFileSuffices']]
    EV_files = [item for sublist in EV_files for item in sublist]

    if len(EV_files) is not len(l1_block['EVFileSuffices']):
        raise FileNotFoundError("Did not find enough EV files for this scan. Only found " + str(EV_files) +" and need " +str(len(l1_block['EVFileSuffices'])))

    if l1_block["ConfoundSuffix"] is not "":
        confound_file = glob.glob(os.path.join(l1_block["ConfoundDirectory"],"**",file_prefix + l1_block['ConfoundSuffix']), recursive = True)
        if len(confound_file) is not 1:
            raise FileNotFoundError("Did not find a confound file for this scan")
        return {"EVs": EV_files, "Confounds": confound_file}

    return {"EVs": EV_files}



#Design

#Step 1: Load in prototype, identify all needed lines
#Step 2: Load in paths for all image files, exclude/include as needed
#Step 3: run through all required image files, construct the file changes
#Step 3a: Change prototype and spit out into fsf output folder

