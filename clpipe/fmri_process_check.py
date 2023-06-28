import click
import pandas as pd
import os
import glob
from .utils import get_logger, add_file_handler, resolve_fmriprep_dir_new
from .config.pipeline import load_pipeline_config

STEP_NAME = "fmri-process-check"

def fmri_process_check(config_file, output_file=None, debug=False):
    """This command checks a BIDS dataset, an fMRIprep'ed dataset and a postprocessed
    dataset, and creates a CSV file that lists all scans across all three datasets. 
    Use to find which subjects/scans failed processing."""

    config = load_pipeline_config(config_file)

    add_file_handler(os.path.join(config.ProjectDirectory, "logs"))
    logger = get_logger(STEP_NAME, debug=debug)
    logger.info("Test Printing")

    sublist = [o for o in os.listdir(resolve_fmriprep_dir_new(config.PostProcessingOptions.TargetDirectory))
               if os.path.isdir(
            os.path.join(resolve_fmriprep_dir_new(config.PostProcessingOptions.TargetDirectory), o)) and 'sub-' in o]

    file_list = []
    for sub in sublist:
        logger.debug("Inspecting " + sub)
        bold_files = glob.glob(
            os.path.join(config.FMRIPrepOptions.BIDSDirectory, sub, '**', 'func', '*.nii.gz'),
            recursive=True)
        fmriprep_files = glob.glob(
            os.path.join(config.PostProcessingOptions.TargetDirectory, sub, '**', 'func',
                         '*' + config.PostProcessingOptions.TargetSuffix), recursive=True)
        logger.debug('[%s]' % ', '.join(map(str, fmriprep_files)))

        postprocess_files = glob.glob(
            os.path.join(config.PostProcessingOptions.OutputDirectory, sub, '**', 'func',
                         '*' + config.PostProcessingOptions.OutputSuffix), recursive=True)

        for file in bold_files:
            logger.debug('Finding ' + file)
            row = pd.DataFrame(columns=['Subject', 'BIDS_File', 'FMRIPrep_File', 'PostProcessed_File'])

            header = os.path.basename(file).split('_bold.nii.gz')[0]
            logger.debug(header)
            target_fmriprep_file = [tfile for tfile in fmriprep_files if
                                    header in tfile and config.PostProcessingOptions.TargetSuffix in tfile]
            logger.debug('Finding FMRIPrep file' + '[%s]' % ', '.join(map(str, target_fmriprep_file)))
            row.loc[0, 0:2] = [sub, file]

            if target_fmriprep_file:
                row.loc[0, 'FMRIPrep_File'] = target_fmriprep_file
                post_proc_file = [pfile for pfile in postprocess_files if
                                  header in pfile and config.PostProcessingOptions.OutputSuffix in pfile]
                if post_proc_file:
                    row.loc[0, 'PostProcessed_File'] = post_proc_file
            file_list.append(row)

    to_file = pd.concat(file_list, ignore_index=True)
    if output_file is None:
        output_file = os.path.join(os.path.dirname(os.path.abspath(config_file)), "Checker-Output.csv")
    to_file.to_csv(output_file)
