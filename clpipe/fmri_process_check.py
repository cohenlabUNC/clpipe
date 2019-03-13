import click
from .config_json_parser import ConfigParser
import pandas as pd
import os
import glob
import logging
from .error_handler import exception_handler
import sys


@click.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), required=True,
              help='The configuration file for the current data processing setup.')
@click.option('-output_file',
              help='Path and name of the output archive. Defaults to current working directory and "Report_Archive.zip"')
@click.option('-debug', is_flag=True, help='Print traceback and detailed processing messages.')
def fmri_process_check(config_file, output_file=None, debug=False):
    """This command checks a BIDS dataset, an fMRIprep'ed dataset and a postprocessed dataset, and creates a CSV file that lists all scans across all three datasets. Use to find which subjects/scans failed processing."""
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ConfigParser()
    config.config_updater(config_file)
    config.validate_config()

    sublist = [o for o in os.listdir(config.config['PostProcessingOptions']['TargetDirectory'])
               if os.path.isdir(
            os.path.join(config.config['PostProcessingOptions']['TargetDirectory'], o)) and 'sub-' in o]
    file_list = []
    for sub in sublist:
        logging.debug("Inspecting " + sub)
        bold_files = glob.glob(
            os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], sub, '**', 'func', '*.nii.gz'),
            recursive=True)
        fmriprep_files = glob.glob(
            os.path.join(config.config['PostProcessingOptions']['TargetDirectory'], sub, '**', 'func',
                         '*' + config.config['PostProcessingOptions']['TargetSuffix']), recursive=True)
        logging.debug('[%s]' % ', '.join(map(str, fmriprep_files)))

        postprocess_files = glob.glob(
            os.path.join(config.config['PostProcessingOptions']['OutputDirectory'], sub, '**', 'func',
                         '*' + config.config['PostProcessingOptions']['OutputSuffix']), recursive=True)

        for file in bold_files:
            logging.debug('Finding ' + file)
            row = pd.DataFrame(columns=['Subject', 'BIDS_File', 'FMRIPrep_File', 'PostProcessed_File'])

            header = os.path.basename(file).split('_bold.nii.gz')[0]
            logging.debug(header)
            target_fmriprep_file = [tfile for tfile in fmriprep_files if
                                    header in tfile and config.config['PostProcessingOptions']['TargetSuffix'] in tfile]
            logging.debug('Finding FMRIPrep file' + '[%s]' % ', '.join(map(str, target_fmriprep_file)))
            row.loc[0, 0:2] = [sub, file]

            if target_fmriprep_file:
                row.loc[0, 'FMRIPrep_File'] = target_fmriprep_file
                post_proc_file = [pfile for pfile in postprocess_files if
                                  header in pfile and config.config['PostProcessingOptions'][
                                      'OutputSuffix'] in pfile]
                if post_proc_file:
                    row.loc[0, 'PostProcessed_File'] = post_proc_file
            file_list.append(row)

    to_file = pd.concat(file_list, ignore_index=True)
    if output_file is None:
        output_file = os.path.join(os.path.dirname(os.path.abspath(config_file)), "Checker-Output.csv")
    to_file.to_csv(output_file)
