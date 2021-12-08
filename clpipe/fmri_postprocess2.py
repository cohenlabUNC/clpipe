import sys
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
from .error_handler import exception_handler

# This hides a pybids warning
bids_config.set_option('extension_initial_dot', True)

logging.basicConfig()
LOG = logging.getLogger(__name__)

EXIT_MSG = "Exiting postprocess2"
PYBIDS_DB_PATH = "TestFiles/fmriprep_dir"


class NoSubjectsFoundError(ValueError):
    pass


class SubjectNotFoundError(ValueError):
    pass

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=True, help = """Where to put the postprocessed data. 
    If a configuration file is provided with a output directory, this argument is not necessary.""")
@click.option('-log_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False, help = 'Path to the logging directory.')
@click.option('-batch/-no-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC without prompt.')

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
    
    try:
        job = PostProcessSubjectJob(subject_id, fmriprep_dir, output_dir, glm_config, log_dir=log_dir)
        job.run()
    except SubjectNotFoundError:
        sys.exit()
    except FileNotFoundError:
        sys.exit()
    
    sys.exit()


def postprocess_fmriprep_dir(subjects=None, config_file=None, glm_config_file=None, fmriprep_dir=None, output_dir=None, 
    batch=False, submit=False, log_dir=None, debug=False):

    # Handle configuration
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    # Make sure any string paths are converted to Path type
    config_file = Path(config_file)
    glm_config_file = Path(glm_config_file)
    fmriprep_dir = Path(fmriprep_dir)
    output_dir = Path(output_dir)
    log_dir = Path(log_dir)

    # Setup Logging
    if debug: 
        LOG.setLevel(logging.DEBUG)
    else:
        sys.excepthook = exception_handler
    LOG.debug(f"Starting postprocessing job targeting: {str(fmriprep_dir)}")
    click.echo(f"Starting postprocessing job targeting: {str(fmriprep_dir)}")

    # Create jobs based on subjects given for processing
    # TODO: PYBIDS_DB_PATH should have config arg
    try:
        jobs_to_run = PostProcessSubjectJobs(fmriprep_dir, output_dir, glm_config_file, subjects, log_dir, PYBIDS_DB_PATH)
    except NoSubjectsFoundError:
        click.echo()
        sys.exit()
    except FileNotFoundError:
        click.echo(f"Invalid fmriprep output path provided: {fmriprep_dir}")
        sys.exit()

    # Setup batch jobs if indicated
    if batch:
        batch_manager = _setup_batch_manager(config)
        jobs_to_run.set_batch_manager(batch_manager)
        
        click.echo(jobs_to_run.batch_manager.print_jobs())

        if submit:
            jobs_to_run.run()
    # Otherwise, process the images locally
    else:
        click.echo(str(jobs_to_run))

        if submit:
            jobs_to_run.run()
    sys.exit()


def _setup_batch_manager(config):
    #TODO: Remove this hardcoded path
    batch_manager = BatchManager(config.config['BatchConfig'], "/nas/longleaf/home/willasc/repos/clpipe/tests/Output-PostProcessing")

    return batch_manager


class PostProcessSubjectJob():
    # TODO: add class logger
    def __init__(self, subject_id: str, fmriprep_dir: os.PathLike, out_dir: os.PathLike, 
        glm_config: os.PathLike, log_dir: os.PathLike=None):
        self.subject_id=subject_id
        self.log_dir=log_dir
        self.fmriprep_dir=fmriprep_dir
        self.out_dir = out_dir

        glm_config = GLMConfigParser(glm_config).config
        self.postprocessing_config = glm_config["GLMSetupOptions"]


    def __str__(self):
        return f"Postprocessing Job: sub-{self.subject_id}"

    def run(self):
        # Open the fmriprep dir and validate that it contains the subject
        try:
            self.bids:BIDSLayout = BIDSLayout(self.fmriprep_dir, validate=False, index_metadata=False)

            if len(self.bids.get(subject=self.subject_id)) == 0:
                snfe = f"Subject {self.subject_id} was not found in fmriprep directory {self.fmriprep_dir}"
                LOG.error(snfe)
                raise SubjectNotFoundError(snfe)
        except FileNotFoundError as fne:
            fnfe = f"Invalid fmriprep output path provided: {fmriprep_dir}"
            LOG.error(fnfe)
            raise fne

        # Create a subject folder for this subject's postprocessing output, if one
        # doesn't already exist
        self.subject_out_dir = self.out_dir / ("sub-" + self.subject_id) / "func"
        if not self.subject_out_dir.exists():
            self.subject_out_dir.mkdir(exist_ok=True, parents=True)

        # Create a nipype working directory for this subject, if it doesn't exist
        self.working_dir = self.subject_out_dir / "working"
        if not self.working_dir.exists():
            self.subject_out_dir.mkdir(exist_ok=True)

        # Create a postprocessing logging directory for this subject, if it doesn't exist
        self.log_dir = self.log_dir / ("sub-" + self.subject_id)
        if not self.log_dir.exists():
            self.log_dir.mkdir(exist_ok=True)
        
        # Find the subject's confounds file
        # TODO: Need switch here from config to determine if confounds wanted
        try:
            self.confounds = self.bids.get(
                subject=self.subject_id, suffix="timeseries", extension=".tsv"
            )[0]
        except IndexError:
            LOG.info(f"Confounds file for subject {self.subject_id} not found.")
            self.confounds = None

        # Process the subject's confounds
        prepare_confounds(Path(self.confounds), self.subject_out_dir / "confounds.tsv",
            self.postprocessing_config)

        # Find the subject's images to run post_proc on
        self.images_to_process = self.bids.get(
            subject=self.subject_id, return_type="filename", 
            extension="nii.gz", datatype="func", suffix="bold")

        # Find the subject's mask file
        # TODO: Need switch here from config to determine if mask file wanted
        try:
            self.mask_image = self.bids.get(
                subject=self.subject_id, suffix="mask", extension=".nii.gz"
            )[0]
            #TODO: Throw multiple masks found exception?
        except IndexError:
            LOG.info(f"Mask image for subject {self.subject_id} not found.")
            self.mask_image = None

        for in_file in self.images_to_process:
            # Calculate the output file name for a given image to process
            _, base, _ = split_filename(in_file)
            out_stem = base + '_postproccessed.nii.gz'
            out_file = os.path.abspath(os.path.join(self.subject_out_dir, out_stem))

            self.wf = build_postprocessing_workflow(self.postprocessing_config, in_file, out_file, 2, 
                name=PostProcessSubjectJob.__class__.__name__, mask_file=self.mask_image,
                base_dir=self.working_dir, crashdump_dir=self.log_dir)

            LOG.info(f"Postprocessing image at path {in_file}")
            self.wf.run()


def _get_subjects(fmriprep_dir: BIDSLayout, subjects):   
    # If no subjects were provided, use all subjects in the fmriprep directory
    if subjects is None or len(subjects) == 0:
        subjects = fmriprep_dir.get_subjects()
        if len(subjects) == 0:
            no_subjects_found_str = f"No subjects found to parse at: {fmriprep_dir.root}"
            LOG.error(no_subjects_found_str)
            raise NoSubjectsFoundError(no_subjects_found_str)

    return subjects


class PostProcessSubjectJobs():
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
            LOG.info("Indexing fMRIPrep directory...")
        
        try:
            self.bids:BIDSLayout = BIDSLayout(fmriprep_dir, validate=False, database_path=self.pybids_db_path, index_metadata=False)
        except FileNotFoundError as fne:
            LOG.error(fne)
            raise fne

        # Choose the subjects to process
        self.subjects_to_process = _get_subjects(self.bids, subjects_to_process)
        
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
        return "\n".join(str(i) for i in self.post_process_jobs)

    def run(self):
        if self.slurm:
            self.batch_manager.submit_jobs()
        else:
            for job in self.post_process_jobs:
                job.run()
        
