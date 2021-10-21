import os
import logging
from pathlib import Path

import click
import nipype.pipeline.engine as pe
from bids import BIDSLayout, layout, config as bids_config

from .config_json_parser import ClpipeConfigParser
from .batch_manager import BatchManager, Job
from .utils import parse_dir_subjects
from nipype.utils.filemanip import split_filename
# from .postprocutils.nodes import ButterworthFilter
# from .postprocutils.workflows import build_10000_global_median_workflow, build_100_voxel_mean_workflow

# This hides a pybids warning
bids_config.set_option('extension_initial_dot', True)

logging.basicConfig()
LOG = logging.getLogger(__name__)

EXIT_MSG = "Exiting postprocess2"

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), help = """Where to put the postprocessed data. 
    If a configuration file is provided with a output directory, this argument is not necessary.""")
@click.option('-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=True, help = 'Flag to submit commands to the HPC without prompt.')
@click.option('-log_dir', is_flag = True, default=True, help = 'Path to the logging directory.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2_cli(subjects, target_dir, output_dir, batch, submit, debug):
    postprocess_fmriprep_dir(subjects=subjects, fmriprep_dir=target_dir, output_dir=output_dir, batch=batch, submit=submit, debug=debug)

@click.command()
@click.argument('target_image', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('output_path', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_image_cli(target_image, output_path, log_dir):
    postprocess_image(target_image, output_path, log_dir)

def postprocess_image(target_image, output_path, log_dir):
    click.echo(f"Processing image: {target_image}")

    job = PostProcessSubjectJob(target_image, output_path, log_dir)
    job.run()

def postprocess_fmriprep_dir(subjects=None, fmriprep_dir=None, output_dir=None, batch=False, submit=False, log_dir=None, debug=False):

    # Setup Logging
    if debug: LOG.setLevel(logging.DEBUG)
    LOG.debug(f"Starting postprocessing job targeting: {fmriprep_dir}")
    
    # Handle configuration
    config = ClpipeConfigParser()

    # Create jobs based on subjects given for processing
    jobs_to_run = PostProcessSubjectJobs(fmriprep_dir, output_dir, subjects, log_dir)

    # Setup batch jobs if indicated
    if batch or click.confirm('Would you to process these subjects on the HPC? (Choose "N" for local)'):
        batch_manager = setup_batch_manager(config)
        jobs_to_run.set_batch_manager(batch_manager)
        click.echo(jobs_to_run.batch_manager.print_jobs())

        if submit or click.confirm('Submit these jobs to the HPC?'):
            jobs_to_run.run()
    # Otherwise, process the images locally
    else:
        click.echo(str(jobs_to_run))

        if submit or click.confirm('Run these jobs locally?'):
            jobs_to_run.run()

def setup_batch_manager(config):
    batch_manager = BatchManager(config.config['BatchConfig'], "/nas/longleaf/home/willasc/repos/clpipe/tests/Output-PostProcessing")

    return batch_manager

# TODO: throw exceptions here instead of exiting
def get_subjects(fmriprep_dir: BIDSLayout, subjects):   
    # If no subjects were provided, use all subjects in the fmriprep directory
    if subjects is None:
        try:
            subjects = fmriprep_dir.get_subjects()
            if len(subjects) == 0:
                no_subjects_found_str = f"No subjects found to parse at: {fmriprep_dir.root}"
                print(no_subjects_found_str)
                LOG.error(no_subjects_found_str)
                print(EXIT_MSG)
                exit()
        except FileNotFoundError as fne:
            print(f"Invalid path provided: {fmriprep_dir.root}")
            LOG.debug(fne)
            print(EXIT_MSG)
            exit()
    # If subjects were provided, return those subjects
    if len(subjects) == 1:
        processing_msg = f"Processing subject: {subjects[0]}"
        LOG.info(processing_msg)
        print(processing_msg)
    else:
        processing_msg = f"Processing subjects: {subjects}"
        LOG.info(processing_msg)
        print(processing_msg)

    return subjects

class CLPipeJob():
    pass

class PostProcessSubjectJob(CLPipeJob):
    #wf: pe.Workflow = None
    
    # TODO: add class logger
    def __init__(self, in_file: os.PathLike, out_file: os.PathLike, log_dir: os.PathLike=None):
        self.in_file=in_file
        self.out_file=out_file
        self.log_dir=log_dir
        
        # self.wf = pe.Workflow(name=PostProcessSubjectJob.__class__.__name__ + subject_id)
        # if log_dir is not None:
        #     self.wf.config['execution']['crashdump_dir'] = crashdump_dir
        # self._compose_workflow()

    def _compose_workflow(self):
        pass
        # voxel_mean_wf = build_100_voxel_mean_workflow(None, self.out_file, base_dir=self.wf.base_dir)
        # butterworth_node = pe.Node(ButterworthFilter(in_file=self.in_file,
        #                         hp=.008,lp=-1,order=2,tr=2), name="butterworth_filter")
    
        # self.wf.connect([
        #     (butterworth_node, voxel_mean_wf, [("out_file","mean.in_file"),
        #                                        ("out_file","mul100.in_file")])
        # ])


    def __str__(self):
        return f"Postprocessing Job: {self.in_file}"

    def run(self):
        print(f"Postprocessing image at path {self.in_file}")
        #self.wf.run()

class PostProcessSubjectJobs(CLPipeJob):
    post_process_jobs = []

    # TODO: Add class logger
    def __init__(self, fmriprep_dir:BIDSLayout, output_dir: os.PathLike, subjects_to_process=None, log_dir: os.PathLike=None):
        self.log_dir = log_dir
        self.output_dir = output_dir
        self.slurm = False
        
        # Get the fmriprep_dir as a BIDSLayout object
        # Currently cannot get index persistance below to work due to dependency issues
        # db_path = "tests/fmriprep_dir"
        print("Indexing fMRIPrep directory...")
        self.fmriprep_dir:BIDSLayout = BIDSLayout(fmriprep_dir, validate=False)

        # Choose the subjects to process
        self.subjects_to_process = get_subjects(self.fmriprep_dir, subjects_to_process)
        
        # Create the jobs
        self.create_jobs()

    def create_jobs(self):
        # Gather all image paths to be processed with pybids query
        images_to_process = self.fmriprep_dir.get(
            subject=self.subjects_to_process, return_type="filename", 
            extension="nii.gz", datatype="func", suffix="bold")

        for in_file in images_to_process:   
            # Calculate the output file name for a given image to process
            _, base, _ = split_filename(in_file)
            out_stem = base + '_filtered.nii'
            out_file = os.path.abspath(os.path.join(self.output_dir, out_stem))

            # Create a new job and add to list of jobs to be run
            job_to_add = PostProcessSubjectJob(in_file, out_file, log_dir=self.log_dir)
            self.post_process_jobs.append(job_to_add)

    def set_batch_manager(self, batch_manager: BatchManager):
        self.slurm=True
        self.batch_manager = batch_manager

        submission_string = """postprocess_image {image_path} {out_file} {log_dir}"""
        for job in self.post_process_jobs:
            sub_string_temp = submission_string.format(image_path=job.in_file,
                                                        out_file=job.out_file,
                                                        log_dir=job.log_dir)
            image_stem = Path(job.in_file).stem

            self.batch_manager.addjob(Job("PostProcessing_" + image_stem, sub_string_temp))

        self.batch_manager.createsubmissionhead()
        self.batch_manager.compilejobstrings()

    def __str__(self):
        out = ""
        for job in self.post_process_jobs:
            out += str(job) + '\n'
        return out

    def run(self):
        if self.slurm:
            self.batch_manager.submit_jobs()
        else:
            for job in self.post_process_jobs:
                job.run()

        
