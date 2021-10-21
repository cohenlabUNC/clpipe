import os
import logging
from pathlib import Path

import click
import nipype.pipeline.engine as pe
from bids import BIDSLayout, layout, config as bids_config

from .config_json_parser import ClpipeConfigParser
from .batch_manager import BatchManager, Job
from .utils import parse_dir_subjects
#from .postprocutils.nodes import ButterworthFilter
#from .postprocutils.workflows import build_10000_global_median_workflow, build_100_voxel_mean_workflow

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
@click.option('-submit/-local', is_flag = True, default=True, help = 'Flag to submit commands to the HPC.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2_cli(subjects, target_dir, output_dir, submit, debug):
    postprocess_fmriprep_dir(subjects=subjects, fmriprep_dir=target_dir, output_dir=output_dir, submit=submit, debug=debug)

@click.argument('target_image', type=click.Path(dir_okay=False, file_okay=True))
def postprocess_image_cli(target_image):
    postprocess_image(target_image)

def postprocess_image(target_image):
    LOG.info(f"Processing image: {target_image}")

def postprocess_fmriprep_dir(subjects=None, fmriprep_dir=None, output_dir=None, submit=False, debug=False):
    
    if debug: LOG.setLevel(logging.DEBUG)
    LOG.debug(f"Starting postprocessing job targeting: {fmriprep_dir}")
    
    # Handle configuration
    config = ClpipeConfigParser()

    # Get the fmriprep_dir as a BIDSLayout object
    #db_path = "tests/fmriprep_dir"
    fmriprep_dir:BIDSLayout = setup_fmriprep_dir(fmriprep_dir)

    # Choose the subjects to process
    subjects = get_subjects(fmriprep_dir, subjects)

    # Choose the images to process
    images_to_process = fmriprep_dir.get(subject=subjects, return_type="filename", extension="nii.gz", datatype="func", suffix="bold")

    # Setup batch jobs if indicated
    if submit:
        batch_manager = setup_batch_jobs(config, images_to_process)
        
        click.echo(batch_manager.print_jobs())

        if click.confirm('Submit these jobs to the HPC?'):
            batch_manager.submit_jobs()
    # Process the iamges locally
    else:
        setup_jobs()

def setup_fmriprep_dir(fmriprep_dir: str):
    #if not os.path.exists(db_path):
    #    click.echo("Indexing fMRIPrep directory...")
    click.echo("Indexing fMRIPrep directory...")
    fmriprep_dir = BIDSLayout(fmriprep_dir, validate=False)

    return fmriprep_dir

def setup_jobs():
    pass

    #postProcessSubjectsJob.run()
    #postProcessSubjectsJob = PostProcessSubjectsJob(target_dir, output_dir, subject_ids=subjects)

def setup_batch_jobs(config, images_to_process):
    submission_string = """postprocess_image {image_path}"""
    
    batch_manager = BatchManager(config.config['BatchConfig'], "/nas/longleaf/home/willasc/repos/clpipe/tests/Output-PostProcessing")

    for image_path in images_to_process:
        sub_string_temp = submission_string.format(image_path=image_path)
        image_stem = Path(image_path).stem

        batch_manager.addjob(Job("PostProcessing_" + image_stem, sub_string_temp))

    batch_manager.createsubmissionhead()
    batch_manager.compilejobstrings()

    return batch_manager

def get_subjects(fmriprep_dir: BIDSLayout, subjects):   
    # If no subjects were provided, use all subjects in the fmriprep directory
    if subjects is None:
        try:
            subjects = fmriprep_dir.get_subjects()
            if len(subjects) == 0:
                no_subjects_found_str = f"No subjects found to parse at: {fmriprep_dir.root}"
                click.echo(no_subjects_found_str)
                LOG.error(no_subjects_found_str)
                click.echo(EXIT_MSG)
                exit()
        except FileNotFoundError as fne:
            click.echo(f"Invalid path provided: {fmriprep_dir.root}")
            LOG.debug(fne)
            click.echo(EXIT_MSG)
            exit()
    # If subjects were provided, return those subjects
    if len(subjects) == 1:
        processing_msg = f"Processing subject: {subjects[0]}"
        LOG.info(processing_msg)
        click.echo(processing_msg)
    else:
        processing_msg = f"Processing subjects: {subjects}"
        LOG.info(processing_msg)
        click.echo(processing_msg)

    return subjects

class PostProcessSubjectJob():
    #wf: pe.Workflow = None
    config: dict = None
    
    def __init__(self, out_dir: os.PathLike, crashdump_dir: str=None):
        #self.ppconfig = config["PostProcessingOptions"]
        #self.subject_id=subject.subject_id
        # get from new fmriprepoutput function
        self.in_file=None
        # derive from out_dir and in_file
        self.out_file=None
        # self.wf = pe.Workflow(name=PostProcessSubjectJob.__class__.__name__ + subject_id)
        # if crashdump_dir is not None:
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

    def run(self):
        print(f"Running job for {self.subject_id}")
        #self.wf.run()

class PostProcessSubjectJobs():
    post_process_jobs: PostProcessSubjectJob = {}
    
    def __init__(self, target_dir, output_dir, subject_ids=None, ):

        pass
        
        
        #self.fMRIprep_dir = FMRIPrepOutputDir(target_dir)

        # if subject_ids == None:
        #     for sub_id in self.fMRIprep_dir.fmriprep_outputs.keys():
        #         in_file = None
        #         self.post_process_jobs[sub_id] = PostProcessSubjectJob(self.fMRIprep_dir.fmriprep_outputs[sub_id], output_dir)
        # else:
        #     for sub_id in subject_ids:
        #         fmri_output = self.fMRIprep_dir.fmriprep_outputs[sub_id]
        #         in_file = None
        #         self.post_process_jobs[sub_id] = PostProcessSubjectJob(fmri_output, output_dir)

    def run(self):
        for job in self.post_process_jobs:
            print(self.post_process_jobs[job].run())

        
