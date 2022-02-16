import sys
import os
import logging
import json
from pathlib import Path

import click
from bids import BIDSLayout, BIDSLayoutIndexer, config as bids_config

from .config_json_parser import ClpipeConfigParser, GLMConfigParser
from .batch_manager import BatchManager, Job
from nipype.utils.filemanip import split_filename
from .postprocutils.workflows import build_postprocessing_workflow, build_confound_postprocessing_workflow
from .error_handler import exception_handler

# This hides a pybids warning
bids_config.set_option('extension_initial_dot', True)

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

class NoSubjectTaskFoundError(ValueError):
    pass

class NoImagesFoundError(ValueError):
    pass

class NoSubjectsFoundError(ValueError):
    pass

class SubjectNotFoundError(ValueError):
    pass

class ConfoundsNotFoundError(ValueError):
    pass

class MixingFileNotFoundError(ValueError):
    pass

class NoiseFileNotFoundError(ValueError):
    pass

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required=True,
              help='Use a given configuration file.')
@click.option('-fmriprep_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False, help = """Where to put the postprocessed data. 
    If a configuration file is provided with a output directory, this argument is not necessary.""")
@click.option('-log_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False, help = 'Path to the logging directory.')
@click.option('-index_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False,
              help='Give the path to an existing pybids index database.')
@click.option('-refresh_index', is_flag=True, default=False, required=False,
              help='Refresh the pybids index database to reflect new fmriprep artifacts.')
@click.option('-batch/-no-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC without prompt.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2_cli(subjects, config_file, fmriprep_dir, output_dir, batch, submit, log_dir, index_dir, refresh_index, debug):
    postprocess_fmriprep_dir(subjects=subjects, config_file=config_file, fmriprep_dir=fmriprep_dir, output_dir=output_dir, 
    batch=batch, submit=submit, log_dir=log_dir, pybids_db_path=index_dir, refresh_index=refresh_index, debug=debug)


@click.command()
@click.argument('subject_id')
@click.argument('bids_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('fmriprep_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('output_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('config_file', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('index_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_subject_cli(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, log_dir):
    postprocess_subject(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, log_dir)


def postprocess_subject(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, log_dir):
    click.echo(f"Processing subject: {subject_id}")
    
    try:
        job = PostProcessSubjectJob(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, pybids_db_path=index_dir, log_dir=log_dir)
        job()
    except SubjectNotFoundError:
        sys.exit()
    except ValueError:
        sys.exit()
    except FileNotFoundError:
        sys.exit()
    
    sys.exit()

def postprocess_fmriprep_dir(subjects=None, config_file=None, bids_dir=None, fmriprep_dir=None, output_dir=None, 
    batch=False, submit=False, log_dir=None, pybids_db_path=None, refresh_index=False, debug=False):

    config=None

    # Get postprocessing configuration from general config
    try:
        if not config_file:
            raise ValueError("No config file provided")
        else:
            configParser = ClpipeConfigParser()
            configParser.config_updater(config_file)
            config = configParser.config
            config_file = Path(config_file)
    except ValueError:
        sys.exit()

    if fmriprep_dir:
        fmriprep_dir = Path(fmriprep_dir)
    else:
        fmriprep_dir = Path(config["FMRIPrepOptions"]["OutputDirectory"]) / "fmriprep"

    if bids_dir:
        bids_dir = Path(bids_dir)
    else:
        bids_dir = Path(config["FMRIPrepOptions"]["BIDSDirectory"])

    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = Path(config["ProjectDirectory"]) / "data_postproc2"

    if log_dir:
        log_dir = Path(log_dir)
    else:
        log_dir = Path(config["ProjectDirectory"]) / "logs" / "postproc2_logs"

    if pybids_db_path:
        pybids_db_path = Path(pybids_db_path)
    else:
        pybids_db_path = Path(config["ProjectDirectory"]) / "bids_index"

    slurm_log_dir = log_dir / "slurm_out"
    if not slurm_log_dir.exists():
            LOG.info(f"Creating subject working directory: {slurm_log_dir}")
            slurm_log_dir.mkdir(exist_ok=True, parents=True)

    # Setup Logging
    if debug: 
        LOG.setLevel(logging.DEBUG)
    else:
        sys.excepthook = exception_handler
    LOG.debug(f"Preparing postprocessing job targeting: {str(fmriprep_dir)}")
    click.echo(f"Preparing postprocessing job targeting: {str(fmriprep_dir)}")

    # Create jobs based on subjects given for processing
    # TODO: PYBIDS_DB_PATH should have config arg
    try:
        jobs_to_run = PostProcessSubjectJobs(bids_dir, fmriprep_dir, output_dir, config_file, subjects_to_process=subjects, 
            log_dir=log_dir, pybids_db_path=pybids_db_path, refresh_index=refresh_index)
    except NoSubjectsFoundError:
        sys.exit()
    except FileNotFoundError:
        sys.exit()

    # Setup batch jobs if indicated
    if batch:
        batch_manager = _setup_batch_manager(config, slurm_log_dir)
        jobs_to_run.set_batch_manager(batch_manager)
        
        click.echo(jobs_to_run.batch_manager.print_jobs())

        if submit:
            jobs_to_run()
    # Otherwise, process the images locally
    else:
        click.echo(str(jobs_to_run))

        if submit:
            jobs_to_run()
    sys.exit()


def _setup_batch_manager(config, log_dir):
    batch_manager = BatchManager(config['BatchConfig'], log_dir)
    batch_manager.update_mem_usage(config['PostProcessingOptions2']['BatchOptions']['MemoryUsage'])
    batch_manager.update_time(config['PostProcessingOptions2']['BatchOptions']['TimeUsage'])
    batch_manager.update_nthreads(config['PostProcessingOptions2']['BatchOptions']['NThreads'])
    batch_manager.update_email(config["EmailAddress"])

    return batch_manager

def _get_bids(bids_dir: os.PathLike, validate=False, database_path: os.PathLike=None, fmriprep_dir: os.PathLike=None, 
                index_metadata=False, refresh=False) -> BIDSLayout:
    try:
        database_path = Path(database_path)
        
        # Use an existing pybids database, and user did not request an index refresh
        if database_path.exists() and not refresh:
            LOG.info(f"Using existing BIDS index: {database_path}")
            return BIDSLayout(database_path=database_path)
        # Index from scratch (slow)
        else:
            indexer = BIDSLayoutIndexer(validate=validate, index_metadata=index_metadata)
            LOG.info(f"Indexing BIDS directory: {bids_dir}")
            print("Indexing BIDS directory - this can take a few minutes...")

            if fmriprep_dir:
                return BIDSLayout(bids_dir, validate=validate, indexer=indexer, database_path=database_path, derivatives=fmriprep_dir, reset_database=refresh)
            else:
                return BIDSLayout(bids_dir, validate=validate, indexer=indexer, database_path=database_path, reset_database=refresh)
    except FileNotFoundError as fne:
        LOG.error(fne)
        raise fne

class PostProcessSubjectJob():
    
    def __init__(self, subject_id: str, bids_dir: os.PathLike, fmriprep_dir: os.PathLike, out_dir: os.PathLike, 
        config_file: os.PathLike, pybids_db_path: os.PathLike=None, log_dir: os.PathLike=None):
        
        self.subject_id = subject_id
        self.bids_dir = Path(bids_dir)
        self.pybids_db_path = pybids_db_path
        self.fmriprep_dir = Path(fmriprep_dir)
        self.log_dir=Path(log_dir)
        self.out_dir = Path(out_dir)
        self.config_file = Path(config_file)
        self.postprocessing_config = None

        self.setup_logger()

    def setup_config(self):
        # Get postprocessing configuration from general config
        
        LOG.info(f"Ingesting configuration: {self.config_file}")
        configParser = ClpipeConfigParser()
        configParser.config_updater(self.config_file)
        self.postprocessing_config = configParser.config["PostProcessingOptions2"]

    def load_bids_dir(self):
        # Open the bids dir and validate that it contains the subject
        self.logger.info(f"Checking fmri output for requested subject in: {self.bids_dir}")
        try:
            self.bids:BIDSLayout = _get_bids(self.bids_dir, database_path=self.pybids_db_path, fmriprep_dir=self.fmriprep_dir)

            if len(self.bids.get(subject=self.subject_id, scope="derivatives")) == 0:
                snfe = f"Subject {self.subject_id} was not found in fmri output directory {self.bids_dir}"
                self.logger.error(snfe)
                raise SubjectNotFoundError(snfe)
        except FileNotFoundError as fne:
            fnfe = f"Invalid bids output path provided: {self.bids_dir}"
            self.logger.error(fnfe, exc_info=True)
            raise fne

    def setup_directories(self):
        # Create a subject folder for this subject's postprocessing output, if one
        # doesn't already exist
        self.subject_out_dir = self.out_dir / ("sub-" + self.subject_id) / "func"
        if not self.subject_out_dir.exists():
            self.logger.info(f"Creating subject directory: {self.subject_out_dir}")
            self.subject_out_dir.mkdir(exist_ok=True, parents=True)

        # Create a nipype working directory for this subject, if it doesn't exist
        self.working_dir = self.subject_out_dir / "working"
        if not self.working_dir.exists():
            self.logger.info(f"Creating subject working directory: {self.working_dir}")
            self.subject_out_dir.mkdir(exist_ok=True)

        # Create a postprocessing logging directory for this subject, if it doesn't exist
        self.log_dir = self.log_dir / ("sub-" + self.subject_id)
        if not self.log_dir.exists():
            self.logger.info(f"Creating subject log directory: {self.log_dir}")
            self.log_dir.mkdir(exist_ok=True)

    def setup_file_logger(self):
        # Create log handler
        f_handler = logging.FileHandler(self.log_dir / f'sub-{self.subject_id}.log')
        f_handler.setLevel(logging.DEBUG)
        
        # Create log format
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)

        # Add handler to the logger
        self.logger.addHandler(f_handler)

    def setup_logger(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}.sub-{self.subject_id}")
        self.logger.setLevel(logging.INFO)
        
        # Create log handler
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)

        # Create log formatter to add to handler
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        
        # Add handler to logger
        self.logger.addHandler(c_handler)

    def build_image_jobs(self):
        self.logger.info(f"Searching for images to process")
        # Find the subject's images to run post_proc on
        try:
            images_to_process = self.bids.get(
                subject=self.subject_id, extension="nii.gz", datatype="func", 
                suffix="bold", desc="preproc", scope="derivatives")

        except IndexError:
            raise NoImagesFound(f"No preproc BOLD image for subject {self.subject_id} found.")

        if len(images_to_process) == 0:
            raise NoImagesFoundError(f"No preproc BOLD imagess found for sub-{self.subject_id}.")

        self.logger.info(f"Found images: {len(images_to_process)}")

        self.logger.info(f"Building image jobs")
        self.image_jobs = []
        for image in images_to_process:
            try:
                image_entities = image.get_entities()

                task = image_entities['task']
                
                try:
                    run = image_entities['run']
                except KeyError:
                    run = None

                self.image_jobs.append(PostProcessImage(self.subject_id, task, run, image.path, self.bids, self.subject_out_dir,
                    self.postprocessing_config, working_dir = self.working_dir, log_dir = self.log_dir))
            except ConfoundsNotFoundError as cnfe:
                self.logger.error(cnfe)
            except NoiseFileNotFoundError as nfnfe:
                self.logger.error(nfnfe)
            except MixingFileNotFoundError as mfnfe:
                self.logger.error(mfnfe)

        for image_job in self.image_jobs:
            self.logger.info(f"Job: {image_job}")
        self.logger.info(f"Built {len(self.image_jobs)} image jobs")

    def setup(self):
        self.setup_config()
        self.setup_directories()
        self.setup_file_logger()
        self.load_bids_dir()
        self.build_image_jobs()
        for image in self.image_jobs:
            image.setup()

    def run(self):
        self.logger.info(f"Running {len(self.image_jobs)} image jobs")
        for image_job in self.image_jobs:
            image_job.run()
        self.logger.info(f"Image jobs completed")

    def __call__(self):
        self.setup()
        self.run()

class PostProcessImage():
    def __init__(self, subject_id:str, task: str, run_num: str, image_path: os.PathLike, bids: BIDSLayout, out_dir: os.PathLike, 
        postprocessing_config: dict, working_dir: os.PathLike=None, log_dir: os.PathLike=None):
        self.subject_id = subject_id
        self.task = task
        self.run_num = run_num
        self.image_path = Path(image_path)
        self.image_file_name = self.image_path.stem
        self.bids = bids
        self.working_dir = Path(working_dir)
        self.log_dir = Path(log_dir)
        self.out_dir = Path(out_dir)
        self.postprocessing_config = postprocessing_config
        self.confounds = None
        self.mixing_file = None
        self.noise_file = None
        self.wf = None
        self.confounds_wf = None

        self.name = f"Subject_{self.subject_id}_Task_{self.task}"
        if self.run_num: self.name += f"_Run_{self.run_num}"

        self.setup_logger()

    def __str__(self):
        return f"Postprocessing Job: {self.image_file_name}"

    def get_confounds(self):
        # Find the subject's confounds file
        
        self.logger.info("Searching for confounds file")
        try:
            self.confounds = self.bids.get(
                subject=self.subject_id, task=self.task, run=self.run_num, return_type="filename", extension=".tsv",
                    desc="confounds", scope="derivatives"
            )[0]
            self.logger.info(f"Confound file found: {self.confounds}")
        except IndexError:
            raise ConfoundsNotFoundError(f"Confound file for sub-{self.subject_id} task-{self.task} run-{self.run_num} not found.")

    def get_mask(self):
        # Find the subject's mask file
        self.logger.info("Searching for mask file")
        try:
            self.mask_image = self.bids.get(
                subject=self.subject_id, task=self.task, run=self.run_num, suffix="mask", extension=".nii.gz", datatype="func", return_type="filename",
                    desc="brain", scope="derivatives"
            )[0]
            self.logger.info(f"Mask file found: {self.mask_image}")
            #TODO: Notify if mask not found
        except IndexError:
            self.logger.warn(f"Mask image for subject {self.subject_id} task-{self.task} not found.")
            self.mask_image = None

    def get_aroma_files(self):
        # Find the subject's aroma files
        if "AROMARegression" not in self.postprocessing_config["ProcessingSteps"]: return

        self.logger.info("Searching for MELODIC mixing file")
        try:
            self.mixing_file = self.bids.get(
                subject=self.subject_id, task=self.task, run=self.run_num, suffix="mixing", extension=".tsv", return_type="filename",
                    desc="MELODIC", scope="derivatives"
            )[0]
            self.logger.info(f"MELODIC mixing file found: {self.mixing_file}")
        except IndexError:
            raise MixingFileNotFoundError(f"MELODIC mixing file for sub-{self.subject_id} task-{self.task} not found.")

        self.logger.info("Searching for AROMA noise ICs file")
        try:
            self.noise_file = self.bids.get(
                subject=self.subject_id, task=self.task, run=self.run_num, suffix="AROMAnoiseICs", extension=".csv", return_type="filename",
                    scope="derivatives"
            )[0]
            self.logger.info(f"AROMA noise ICs file found: {self.noise_file}")
        except IndexError:
            raise NoiseFileNotFoundError(f"AROMA noise ICs file for sub-{self.subject_id} task-{self.task} not found.")

    def setup_logger(self):
        self.logger = logging.getLogger(f"{self.__str__()}")
        self.logger.setLevel(logging.INFO)
        
        # Create log handler
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)

        # Create log formatter to add to handler
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        
        # Add handler to logger
        self.logger.addHandler(c_handler)

    def get_tr(self):
        # To get the TR, we do another, similar query to get the sidecar and open it as a dict, because indexing metadata in
        # pybids is too slow to be worth just having the TR available
        # This can probably be done in just one query combined with the above
        image_to_process_json = self.bids.get(
            subject=self.subject_id, task=self.task, extension=".json", datatype="func", 
            suffix="bold", desc="preproc", scope="derivatives", return_type="filename")[0]

        with open(image_to_process_json) as sidecar_file:
            sidecar_data = json.load(sidecar_file)
            self.tr = sidecar_data["RepetitionTime"]

    def setup_confounds_workflow(self):
        if not self.postprocessing_config["ConfoundOptions"]["Include"]: return

        # TODO: Run this async or batch
        self.logger.info(f"Processing confounds for sub-{self.subject_id} task-{self.task}")
        self.get_confounds()
        confound_suffix = self.postprocessing_config["ConfoundOptions"]["ProcessedConfoundsSuffix"]

        # Calculate the output file name
        base, image_name, exstension = split_filename(self.confounds)
        out_stem = image_name + '_' + confound_suffix + '.tsv'
        self.confound_out_file = os.path.abspath(os.path.join(self.out_dir, out_stem))
        
        self.logger.debug(f"Postprocessed confound out file: {self.confound_out_file}")
    
        try:
            self.confounds_wf = build_confound_postprocessing_workflow(self.postprocessing_config, confound_file = self.confounds,
                out_file=self.confound_out_file, tr=self.tr,
                name=f"{self.name}_Confound_Postprocessing_Pipeline",
                mixing_file=self.mixing_file, noise_file=self.noise_file,
                base_dir=self.working_dir, crashdump_dir=self.log_dir)
        except ValueError as ve:
            self.logger.warn(ve)
            self.logger.warn("Skipping confounds processing")

    def setup_workflow(self):
        # Calculate the output file name
        base, image_name, exstension = split_filename(self.image_file_name)
        out_stem = image_name + '_postproccessed.nii.gz'
        out_file = os.path.abspath(os.path.join(self.out_dir, out_stem))

        self.logger.info(f"Building postprocessing workflow for image: {self.image_file_name}")
        self.wf = build_postprocessing_workflow(self.postprocessing_config, in_file=self.image_path, out_file=out_file,
            name=f"{self.name}_Postprocessing_Pipeline",
            mask_file=self.mask_image, confound_file = self.confounds,
            mixing_file=self.mixing_file, noise_file=self.noise_file,
            tr=self.tr, 
            base_dir=self.working_dir, crashdump_dir=self.log_dir)

    def setup(self):
        self.get_aroma_files()
        self.get_mask()
        self.get_tr()
        self.setup_workflow()
        self.setup_confounds_workflow()

    def run(self):
        self.logger.info(f"Running postprocessing workflow for image: {self.image_file_name}")
        self.wf.run()
        self.logger.info(f"Postprocessing workflow complete for image: {self.image_file_name}")

        # Draw the workflow's process graph if requested in config
        if self.postprocessing_config["WriteProcessGraph"]:
            graph_image_path = self.out_dir / "process_graph.dot"
            self.logger.info(f"Drawing workflow graph: {graph_image_path}")
            self.wf.write_graph(dotfilename = graph_image_path, graph2use="colored")

        # Process confounds, if this option was included
        if self.confounds_wf:
            self.logger.info("Postprocessing confounds")
            self.confounds_wf.run()
            
            # Draw the workflow's process graph if requested in config
            if self.postprocessing_config["WriteProcessGraph"]:
                graph_image_path = self.out_dir / "confounds_process_graph.dot"
                self.logger.info(f"Drawing confounds workflow graph: {graph_image_path}")
                self.confounds_wf.write_graph(dotfilename = graph_image_path, graph2use="colored")

    def __call__(self):
        self.setup()
        self.run()


def _get_subjects(bids_dir: BIDSLayout, subjects):   
    # If no subjects were provided, use all subjects in the fmriprep directory
    if subjects is None or len(subjects) == 0:
        subjects = bids_dir.get_subjects(scope='derivatives')
        if len(subjects) == 0:
            no_subjects_found_str = f"No subjects found to parse at: {bids_dir.root}"
            LOG.error(no_subjects_found_str)
            raise NoSubjectsFoundError(no_subjects_found_str)

    return subjects


class PostProcessSubjectJobs():
    post_process_jobs = []

    # TODO: Add class logger
    def __init__(self, bids_dir, fmriprep_dir, output_dir: os.PathLike, config_file: os.PathLike, 
        subjects_to_process=None, log_dir: os.PathLike=None, pybids_db_path: os.PathLike=None, refresh_index=False):
        
        self.setup_logger()

        self.output_dir = output_dir

        # Create the root output directory for all subject postprocessing results, if it doesn't yet exist.
        if not output_dir.exists():
            self.output_dir.mkdir()

        self.log_dir = log_dir
        self.config_file = config_file
        self.slurm = False
        self.pybids_db_path = pybids_db_path
        self.bids_dir = bids_dir
        self.fmriprep_dir = fmriprep_dir

        self.bids:BIDSLayout = _get_bids(self.bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir, refresh=refresh_index)

        # Choose the subjects to process
        self.logger.info("Searching for subjects to process")
        self.subjects_to_process = _get_subjects(self.bids, subjects_to_process)
        
        # Create the jobs
        self.create_jobs()

    def create_jobs(self):
        self.logger.info("Creating postprocessing jobs")
        for subject in self.subjects_to_process:
            # Create a new job and add to list of jobs to be run
            job_to_add = PostProcessSubjectJob(subject, self.bids_dir, self.fmriprep_dir,
                self.output_dir, self.config_file, pybids_db_path=self.pybids_db_path, log_dir=self.log_dir)
            self.post_process_jobs.append(job_to_add)
        self.logger.info(f"Created {len(self.post_process_jobs)} postprocessing jobs")
        
    def set_batch_manager(self, batch_manager: BatchManager):
        self.logger.info("Setting up batch management")
        
        self.slurm=True
        self.batch_manager = batch_manager

        submission_string = """postprocess_subject {subject_id} {bids_dir} {fmriprep_dir} {output_dir} {config_file} {index_dir} {log_dir}"""
        for job in self.post_process_jobs:
            sub_string_temp = submission_string.format(subject_id=job.subject_id,
                                                        bids_dir=self.bids_dir,
                                                        fmriprep_dir=self.fmriprep_dir,
                                                        config_file=self.config_file,
                                                        index_dir=self.pybids_db_path,
                                                        output_dir=self.output_dir,
                                                        log_dir=self.log_dir)
            subject_id = Path(job.subject_id).stem

            self.batch_manager.addjob(Job("PostProcessing_" + subject_id, sub_string_temp))

        self.batch_manager.createsubmissionhead()
        self.batch_manager.compilejobstrings()

    def __str__(self):
        return "\n".join(str(i) for i in self.post_process_jobs)

    def setup_directories(self):
        # Create a postproc output directory, if it doesn't exist
        if not self.output_dir.exists():
            self.logger.info(f"Creating postprocessing directory: {self.output_dir}")
            self.output_dir.mkdir(exist_ok=True, parents=True)

        # Create a postproc log directory, if it doesn't exist
        if not self.log_dir.exists():
            self.logger.info(f"Creating postprocessing log directory at {self.log_dir}")
            self.log_dir.mkdir(exist_ok=True)

    def setup_logger(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.setLevel(logging.INFO)
        
        # Create log handler
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)

        # Create log formatter to add to handler
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        
        # Add handler to logger
        self.logger.addHandler(c_handler)

    def setup_file_logger(self):
        # Create log handler
        f_handler = logging.FileHandler(self.log_dir / f'postprocess.log')
        f_handler.setLevel(logging.DEBUG)
        
        # Create log format
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)

        # Add handler to the logger
        self.logger.addHandler(f_handler)

    def run(self):
        self.setup_directories()
        self.setup_file_logger()
        
        num_jobs = len(self.post_process_jobs)

        if self.slurm:
            self.logger.info(f"Running {num_jobs} postprocessing jobs in batch mode")
            self.batch_manager.submit_jobs()
        else:
            self.logger.info(f"Running {num_jobs} postprocessing jobs")
            for job in self.post_process_jobs:
                job()

    def __call__(self):
        self.run()
        
