import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from nipype.interfaces.fsl.utils import ExtractROI
import os
import parse
import glob
from .error_handler import exception_handler
import sys
import logging


@click.command()
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="The configuration file for the study, use if you have a custom batch configuration.",
)
@click.option(
    "-fmap_cleanup_tp",
    default=None,
    help="The number of timepoints from the beginning of the scan to include.",
)
@click.option("-bids_dir", help="The dicom info output file name.")
@click.option(
    "-subject",
    required=False,
    help="A subject  to convert using the supplied configuration file.  Use to convert single subjects, else leave empty",
)
@click.option("-single", is_flag=True, default=False)
@click.option("-submit", is_flag=True, default=False, help="Submit jobs to HPC")
def fmap_cleanup(
    fmap_cleanup_tp=None,
    bids_dir=None,
    config_file=None,
    subject=None,
    single=None,
    submit=None,
):
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    if bids_dir is None:
        bids_dir = config.config["FMRIPrepOptions"]["BIDSDirectory"]

    sub_dirs = [sub for sub in os.listdir(bids_dir) if "sub-" in sub]

    if subject is not None:
        sub_dirs = [sub for sub in sub_dirs if subject in sub]

    submission_string = """fmap_cleanup -config_file {config_file} -fmap_cleanup_tp {fmap_tp}  -subject {subject} -single"""

    batch_manager = BatchManager(
        config.config["BatchConfig"],
        config.config["DICOMToBIDSOptions"]["LogDirectory"],
    )
    batch_manager.createsubmissionhead()
    batch_manager.update_mem_usage(config.config["DICOMToBIDSOptions"]["MemUsage"])
    batch_manager.update_time(config.config["DICOMToBIDSOptions"]["TimeUsage"])
    batch_manager.update_nthreads(config.config["DICOMToBIDSOptions"]["CoreUsage"])

    fmap_tp = config.config["FMRIPrepOptions"]["FMapCleanupROIs"]

    if fmap_cleanup_tp is not None:
        fmap_tp = fmap_cleanup_tp

    for sub in sub_dirs:
        target_folder = os.path.join([bids_dir, sub])
        if not single:
            job_id = "fmapclean" + sub
            job1 = Job(
                job_id,
                submission_string.format(
                    config_file=config_file,
                    subject=sub.replace("sub-", ""),
                    fmap_tp=str(fmap_tp),
                ),
            )
            batch_manager.addjob(job1)

            batch_manager.compilejobstrings()
            if submit:
                batch_manager.submit_jobs()
            else:
                batch_manager.print_jobs()
        else:
            _fmap_cleanup(target_folder, fmap_tp)


def _fmap_cleanup(sub_folder, fmap_tp):
    files = glob.glob(os.path.join([sub_folder, "**", "*"]), recursive=True)
    files = [os.path.abspath(file) for file in files if "epi.nii" in file]
    logging.debug(files)
    for file in files:
        fslroi = ExtractROI(in_file=file, roi_file=file, t_min=0, t_size=fmap_tp)
        logging.debug(fslroi.cmdline)
