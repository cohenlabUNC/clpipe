"""
Design

Step 1: Load in prototype, identify all needed lines
Step 2: Load in paths for all image files, exclude/include as needed
Step 3: Run through all required image files, construct the file changes
Step 3a: Change prototype and spit out into fsf output folder
Step 4: Launch a feat job for each fsf
"""

import os
import glob
import logging
from .config_json_parser import GLMConfigParser
import sys
from .error_handler import exception_handler
from pathlib import Path
import nibabel as nib

from .batch_manager import BatchManager, Job


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


def glm_l1_launch_controller(glm_config_file: str=None, l1_name: str=None,
                             test_one: bool=False, submit: bool=True, 
                             debug: bool=None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    glm_config = GLMConfigParser(glm_config_file)

    glm_setup_options = _fetch_glm_setup_options_by_model(glm_config, l1_name)
    batch_options = glm_setup_options["BatchOptions"]

    memory_usage = batch_options["MemoryUsage"]
    time_usage = batch_options["TimeUsage"]
    n_threads = int(batch_options["NThreads"])
    batch_config_path = batch_options["BatchConfig"]
    email = batch_options["Email"]

    fsf_dir = glm_setup_options["FSFDir"]
    log_dir = glm_setup_options["LogDir"]

    batch_manager = _setup_batch_manager(memory_usage, time_usage, n_threads,
                                         email, batch_config_path, log_dir)

    glm_l1_launch(fsf_dir, batch_manager, test_one=test_one, submit=submit)


def _fetch_glm_setup_options_by_model(glm_config: dict, l1_name: str):
    l1_block = [x for x in glm_config.config['Level1Setups'] \
        if x['ModelName'] == str(l1_name)]
    if len(l1_block) is not 1:
        raise ValueError("L1 model not found, or multiple entries found.")

    l1_block = l1_block[0]
    return l1_block


def _setup_batch_manager(memory_usage: str, time_usage: str, n_threads: int, 
                         email: str, batch_config_path: str, log_dir):
    batch_manager = BatchManager(batch_config_path, log_dir)
    batch_manager.update_mem_usage(memory_usage)
    batch_manager.update_time(time_usage)
    batch_manager.update_nthreads(n_threads)
    batch_manager.update_email(email)

    return batch_manager


def glm_l1_launch(fsf_dir: str, batch_manager: BatchManager, 
                  test_one:bool=False, submit: bool=False):
    submission_strings = _create_l1_submission_strings(
        fsf_dir, test_one=test_one)
    _run_jobs(batch_manager, submission_strings, submit)

 
def _create_l1_submission_strings(fsf_files: os.PathLike, test_one:bool=False):
        logging.info(f"Building feat job submission strings")

        submission_strings = {}
        # "EXPORT PYTHONPATH = ; 
        SUBMISSION_STRING_TEMPLATE = ("feat {fsf_file}")
        
        logging.info("Creating submission strings")
        for fsf in Path(fsf_files).iterdir():
            key = f"{str(fsf.stem)}"
            
            submission_strings[key] = SUBMISSION_STRING_TEMPLATE.format(
                fsf_file=fsf
            )

            if test_one:
                break
        return submission_strings


def _populate_batch_manager(batch_manager: BatchManager, 
                            submission_strings: dict):
    logging.info("Setting up batch manager with jobs to run.")

    for key in submission_strings.keys():
        batch_manager.addjob(Job(key, submission_strings[key]))

    batch_manager.createsubmissionhead()
    batch_manager.compilejobstrings()


def _run_jobs(batch_manager, submission_strings, submit=True):
    num_jobs = len(submission_strings)

    if batch_manager:
        _populate_batch_manager(batch_manager, submission_strings)
        if submit:
            logging.info(f"Running {num_jobs} job(s) in batch mode")
            batch_manager.submit_jobs()
        else:
            batch_manager.print_jobs()
