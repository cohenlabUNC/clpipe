import os
import logging
from pathlib import Path

import click
from bids import BIDSLayout, config as bids_config

from .config_json_parser import ClpipeConfigParser, GLMConfigParser
from .batch_manager import BatchManager, Job
from nipype.utils.filemanip import split_filename
from .postprocutils.workflows import build_postprocessing_workflow
from .postprocutils.confounds import prepare_confounds

# This hides a pybids warning
bids_config.set_option('extension_initial_dot', True)

logging.basicConfig()
LOG = logging.getLogger(__name__)

EXIT_MSG = "Exiting postprocess2"
PYBIDS_DB_PATH = "TestFiles/fmriprep_dir"

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), help = """Where to put the postprocessed data. 
    If a configuration file is provided with a output directory, this argument is not necessary.""")
@click.option('-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=True, help = 'Flag to submit commands to the HPC without prompt.')
@click.option('-log_dir', is_flag = True, default=True, help = 'Path to the logging directory.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2_cli(subjects, config_file, glm_config_file, target_dir, output_dir, batch, submit, log_dir, debug):
    postprocess_fmriprep_dir(subjects=subjects, config_file=config_file, glm_config_file=glm_config_file, fmriprep_dir=target_dir, output_dir=output_dir, 
    batch=batch, submit=submit, log_dir=log_dir, debug=debug)

@click.command()
@click.argument('subject_id', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('fmriprep_dir', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('output_dir', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('glm_config', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_subject_cli(subject_id, fmriprep_dir, output_dir, glm_config, log_dir):
    postprocess_subject(subject_id, fmriprep_dir, output_dir, glm_config, log_dir)

def postprocess_subject(subject_id, fmriprep_dir, output_dir, glm_config, log_dir):
    click.echo(f"Processing subject: {subject_id}")

    job = PostProcessSubjectJob(subject_id, fmriprep_dir, output_dir, glm_config, log_dir=log_dir)
    job.run()

def postprocess_fmriprep_dir(subjects=None, config_file=None, glm_config_file=None, fmriprep_dir=None, output_dir=None, 
    batch=False, submit=False, log_dir=None, debug=False):

    # Setup Logging
    if debug: LOG.setLevel(logging.DEBUG)
    LOG.debug(f"Starting postprocessing job targeting: {fmriprep_dir}")
    
    # Handle configuration
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    # Create jobs based on subjects given for processing
    # TODO: PYBIDS_DB_PATH should have config arg
    jobs_to_run = PostProcessSubjectJobs(fmriprep_dir, output_dir, subjects, glm_config_file, log_dir, PYBIDS_DB_PATH)

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

    # TODO: add class logger
    def __init__(self, subject_id: str, fmriprep_dir: os.PathLike, out_dir: os.PathLike, 
        glm_config: os.PathLike, log_dir: os.PathLike=None):
        self.subject_id=subject_id
        self.log_dir=log_dir
        self.fmriprep_dir=fmriprep_dir
        
        glm_config = GLMConfigParser(glm_config).config
        self.postprocessing_config = glm_config["GLMSetupOptions"]

        # Create a subject folder for this subject's postprocessing output, if one
        # doesn't already exist
        self.subject_out_dir = out_dir / ("sub-" + subject_id) / "func"
        if not self.subject_out_dir.exists():
            self.subject_out_dir.mkdir(exist_ok=True, parents=True)

        # Create a nipype working directory for this subject, if it doesn't exist
        self.working_dir = self.subject_out_dir / "working"
        if not self.working_dir.exists():
            self.subject_out_dir.mkdir(exist_ok=True)

        # Create a postprocessing logging directory for this subject, if it doesn't exist
        self.log_dir = log_dir / ("sub-" + subject_id)
        if not self.log_dir.exists():
            self.log_dir.mkdir(exist_ok=True)

    def __str__(self):
        return f"Postprocessing Job: {self.subject_id}"

    def run(self):
        self.bids:BIDSLayout = BIDSLayout(self.fmriprep_dir, validate=False)
        
        # Find the subject's confounds file
        # TODO: Need switch here from config to determine if confounds wanted
        self.confounds = self.bids.get(
            subject=self.subject_id, suffix="timeseries", extension=".tsv"
        )[0]

        # Process the subject's confounds
        prepare_confounds(Path(self.confounds), self.subject_out_dir / "confounds.tsv",
            self.postprocessing_config)

        # Find the subject's images to run post_proc on
        self.images_to_process = self.bids.get(
            subject=self.subject_id, return_type="filename", 
            extension="nii.gz", datatype="func", suffix="bold")

        # Find the subject's mask file
        # TODO: Need switch here from config to determine if mask file wanted
        self.mask_image = self.bids.get(
            subject=self.subject_id, suffix="mask", extension=".nii.gz"
        )[0]

        for in_file in self.images_to_process:
            # Calculate the output file name for a given image to process
            _, base, _ = split_filename(in_file)
            out_stem = base + '_postproccessed.nii.gz'
            out_file = os.path.abspath(os.path.join(self.subject_out_dir, out_stem))

            self.wf = build_postprocessing_workflow(self.postprocessing_config, in_file, out_file, 2, 
                name=PostProcessSubjectJob.__class__.__name__, mask_file=self.mask_image,
                base_dir=self.working_dir, crashdump_dir=self.log_dir)

            print(f"Postprocessing image at path {in_file}")
            self.wf.run()

class PostProcessSubjectJobs(CLPipeJob):
    post_process_jobs = []

    # TODO: Add class logger
    def __init__(self, fmriprep_dir, output_dir: os.PathLike, glm_config: os.PathLike, 
        subjects_to_process=None, log_dir: os.PathLike=None, pybids_db_path: os.PathLike=None):
        
        self.output_dir = output_dir

        # Create the root output directory for all subject postprocessing results, if it doesn't yet exist.
        if not output_dir.exists():
            self.output_dir.mkdir()

        self.log_dir = log_dir
        self.glm_config = glm_config
        self.slurm = False
        self.pybids_db_path = pybids_db_path
        self.fmriprep_dir = fmriprep_dir

        # Get the fmriprep_dir as a BIDSLayout object
        if pybids_db_path and not os.path.exists(pybids_db_path):
            print("Indexing fMRIPrep directory...")
        self.bids:BIDSLayout = BIDSLayout(fmriprep_dir, validate=False, database_path=self.pybids_db_path)

        # Choose the subjects to process
        self.subjects_to_process = get_subjects(self.bids, subjects_to_process)
        
        # Create the jobs
        self.create_jobs()

    def create_jobs(self):
        for subject in self.subjects_to_process:
            # Create a new job and add to list of jobs to be run
            job_to_add = PostProcessSubjectJob(subject, self.fmriprep_dir,
                self.output_dir, self.glm_config, log_dir=self.log_dir)
            self.post_process_jobs.append(job_to_add)
        
    def set_batch_manager(self, batch_manager: BatchManager):
        self.slurm=True
        self.batch_manager = batch_manager

        submission_string = """postprocess_subject {subject_id} {fmriprep_dir} {output_dir} {glm_config} {log_dir}"""
        for job in self.post_process_jobs:
            sub_string_temp = submission_string.format(subject_id=job.subject_id,
                                                        fmriprep_dir=self.fmriprep_dir,
                                                        glm_config=self.glm_config,
                                                        output_dir=job.subject_out_dir,
                                                        log_dir=job.log_dir)
            subject_id = Path(job.subject_id).stem

            self.batch_manager.addjob(Job("PostProcessing_" + subject_id, sub_string_temp))

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

        
