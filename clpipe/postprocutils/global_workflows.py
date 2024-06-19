import os

from nipype.interfaces.utility import Function, IdentityInterface
import nipype.pipeline.engine as pe
from nipype.interfaces.afni import Undump, ROIStats

from .utils import get_scrub_vector_node, logical_or_across_lists, expand_scrub_dict
from .image_workflows import (
    build_image_postprocessing_workflow,
    STEP_CONFOUND_REGRESSION,
    STEP_SCRUB_TIMEPOINTS,
)
from .confounds_workflows import build_confounds_processing_workflow
from ..utils import get_logger
from ..config.options import PostProcessingOptions
from .nodes import build_output_node

STEP_ROI_EXTRACT = "ROIExtract"
STEP_SPHERE_EXTRACT = "SphereExtract"


def build_postprocessing_wf(
    processing_options: PostProcessingOptions,
    tr: int,
    name: str = "postprocessing_wf",
    image_file: os.PathLike = None,
    image_export_path: os.PathLike = None,
    confounds_file: os.PathLike = None,
    confounds_export_path: os.PathLike = None,
    mask_file: os.PathLike = None,
    mixing_file: os.PathLike = None,
    noise_file: os.PathLike = None,
    working_dir: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    """Creates a top-level postprocessing workflow which combines the image and confounds processing workflows

    Args:
        image_wf (pe.Workflow, optional): An image processing workflow. Defaults to None.
        confounds_wf (pe.Workflow, optional): A confound processing workflow. Defaults to None.
        name (str, optional): The name for the constructed workflow. Defaults to "Postprocessing_Pipeline".
        confound_regression (bool, optional): Should the processed confounds be passed to the image workflow for regression? Defaults to False.

    Returns:
        pe.Workflow: A complete postprocessing workflow.
    """

    # TODO: Build-time inputs - inputs used to make decisions while making graph
    #   these are parameter arguments to the wf builder
    #       image_path: os.PathLike=None,
    #       confounds_path: os.PathLike=None,
    # Everything else is an input to the workflow, set outside the builder.
    # Needs to propogate down through sub-workflows as well.

    logger = get_logger("postprocessing_wf_builder")
    processing_steps = processing_options.processing_steps

    # Create the global postprocessing workflow
    postproc_wf = pe.Workflow(name=name, base_dir=base_dir)
    if crashdump_dir is not None:
        postproc_wf.config["execution"]["crashdump_dir"] = crashdump_dir

    output_node = pe.Node(
        IdentityInterface(
            fields=["out_file", "processed_confounds_file"], mandatory_inputs=False
        ),
        name="outputnode",
    )

    # Create the confounds workflow, if confounds path given
    confounds_wf = None
    if confounds_file:
        confounds_wf = build_confounds_processing_workflow(
            processing_options,
            confounds_file=confounds_file,
            export_file=confounds_export_path,
            tr=tr,
            name=f"confounds_wf",
            mixing_file=mixing_file,
            noise_file=noise_file,
            base_dir=working_dir,
            crashdump_dir=crashdump_dir,
        )

    # Create the image workflow, if an image path is given
    image_wf = None
    if image_file:
        logger.info(f"Building postprocessing workflow for: {name}")
        image_wf = build_image_postprocessing_workflow(
            processing_options,
            in_file=image_file,
            export_path=image_export_path,
            name=f"image_wf",
            mask_file=mask_file,
            confounds_file=confounds_file,
            mixing_file=mixing_file,
            noise_file=noise_file,
            tr=tr,
            base_dir=base_dir,
            crashdump_dir=crashdump_dir,
        )

        # Connect postprocessed confound file to image_wf if needed
        if STEP_CONFOUND_REGRESSION in processing_steps:
            postproc_wf.connect(
                confounds_wf,
                "outputnode.out_file",
                image_wf,
                "inputnode.confounds_file",
            )

    # Setup outputs
    postproc_wf.connect(image_wf, "outputnode.out_file", output_node, "out_file")
    postproc_wf.connect(
        confounds_wf, "outputnode.out_file", output_node, "processed_confounds_file"
    )

    # Setup scrub target if needed
    if STEP_SCRUB_TIMEPOINTS in processing_steps:
        mult_scrub_wf = build_multiple_scrubbing_workflow(
            processing_options.processing_step_options.scrub_timepoints.scrub_columns,
            confounds_file,
        )
        mult_scrub_wf.get_node("inputnode").inputs.confounds_file = confounds_file

        if image_wf:
            postproc_wf.connect(
                mult_scrub_wf, "outputnode.out_file", image_wf, "inputnode.scrub_vector"
            )
        if confounds_wf:
            postproc_wf.connect(
                mult_scrub_wf,
                "outputnode.out_file",
                confounds_wf,
                "inputnode.scrub_vector",
            )

    return postproc_wf


def build_multiple_scrubbing_workflow(
    scrub_configs: list,
    confounds_file: os.PathLike,
    name: str = "multiple_scrubbing_workflow",
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    """Creates a multiple scrubbing workflow which scrubs multiple columns based on target variables defined in the config file.

    Args:
        scrub_configs (list): The level for the config file that contains information about which columns to scrub.
        name (str, optional): The name for the constructed workflow. Defaults to "Postprocessing_Pipeline".

    Returns:
        pe.Workflow: A workflow for scrubbing multiple columns.

    """
    # Create an input node for the workflow
    input_node = pe.Node(
        IdentityInterface(fields=["confounds_file", "scrub_configs"]), name="inputnode"
    )

    # Define the output node for the workflow
    output_node = pe.Node(IdentityInterface(fields=["out_file"]), name="outputnode")

    # Convert list of ScrubColumns to list of dicts
    scrub_configs = [scrub_config.to_dict() for scrub_config in scrub_configs]

    # Feed the scrub config list of dicts into the mapper via the workflow inputnode
    input_node.inputs.scrub_configs = scrub_configs
    input_node.inputs.tsv_file = confounds_file

    # Expanding Dict using Wildcard node
    expand_node = pe.Node(
        Function(
            input_names=["tsv_file", "scrub_configs"],
            output_names=["scrub_configs"],
            function=expand_scrub_dict,
        ),
        name="expand_node",
    )

    # Define the function node
    scrub_target_node = pe.MapNode(
        Function(
            input_names=["confounds_file", "scrub_configs"],
            output_names=["scrub_vector"],
            function=get_scrub_vector_node,
        ),
        iterfield=["scrub_configs"],
        name="get_scrub_vector_map_node",
    )

    # Create the logical_or_node
    reduce_node = pe.Node(
        Function(
            input_names=["list_of_lists"],
            output_names=["or_result"],
            function=logical_or_across_lists,
        ),
        name="reduce_node",
    )

    # Create a new workflow to hold only the scrub_target_node
    mult_scrub_wf = pe.Workflow(name=name, base_dir=base_dir)
    if crashdump_dir is not None:
        mult_scrub_wf.config["execution"]["crashdump_dir"] = crashdump_dir

    mult_scrub_wf.add_nodes(
        [input_node, expand_node, scrub_target_node, reduce_node, output_node]
    )

    mult_scrub_wf.connect(input_node, "tsv_file", expand_node, "tsv_file")
    mult_scrub_wf.connect(input_node, "scrub_configs", expand_node, "scrub_configs")
    mult_scrub_wf.connect(
        expand_node, "scrub_configs", scrub_target_node, "scrub_configs"
    )
    mult_scrub_wf.connect(
        input_node, "confounds_file", scrub_target_node, "confounds_file"
    )

    mult_scrub_wf.connect(
        scrub_target_node, "scrub_vector", reduce_node, "list_of_lists"
    )
    mult_scrub_wf.connect(reduce_node, "or_result", output_node, "out_file")

    return mult_scrub_wf


def build_sphere_extract_workflow(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    coordinates_file: os.PathLike = None,
    sphere_radius: int = None,
    mask_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None
):
    workflow = pe.Workflow(name=STEP_SPHERE_EXTRACT, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    # Setup identity (pass through) input/output nodes
    input_node = pe.Node(
        IdentityInterface(
            fields=["in_file", "out_file", "master_file", "sphere_radius", "mask_file"],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = build_output_node()

    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file
    if coordinates_file:
        input_node.inputs.coordinates_file = coordinates_file
    if sphere_radius:
        input_node.inputs.sphere_radius = sphere_radius
    if mask_file:
        input_node.inputs.mask_file = mask_file

    
    undump_node = pe.Node(
        Undump(out_file="sphere_mask.nii.gz", coordinates_specification="xyz"), name="undump"
    )

    index_node = pe.Node(
        Function(
            input_names=["coordinates_file"],
            output_names=["out_file"],
            function=_index_coordinates,
        ),
        name="index_coordinates",
    )

    roi_stats_node = pe.Node(
        ROIStats(nobriklab=True), name="roi_stats"
    )

    # Index the coordinates file
    workflow.connect(input_node, "coordinates_file", index_node, "coordinates_file")

    # Setup coordinates-based mask creation nodes
    workflow.connect(index_node, "out_file", undump_node, "in_file")
    workflow.connect(input_node, "in_file", undump_node, "master_file")
    workflow.connect(input_node, "sphere_radius", undump_node, "srad")
    workflow.connect(input_node, "mask_file", undump_node, "mask_file")
    
    # Setup ROIStats node
    workflow.connect(input_node, "in_file", roi_stats_node, "in_file")
    workflow.connect(undump_node, "out_file", roi_stats_node, "mask_file")
    
    #workflow.connect(input_node, "out_file", roi_stats_node, "out_file")

    workflow.connect(roi_stats_node, "out_file", output_node, "out_file")

    return workflow


def _index_coordinates(coordinates_file):
    # Imports must be in function for running as node
    from pathlib import Path

    # Load in the coordinates file. For each row in the file, add an index 1 to
    #  n at the end of each row. Save the new file.

    new_fname = f"{Path(coordinates_file).stem}_indexed.txt"

    with open(coordinates_file, "r") as f:
        data = f.readlines()
        for i, line in enumerate(data):
            data[i] = line.strip() + f"\t{i+1}\n"

        with open(new_fname, "w") as f:
            f.writelines(data)

    return str(Path(new_fname).absolute())
