from nipype.interfaces import afni as afni
from nipype.interfaces import fsl as fsl
from pathlib import Path
import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
import logging
import sys
from .error_handler import exception_handler
from nipype import MapNode, Node, Workflow

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Use a given configuration file.')
@click.option('-task', help = 'Which task to extract T2* from. If left blank, defaults to all tasks.')
@click.option('-onlymean', is_flag = True, default = False, help = 'Return the average of all extracted T2* images per subject only. Not including this flag returns individual T2* images per scan.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed  traceback for errors.')
def t2star_extract(config_file = None, subjects = None, task = None,onlymean = None, submit = None, debug = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config["T2StarExtraction"]['TargetDirectory'])
        if os.path.isdir(os.path.join(config.config["T2StarExtraction"]['TargetDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects
    logging.debug(sublist)
    batch_manager = BatchManager(config.config['BatchConfig'], config.config["T2StarExtraction"]['LogDirectory'])
    for sub in sublist:
        sub_string = "sub-"+sub
        search_string = os.path.abspath(
            os.path.join(config.config["T2StarExtraction"]['TargetDirectory'], "sub-" + sub, "**",
                         "*" + config.config["T2StarExtraction"]['TargetSuffix']))
        logging.debug(search_string)
        subject_files = glob.glob(search_string, recursive=True)
        if task is not None:
            sub_string = sub_string+"_task-"+task
            subject_files = [x for x in subject_files if "task-"+task in x]
        logging.debug(subject_files)
        wf = Workflow(name = "t2star_timeaverage",
                      base_dir=config.config['ProjectDirectory'])


        subject_masks = [file.replace(config.config["T2StarExtraction"]["TargetSuffix"],config.config["T2StarExtraction"]["MaskSuffix"]) for file in subject_files]
        subject_masks = [file.replace(config.config["T2StarExtraction"]["TargetDirectory"], config.config["T2StarExtraction"]["MaskDirectory"]) for file in subject_masks]

        mean_node = MapNode(afni.ROIStats(), name = "Mean_Calc", iterfield=['in_file', 'mask_file'])
        mean_node.inputs.stat = "mean"
        mean_node.inputs.in_file = subject_files
        mean_node.inputs.mask_file = subject_masks
        mean_node.inputs.format1D = True

        sd_node = MapNode(afni.ROIStats(), name = "SD_Calc",  iterfield=['in_file', 'mask_file'])
        sd_node.inputs.stat = "sigma"
        sd_node.inputs.in_file = subject_files
        sd_node.inputs.mask_file = subject_masks
        sd_node.inputs.format1D = True

        zscore_node = MapNode(afni.Calc(),name = "ZScore_Transform", iterfield=['in_file_a', 'in_file_b', 'in_file_c'])
        zscore_node.inputs.expr = "(a-b)/c"
        zscore_node.inputs.in_file_a = subject_files
        zscore_node.inputs.outputtype = "NIFTI_GZ"
        merge_node = Node(afni.TCat(), name = "Merge_Images")
        
        average_node = Node(afni.TStat(), name = "Average_Across_Images")
        average_node.inputs.args = "-nzmean"
        average_node.inputs.outputtype = "NIFTI_GZ"

        out_file = os.path.join(config.config["T2StarExtraction"]["OutputDirectory"], sub_string+"_"+config.config["T2StarExtraction"]["OutputSuffix"])
        average_node.inputs.out_file = out_file
        wf.connect(mean_node, "out_file", zscore_node, "in_file_b")
        wf.connect(sd_node, "out_file", zscore_node, "in_file_c")

        wf.connect(zscore_node, "out_file", merge_node, "in_files")
        wf.connect(merge_node, "merged_file", average_node, "in_file")

        wf.run()


