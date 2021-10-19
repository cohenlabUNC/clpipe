import os
import logging

import nipype.pipeline.engine as pe
import click

from .config_json_parser import ClpipeConfigParser
from .batch_manager import BatchManager, Job
from .utils import parse_dir_subjects
#from .postprocutils.nodes import ButterworthFilter
#from .postprocutils.workflows import build_10000_global_median_workflow, build_100_voxel_mean_workflow

logging.basicConfig()
LOG = logging.getLogger(__name__)

EXIT_MSG = "Exiting postprocess2"

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2_cli(subjects, target_dir, submit, debug):
    fmri_postprocess2(subjects=subjects, target_dir=target_dir, submit=submit, debug=debug)


def fmri_postprocess2(subjects=None, target_dir=None, submit=False, debug=False):
    
    if debug: LOG.setLevel(logging.DEBUG)
    LOG.debug(f"Starting postprocessing job targeting: {target_dir}")
    
    # Handle configuration
    config = ClpipeConfigParser()
    batch_manager = BatchManager(config.config['BatchConfig'], ".")

    # Select the subject id(s) to process
    subjects = _process_subjects(subjects)

def _process_subjects(subjects):   
    if subjects is None:
        try:
            subjects = parse_dir_subjects(str(target_dir))
            if len(subjects) == 0:
                no_subjects_found_str = f"No subjects found to parse at: {target_dir}"
                click.echo(no_subjects_found_str)
                LOG.error(no_subjects_found_str)
                click.echo(EXIT_MSG)
                exit()
        except FileNotFoundError as fne:
            click.echo(f"Invalid path provided: {target_dir}")
            LOG.debug(fne)
            click.echo(EXIT_MSG)
            exit()
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
    wf: pe.Workflow = None
    config: dict = None
    
    def __init__(self, config, subject_id: str, in_file: os.PathLike, out_file: os.PathLike, crashdump_dir: str=None):
        #self.ppconfig = config["PostProcessingOptions"]
        self.config=config
        self.subject_id=subject_id
        self.in_file=in_file
        self.out_file=out_file
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
        self.wf.run()