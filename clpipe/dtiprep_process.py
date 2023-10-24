# Step 1: Identify files that have multiple encoding directions
# Step 2: Extract b=0 images
# Step 3: use FSL topup to create a unwarping image
# Step 4:

import os
import click
import sys
import logging
from .job_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from .error_handler import exception_handler
import glob
import numpy as np
import json


@click.command()
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.",
)
@click.option(
    "-bids_dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Which BIDS directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary.",
)
@click.option(
    "-working_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to generate the working directory. If a configuration file is provided with a working directory, this argument is not necessary.",
)
@click.option(
    "-output_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to put the preprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.",
)
@click.option(
    "-log_output_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to put HPC output files (such as SLURM output files). If not specified, defaults to <outputDir>/batchOutput.",
)
@click.option(
    "-submit", is_flag=True, default=False, help="Flag to submit commands to the HPC"
)
@click.option(
    "-debug", is_flag=True, help="Flag to enable detailed error messages and traceback"
)
def dti_preprocess(
    bids_dir=None,
    working_dir=None,
    output_dir=None,
    config_file=None,
    subjects=None,
    log_output_dir=None,
    submit=False,
    debug=False,
):
    """This command runs a BIDS formatted dataset through a DTI preprocessing pipeline. Specify subject IDs to run specific subjects. If left blank, runs all subjects."""

    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_fmriprep_directories(bids_dir, working_dir, output_dir)
    config.validate_config()
    if not any(
        [
            config.config["DTIPrepOptions"]["BIDSDirectory"],
            config.config["FMRIPrepOptions"]["OutputDirectory"],
            config.config["DTIPrepOptions"]["WorkingDirectory"],
        ]
    ):
        raise ValueError(
            "Please make sure the BIDS, working and output directories are specified in either the configfile or in the command. At least one is not specified."
        )
    if log_output_dir is not None:
        if os.path.isdir(log_output_dir):
            log_output_dir = os.path.abspath(log_output_dir)
        else:
            log_output_dir = os.path.abspath(log_output_dir)
            os.makedirs(log_output_dir, exist_ok=True)
    else:
        log_output_dir = os.path.join(
            config.config["DTIPrepOptions"]["OutputDirectory"], "Batch_Output"
        )
        os.makedirs(log_output_dir, exist_ok=True)


def dti_scan_json_grabber(bids_dir, subject, session):
    if session is None:
        sub_files_scans = glob.glob(
            os.path.join(
                bids_dir, "sub-{subject}".format(subject=subject), "dwi", "*_dwi.nii.gz"
            ),
            recursive=True,
        )
        sub_files_bvals = glob.glob(
            os.path.join(
                bids_dir, "sub-{subject}".format(subject=subject), "dwi", "*_dwi.bval"
            ),
            recursive=True,
        )
        sub_files_bvecs = glob.glob(
            os.path.join(
                bids_dir, "sub-{subject}".format(subject=subject), "dwi", "*_dwi.bvec"
            ),
            recursive=True,
        )
    else:
        sub_files_scans = glob.glob(
            os.path.join(
                bids_dir,
                "sub-{subject}".format(subject=subject),
                "ses-{session}".format(subject=subject),
                "dwi",
                "*_dwi.nii.gz",
            ),
            recursive=True,
        )
        sub_files_bvals = glob.glob(
            os.path.join(
                bids_dir, "sub-{subject}".format(subject=subject), "dwi", "*_dwi.bval"
            ),
            recursive=True,
        )
        sub_files_bvecs = glob.glob(
            os.path.join(
                bids_dir, "sub-{subject}".format(subject=subject), "dwi", "*_dwi.bvec"
            ),
            recursive=True,
        )

    dir = []
    total_readout_time = []
    for scan in sub_files_scans:
        json_path = scan.split(".")[0] + ".json"
        with open(os.path.abspath(json_path), "r") as config_file:
            sidecar = json.load(config_file)
        dir.append(sidecar["PhaseEncodingDirection"])
        total_readout_time.append(sidecar["TotalReadoutTime"])

    if ("j" and "j-") or ("i" and "i-") or ("k" and "k-") not in dir:
        return None

    scan_info = []
    for idx, scan in enumerate(sub_files_scans):
        bval_toggle = os.path.exists(scan.split(".")[0] + ".bval")
        if bval_toggle:
            scan_info.append(
                {
                    "scan": sub_files_scans[idx],
                    "dir": dir[idx],
                    "trt": total_readout_time[idx],
                    "bval": scan.split(".")[0] + ".bval",
                }
            )
        else:
            scan_info.append(
                {
                    "scan": sub_files_scans[idx],
                    "dir": dir[idx],
                    "trt": total_readout_time[idx],
                    "bval": None,
                }
            )

    return scan_info


def topup_command_creator(scan_info, config, subject):
    acq_param_dir_map = {
        "i": [1, 0, 0],
        "i-": [-1, 0, 0],
        "j": [0, 1, 0],
        "j-": [0, -1, 0],
        "k": [0, 0, 1],
        "k-": [0, 0, -1],
    }

    wk_dir = config.config["DTIprepOptions"]["WorkingDirectory"]
    os.mkdir(os.path.join(wk_dir, "sub-" + subject))
    target_wkdir = os.path.join(wk_dir, "sub-" + subject)
    fslroi_string = " fslroi {scan} {scan_output} 0 {maxindex};"
    fslroi_list = []
    acqparam_list = []
    merge_list = []
    for scan in scan_info:
        scan_name = os.path.basename(scan["scan"])
        if scan["bval"] is not None:
            b0coords = np.genfromtxt(scan["bval"])
            maxindex = max(np.where(b0coords == 0)[0]) + 1
        else:
            maxindex = 1
        fslroi_list.append(
            fslroi_string.format(
                scan=scan["scan"],
                scan_output=os.path.join(target_wkdir, scan_name),
                max_index=maxindex,
            )
        )
        merge_list.append(os.path.join(target_wkdir, scan_name))
        for i in range(0, maxindex):
            acqparam_list.append(
                acq_param_dir_map[scan["dir"]].copy().extend(scan["trt"])
            )

    acqparam = np.array(acqparam_list)
    acqparam.tofile(os.path.join(target_wkdir, "acqparam.txt"), sep=" ")
    merge_string = " ".join(merge_list)
    fslroi_full_string = " ".join(fslroi_list)
    acqparam_file = os.path.join(target_wkdir, "acqparam.txt")
    submission_string = """module add fsl; {fslroilist} fslmerge -t {topupinput} {mergelist}; topup --imain= {topupinput} \\
      --datain={acqparamfile} \\
      --config=b02b0.cnf \\
      --out={out} \\
      --iout={iout} \\
      --fout={fout} 
    """

    forsubmission = submission_string.format(
        fslroi_list=fslroi_full_string,
        topupinput=os.path.join(target_wkdir, "totopupfile"),
        mergelist=merge_string,
        acqparamfile=acqparam_file,
        out="topupfileout",
        iout="topupfileout_iout",
        fout="topupfileout_fout",
    )

    return forsubmission
