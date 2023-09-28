from nipype.interfaces import afni as afni
import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
import logging
import sys
from .error_handler import exception_handler
from nipype import MapNode, Node, Workflow
import nipype.utils
import pandas as pd
import clpipe.postprocutils.rm_omit_node as rm_omit_node


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
    help="Which task to extract ReHo from. If left blank, defaults to all tasks.",
)
@click.option(
    "-submit", is_flag=True, default=False, help="Flag to submit commands to the HPC."
)
@click.option(
    "-sub_average",
    is_flag=True,
    default=False,
    help="Average ReHo images within a subject?",
)
@click.option(
    "-single",
    is_flag=True,
    default=False,
    help="Run the function. Mainly used internally.",
)
@click.option(
    "-debug", is_flag=True, default=False, help="Print detailed  traceback for errors."
)
def reho_extract(
    config_file=None,
    subjects=None,
    task=None,
    submit=None,
    single=None,
    debug=None,
    sub_average=None,
):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    if config.config["ReHoExtraction"]["ExclusionFile"] is not "":
        exclusion_file = pd.read_csv(config.config["ReHoExtraction"]["ExclusionFile"])

    if not subjects:
        subjectstring = "ALL"
        sublist = [
            o.replace("sub-", "")
            for o in os.listdir(config.config["ReHoExtraction"]["TargetDirectory"])
            if os.path.isdir(
                os.path.join(config.config["ReHoExtraction"]["TargetDirectory"], o)
            )
            and "sub-" in o
        ]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects
    logging.debug(sublist)
    batch_manager = BatchManager(
        config.config["BatchConfig"], config.config["ReHoExtraction"]["LogDirectory"]
    )
    if single:
        for sub in sublist:
            search_string = os.path.abspath(
                os.path.join(
                    config.config["ReHoExtraction"]["TargetDirectory"],
                    "sub-" + sub,
                    "**",
                    "*" + config.config["ReHoExtraction"]["TargetSuffix"],
                )
            )
            logging.debug(search_string)
            subject_files = glob.glob(search_string, recursive=True)
            if len(subject_files) < 1:
                raise FileNotFoundError(
                    "No imaging files were found. Do you have the correct input suffix specified?"
                )
            sub_string = "sub-" + sub
            if task is not None:
                sub_string = sub_string + "_task-" + task
                subject_files = [x for x in subject_files if "task-" + task in x]
            if config.config["ReHoExtraction"]["ExclusionFile"] is not "":
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
                suffix="reho-" + sub,
                prefix="tmp_",
                dir=config.config["ReHoExtraction"]["WorkingDirectory"],
            ) as tmpdir:
                wf = Workflow(name="reho_calc", base_dir=tmpdir)

                subject_masks = [
                    file.replace(
                        config.config["ReHoExtraction"]["TargetSuffix"],
                        config.config["ReHoExtraction"]["MaskSuffix"],
                    )
                    for file in subject_files
                ]
                subject_masks = [
                    file.replace(
                        config.config["ReHoExtraction"]["TargetDirectory"],
                        config.config["ReHoExtraction"]["MaskDirectory"],
                    )
                    for file in subject_masks
                ]

                nanomit_node = MapNode(
                    rm_omit_node.NANOmit(), name="NAN_Removal", iterfield=["in_file"]
                )
                nanomit_node.inputs.in_file = subject_files

                if sub_average:
                    reho_node = MapNode(
                        afni.ReHo(),
                        name="Mean_Calc",
                        iterfield=["in_file", "mask_file"],
                    )
                    reho_node.inputs.neighborhood = "vertices"
                    reho_node.inputs.mask_file = subject_masks

                    merge_node = Node(afni.TCat(), name="Merge_Images")
                    merge_node.inputs.outputtype = "NIFTI_GZ"
                    average_node = Node(afni.TStat(), name="Average_Across_Images")
                    average_node.inputs.args = "-nzmean"
                    average_node.inputs.outputtype = "NIFTI_GZ"
                    out_file = os.path.join(
                        config.config["ReHoExtraction"]["OutputDirectory"],
                        sub_string
                        + "_"
                        + config.config["ReHoExtraction"]["OutputSuffix"],
                    )
                    average_node.inputs.out_file = out_file
                    wf.connect(nanomit_node, "out_file", reho_node, "in_file")
                    wf.connect(reho_node, "out_file", merge_node, "in_files")
                    wf.connect(merge_node, "out_file", average_node, "in_file")
                else:
                    reho_node = MapNode(
                        afni.ReHo(),
                        name="Mean_Calc",
                        iterfield=["in_file", "mask_file", "out_file"],
                    )
                    reho_node.inputs.neighborhood = "vertices"
                    reho_node.inputs.mask_file = subject_masks
                    out_files = [
                        os.path.basename(x).replace(
                            config.config["ReHoExtraction"]["TargetSuffix"],
                            config.config["ReHoExtraction"]["OutputSuffix"],
                        )
                        for x in subject_files
                    ]
                    out_files = [
                        os.path.join(
                            os.path.abspath(
                                config.config["ReHoExtraction"]["OutputDirectory"]
                            ),
                            x,
                        )
                        for x in out_files
                    ]
                    reho_node.inputs.out_file = out_files
                    wf.connect(nanomit_node, "out_file", reho_node, "in_file")

                wf.run()
    else:
        logging.debug("Compiling Job Strings")
        job_string = """reho_extract -config_file {config_file} {task} {sub_average} {debug} -single {subject}"""
        task_string = ""
        debug_string = ""
        subaverage_string = ""
        if task is not None:
            task_string = "-task " + task
        if debug:
            debug_string = "-debug"
        if sub_average:
            subaverage_string = "-sub_average"
        for sub in sublist:
            job_str = job_string.format(
                config_file=config_file,
                task=task_string,
                debug=debug_string,
                sub_average=subaverage_string,
                subject=sub,
            )
            batch_manager.addjob(Job("rehoextract-" + sub, job_str))
        if submit:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())
