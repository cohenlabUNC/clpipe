import os

from nipype.interfaces.utility import Function, IdentityInterface
import nipype.pipeline.engine as pe

from .utils import get_scrub_vector_node
from .image_workflows import build_image_postprocessing_workflow, STEP_CONFOUND_REGRESSION, STEP_SCRUB_TIMEPOINTS
from .confounds_workflows import build_confounds_processing_workflow
from ..utils import get_logger

def build_postprocessing_wf(
    postprocessing_config: dict,
    tr: int,
    name: str = "postprocessing_wf",
    image_file: os.PathLike=None,
    image_export_path: os.PathLike=None,
    confounds_file: os.PathLike=None,
    confounds_export_path: os.PathLike=None,
    mask_file: os.PathLike=None,
    mixing_file: os.PathLike=None,
    noise_file: os.PathLike=None,
    working_dir: os.PathLike=None,
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
    processing_steps = postprocessing_config["ProcessingSteps"]

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
            postprocessing_config,
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
            postprocessing_config,
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
                confounds_wf, "outputnode.out_file", image_wf, "inputnode.confounds_file"
            )

    # Setup outputs
    postproc_wf.connect(image_wf, "outputnode.out_file", output_node, "out_file")
    postproc_wf.connect(
        confounds_wf, "outputnode.out_file", output_node, "processed_confounds_file"
    )

    
    # Setup scrub target if needed
    if STEP_SCRUB_TIMEPOINTS in processing_steps:
        scrub_target_node = pe.Node(
            Function(
                input_names=[
                    "confounds_file",
                    "scrub_target_variable",
                    "scrub_threshold",
                    "scrub_behind",
                    "scrub_ahead",
                    "scrub_contiguous",
                ],
                output_names=["scrub_vector"],
                function=get_scrub_vector_node,
            ),
            name="get_scrub_vector_node",
        )

        # Setup scrub inputs
        scrub_target_node.inputs.scrub_target_variable = postprocessing_config[
            "ProcessingStepOptions"
        ]["ScrubTimepoints"]["TargetVariable"]
        scrub_target_node.inputs.scrub_threshold = postprocessing_config[
            "ProcessingStepOptions"
        ]["ScrubTimepoints"]["Threshold"]
        scrub_target_node.inputs.scrub_behind = postprocessing_config[
            "ProcessingStepOptions"
        ]["ScrubTimepoints"]["ScrubBehind"]
        scrub_target_node.inputs.scrub_ahead = postprocessing_config[
            "ProcessingStepOptions"
        ]["ScrubTimepoints"]["ScrubAhead"]
        scrub_target_node.inputs.scrub_contiguous = postprocessing_config[
            "ProcessingStepOptions"
        ]["ScrubTimepoints"]["ScrubContiguous"]

        scrub_target_node.inputs.confounds_file = confounds_file
        if image_wf:
            postproc_wf.connect(
                scrub_target_node, "scrub_vector", image_wf, "inputnode.scrub_vector"
            )
        if confounds_wf:
            postproc_wf.connect(
                scrub_target_node, "scrub_vector", confounds_wf, "inputnode.scrub_vector"
            )

    return postproc_wf