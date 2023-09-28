from nipype.interfaces import afni as afni
import nipype.utils
from nipype.interfaces import fsl as fsl
from pathlib import Path
import pandas as pd
import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
import logging
import sys
from .error_handler import exception_handler
from nipype import MapNode, Node, Workflow
import clpipe.postprocutils.rm_omit_node as rm_omit_node


def rm_nan(in_file):
    import nibabel
    import numpy

    img = nibabel.load(in_file)
    img_dat = img.get_fdata()

    nan_vec = numpy.sum(numpy.isnan(img_dat), axis=(0, 1, 2))
    it = numpy.nditer(nan_vec, flags=["f_index"])
    good_inds = [it.index for x in it if x == 0]
    img_trimdat = img_dat[good_inds]
    rm_file = nibabel.Nifti1Image(img_trimdat, img.affine, nibabel.Nifti1Header())


@click.command()
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="Use a given configuration file.",
)
@click.option(
    "-task",
    help="Which task to extract T2* from. If left blank, defaults to all tasks.",
)
@click.option(
    "-submit", is_flag=True, default=False, help="Flag to submit commands to the HPC."
)
@click.option(
    "-single",
    is_flag=True,
    default=False,
    help="Submit to batch, or run in current session. Mainly used internally.",
)
@click.option(
    "-debug", is_flag=True, default=False, help="Print detailed traceback for errors."
)
def t2star_extract(
    config_file=None, subjects=None, task=None, submit=None, debug=None, single=None
):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    if config.config["T2StarExtraction"]["ExclusionFile"] is not "":
        exclusion_file = pd.read_csv(config.config["T2StarExtraction"]["ExclusionFile"])

    if not subjects:
        subjectstring = "ALL"
        sublist = [
            o.replace("sub-", "")
            for o in os.listdir(config.config["T2StarExtraction"]["TargetDirectory"])
            if os.path.isdir(
                os.path.join(config.config["T2StarExtraction"]["TargetDirectory"], o)
            )
            and "sub-" in o
        ]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects
    logging.debug(sublist)
    batch_manager = BatchManager(
        config.config["BatchConfig"], config.config["T2StarExtraction"]["LogDirectory"]
    )

    if single:
        for sub in sublist:
            sub_string = "sub-" + sub
            search_string = os.path.abspath(
                os.path.join(
                    config.config["T2StarExtraction"]["TargetDirectory"],
                    "sub-" + sub,
                    "**",
                    "*" + config.config["T2StarExtraction"]["TargetSuffix"],
                )
            )
            logging.debug(search_string)
            subject_files = glob.glob(search_string, recursive=True)
            if len(subject_files) < 1:
                raise FileNotFoundError(
                    "No imaging files were found. Do you have the correct input suffix specified?"
                )
            if task is not None:
                sub_string = sub_string + "_task-" + task
                subject_files = [x for x in subject_files if "task-" + task in x]

            if config.config["T2StarExtraction"]["ExclusionFile"] is not "":
                logging.debug("Exclusion active")
                logging.debug([os.path.basename(x) for x in subject_files])
                logging.debug(exclusion_file["filename"].to_list())
                subject_files = [
                    x
                    for x in subject_files
                    if os.path.basename(x) not in exclusion_file["filename"].to_list()
                ]
                if len(subject_files) < 1:
                    raise FileNotFoundError(
                        "After checking excluded files, this subject had no viable scans! Verify if this is correct"
                    )

            logging.debug(subject_files)
            with nipype.utils.tmpdirs.TemporaryDirectory(
                suffix="t2star-" + sub,
                prefix="tmp_",
                dir=config.config["T2StarExtraction"]["WorkingDirectory"],
            ) as tmpdir:
                wf = Workflow(name="t2star_timeaverage", base_dir=tmpdir)

                subject_masks = [
                    file.replace(
                        config.config["T2StarExtraction"]["TargetSuffix"],
                        config.config["T2StarExtraction"]["MaskSuffix"],
                    )
                    for file in subject_files
                ]
                subject_masks = [
                    file.replace(
                        config.config["T2StarExtraction"]["TargetDirectory"],
                        config.config["T2StarExtraction"]["MaskDirectory"],
                    )
                    for file in subject_masks
                ]

                nanomit_node = MapNode(
                    rm_omit_node.NANOmit(), name="NAN_Removal", iterfield=["in_file"]
                )
                nanomit_node.inputs.in_file = subject_files

                mean_node = MapNode(
                    afni.ROIStats(),
                    name="Mean_Calc",
                    iterfield=["in_file", "mask_file"],
                )
                mean_node.inputs.stat = "mean"
                mean_node.inputs.mask_file = subject_masks
                mean_node.inputs.format1D = True

                sd_node = MapNode(
                    afni.ROIStats(), name="SD_Calc", iterfield=["in_file", "mask_file"]
                )
                sd_node.inputs.stat = "sigma"
                sd_node.inputs.mask_file = subject_masks
                sd_node.inputs.format1D = True

                zscore_node = MapNode(
                    afni.Calc(),
                    name="ZScore_Transform",
                    iterfield=["in_file_a", "in_file_b", "in_file_c"],
                )
                zscore_node.inputs.expr = "(a-b)/c"
                zscore_node.inputs.outputtype = "NIFTI_GZ"
                merge_node = Node(afni.TCat(), name="Merge_Images")
                merge_node.inputs.outputtype = "NIFTI_GZ"
                average_node = Node(afni.TStat(), name="Average_Across_Images")
                average_node.inputs.args = "-nzmean"
                average_node.inputs.outputtype = "NIFTI_GZ"

                out_file = os.path.join(
                    config.config["T2StarExtraction"]["OutputDirectory"],
                    sub_string
                    + "_"
                    + config.config["T2StarExtraction"]["OutputSuffix"],
                )
                average_node.inputs.out_file = out_file
                wf.connect(nanomit_node, "out_file", mean_node, "in_file")
                wf.connect(nanomit_node, "out_file", sd_node, "in_file")
                wf.connect(nanomit_node, "out_file", zscore_node, "in_file_a")
                wf.connect(mean_node, "out_file", zscore_node, "in_file_b")
                wf.connect(sd_node, "out_file", zscore_node, "in_file_c")

                wf.connect(zscore_node, "out_file", merge_node, "in_files")
                wf.connect(merge_node, "out_file", average_node, "in_file")

                wf.run()
    else:
        logging.debug("Compiling Job Strings")
        job_string = """t2star_extract -config_file {config_file} {task} {debug} -single {subject}"""
        task_string = ""
        debug_string = ""
        if task is not None:
            task_string = "-task " + task
        if debug:
            debug_string = "-debug"
        for sub in sublist:
            job_str = job_string.format(
                config_file=config_file,
                task=task_string,
                debug=debug_string,
                subject=sub,
            )
            batch_manager.addjob(Job("t2starextract-" + sub, job_str))
        if submit:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())
