"""Workflow Builder Functions.

Contains a collection of image processing workflow builders used to create a
postprocessing pipeline.
"""

import os

from math import sqrt, log
import pkg_resources

# TODO: import these without specifying, to help with code readability
from nipype.interfaces.fsl.maths import (
    MeanImage,
    BinaryMaths,
    ApplyMask,
    TemporalFilter,
)
from nipype.interfaces.fsl.utils import ImageStats, FilterRegressor
from nipype.interfaces.afni import TProject
from nipype.interfaces.fsl.model import GLM
from nipype.interfaces.fsl import SUSAN, FLIRT
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.interfaces.io import ExportFile
import nipype.pipeline.engine as pe

import clpipe.postprocutils.r_setup
from .nodes import (
    build_input_node,
    build_output_node,
    ButterworthFilter,
    RegressAromaR,
    ImageSlice,
)
from .utils import scrub_image, get_scrub_vector_node
from ..errors import ImplementationNotFoundError
from ..config.postprocessing import PostProcessingConfig

# TODO: Set these values up as hierarchical, maybe with enums

STEP_TEMPORAL_FILTERING = "TemporalFiltering"
IMPLEMENTATION_BUTTERWORTH = "Butterworth"
IMPLEMENTATION_FSLMATHS = "fslmaths"

STEP_INTENSITY_NORMALIZATION = "IntensityNormalization"
IMPLEMENTATION_10000_GLOBAL_MEDIAN = "10000_GlobalMedian"
IMPLEMENTATION_100_VOXEL_MEAN = "100_voxelmean"

STEP_SPATIAL_SMOOTHING = "SpatialSmoothing"
IMPLEMENTATION_SUSAN = "SUSAN"

STEP_AROMA_REGRESSION = "AROMARegression"
IMPLEMENTATION_FSL_REGFILT = "fsl_regfilt"
IMPLEMENTATION_FSL_REGFILT_R = "fsl_regfilt_R"

STEP_CONFOUND_REGRESSION = "ConfoundRegression"
IMPLEMENTATION_FSL_GLM = "fsl_glm"
IMPLEMENTATION_AFNI_3DTPROJECT = "afni_3dTproject"

STEP_APPLY_MASK = "ApplyMask"
STEP_TRIM_TIMEPOINTS = "TrimTimepoints"
STEP_RESAMPLE = "Resample"

STEP_SCRUB_TIMEPOINTS = "ScrubTimepoints"


def build_postprocessing_workflow(
    image_wf: pe.Workflow = None,
    confounds_wf: pe.Workflow = None,
    name: str = "image_wf",
    postprocessing_config: dict = None,
    confounds_file: os.PathLike = None,
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

    input_node = pe.Node(
        IdentityInterface(
            fields=[
                "in_file",
                "confounds_file",
                "image_export_path",
                "confounds_export_path",
            ],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = pe.Node(
        IdentityInterface(
            fields=["out_file", "processed_confounds_file"], mandatory_inputs=False
        ),
        name="outputnode",
    )

    postproc_wf = pe.Workflow(name=name, base_dir=base_dir)
    if crashdump_dir is not None:
        postproc_wf.config["execution"]["crashdump_dir"] = crashdump_dir

    if confounds_file:
        input_node.confounds_file = confounds_file

    # Setup inputs
    postproc_wf.connect(input_node, "in_file", image_wf, "inputnode.in_file")
    postproc_wf.connect(input_node, "confounds_file", confounds_wf, "inputnode.in_file")
    # postproc_wf.connect(input_node, "image_export_path", image_wf, "inputnode.export_file")
    # postproc_wf.connect(input_node, "confounds_export_path", confounds_wf, "inputnode.in_file")

    # Setup outputs
    postproc_wf.connect(image_wf, "outputnode.out_file", output_node, "out_file")
    postproc_wf.connect(
        confounds_wf, "outputnode.out_file", output_node, "processed_confounds_file"
    )

    processing_steps = postprocessing_config["ProcessingSteps"]

    # Connect postprocessed confound file to image_wf if needed
    if STEP_CONFOUND_REGRESSION in processing_steps:
        postproc_wf.connect(
            confounds_wf, "outputnode.out_file", image_wf, "inputnode.confounds_file"
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

        postproc_wf.connect(
            input_node, "confounds_file", scrub_target_node, "confounds_file"
        )
        postproc_wf.connect(
            scrub_target_node, "scrub_vector", image_wf, "inputnode.scrub_vector"
        )
        postproc_wf.connect(
            scrub_target_node, "scrub_vector", confounds_wf, "inputnode.scrub_vector"
        )

    return postproc_wf


def build_image_postprocessing_workflow(
    postproc_config: PostProcessingConfig,
    in_file: os.PathLike = None,
    export_path: os.PathLike = None,
    name: str = "Postprocessing_Pipeline",
    processing_steps: list = None,
    mask_file: os.PathLike = None,
    mixing_file: os.PathLike = None,
    noise_file: os.PathLike = None,
    confounds_file: os.PathLike = None,
    tr: float = None,
    scrub_vector: list = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    postproc_wf = pe.Workflow(name=name, base_dir=base_dir)

    if crashdump_dir is not None:
        postproc_wf.config['execution']['crashdump_dir'] = crashdump_dir
    
    step_count = len(postproc_config.processing_steps)

    if step_count < 1:
        raise ValueError(
            "The PostProcess workflow requires at least 1 processing step."
        )

    input_node = pe.Node(
        IdentityInterface(
            fields=[
                "in_file",
                "export_path",
                "confounds_file",
                "scrub_vector",
                "mask_file",
                "mixing_file",
                "noise_file",
                "tr",
            ],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = pe.Node(
        IdentityInterface(fields=["out_file"], mandatory_inputs=True), name="outputnode"
    )

    # Set WF inputs
    if in_file:
        input_node.inputs.in_file = in_file
    if export_path:
        input_node.inputs.export_file = export_path
    if confounds_file:
        input_node.inputs.confounds_file = confounds_file
    if scrub_vector:
        input_node.inputs.scrub_vector = scrub_vector
    if mask_file:
        input_node.inputs.mask_file = mask_file
    if mixing_file:
        input_node.inputs.mixing_file = mixing_file
    if noise_file:
        input_node.inputs.noise_file = noise_file
    if tr:
        input_node.inputs.tr = tr

    current_wf = None
    prev_wf = None

    # Iterate through list of processing steps, adding a new sub workflow for each step
    for index, step in enumerate(processing_steps):
        # Decide which wf to add next
        if step == STEP_TEMPORAL_FILTERING:
            if not tr:
                raise ValueError(f"Missing TR corresponding to image: {in_file}")
            hp = postproc_config.processing_step_options.temporal_filtering.filtering_high_pass
            lp = postproc_config.processing_step_options.temporal_filtering.filtering_low_pass
            order = postproc_config.processing_step_options.temporal_filtering.filtering_order
            implementation_name = postproc_config.processing_step_options.temporal_filtering.implementation

            temporal_filter_implementation = _getTemporalFilterImplementation(
                implementation_name
            )

            current_wf = temporal_filter_implementation(
                hp=hp,
                lp=lp,
                tr=tr,
                order=order,
                base_dir=postproc_wf.base_dir,
                crashdump_dir=crashdump_dir,
            )

        elif step == STEP_INTENSITY_NORMALIZATION:
            implementation_name = postproc_config.processing_step_options.intensity_normalization.implementation

            intensity_normalization_implementation = (
                _getIntensityNormalizationImplementation(implementation_name)
            )

            current_wf = intensity_normalization_implementation(
                base_dir=postproc_wf.base_dir,
                mask_file=mask_file,
                crashdump_dir=crashdump_dir,
            )

        elif step == STEP_SPATIAL_SMOOTHING:
            fwhm_mm= postproc_config.processing_step_options.spatial_smoothing.fwhm
            #brightness_threshold = postproc_config.processing_step_options.spatial_smoothing.brightness_threshold
            implementation_name = postproc_config.processing_step_options.spatial_smoothing.implementation

            spatial_smoothing_implementation = _getSpatialSmoothingImplementation(implementation_name)

            current_wf = spatial_smoothing_implementation(
                base_dir=postproc_wf.base_dir,
                mask_path=mask_file,
                fwhm_mm=fwhm_mm,
                crashdump_dir=crashdump_dir,
            )

        elif step == STEP_AROMA_REGRESSION:
            implementation_name = postproc_config.processing_step_options.aroma_regression.implementation

            apply_aroma_implementation = _getAROMARegressionImplementation(
                implementation_name
            )

            current_wf = apply_aroma_implementation(
                mixing_file=mixing_file,
                noise_file=noise_file,
                mask_file=mask_file,
                base_dir=postproc_wf.base_dir,
                crashdump_dir=crashdump_dir,
            )

        elif step == STEP_CONFOUND_REGRESSION:
            implementation_name = postproc_config.processing_step_options.confoundRegression.implementation

            confound_regression_implementation = _getConfoundRegressionImplementation(
                implementation_name
            )

            current_wf = confound_regression_implementation(
                mask_file=mask_file,
                base_dir=postproc_wf.base_dir,
                crashdump_dir=crashdump_dir,
            )

            postproc_wf.connect(
                input_node, "confounds_file", current_wf, "inputnode.confounds_file"
            )

        elif step == STEP_APPLY_MASK:
            if mask_file is None:
                raise ValueError(f"{STEP_APPLY_MASK}: No mask file provided.")
            current_wf = build_apply_mask_workflow(
                mask_file=mask_file,
                base_dir=postproc_wf.base_dir,
                crashdump_dir=crashdump_dir,
            )

        elif step == STEP_TRIM_TIMEPOINTS:
            trim_from_beginning = postproc_config.processing_step_options.trim_timepoints.from_beginning
            trim_from_end = postproc_config.processing_step_options.trim_timepoints.from_end

            current_wf = build_trim_timepoints_workflow(
                trim_from_beginning=trim_from_beginning,
                trim_from_end=trim_from_end,
                base_dir=postproc_wf.base_dir,
                crashdump_dir=crashdump_dir,
            )

        elif step == STEP_RESAMPLE:
            reference_image = postproc_config.processing_step_options.resample.reference_image
            if reference_image == "SET REFERENCE IMAGE":
                raise ValueError(
                    "No reference image provided. Please set a path to reference in clpipe_config.json"
                )

            current_wf = build_resample_workflow(
                reference_image=reference_image,
                base_dir=postproc_wf.base_dir,
                crashdump_dir=crashdump_dir,
            )

        elif step == STEP_SCRUB_TIMEPOINTS:
            insert_na = postproc_config.processing_step_options.scrub_timepoints.insert_na

            current_wf = build_scrubbing_workflow(
                insert_na=insert_na,
                base_dir=postproc_wf.base_dir,
                crashdump_dir=crashdump_dir,
            )
            postproc_wf.connect(
                input_node, "scrub_vector", current_wf, "inputnode.scrub_vector"
            )

        # Send input of postproc workflow to first workflow
        if index == 0:
            postproc_wf.connect(input_node, "in_file", current_wf, "inputnode.in_file")
        # Connect previous wf to current wf
        elif step_count > 1:
            postproc_wf.connect(
                prev_wf, "outputnode.out_file", current_wf, "inputnode.in_file"
            )

        # Keep a reference to current_wf as "prev_wf" for the next loop
        prev_wf = current_wf

    # Connect the output of the last node to postproc workflow's output node
    postproc_wf.connect(prev_wf, "outputnode.out_file", output_node, "out_file")
    if export_path:
        # TODO: Update the postproc workflow to make extension guarentees
        export_node = pe.Node(
            ExportFile(out_file=export_path, clobber=True, check_extension=False),
            name="export_image",
        )
        postproc_wf.connect(current_wf, "outputnode.out_file", export_node, "in_file")

    return postproc_wf


def _getTemporalFilterImplementation(implementationName: str):
    if implementationName == IMPLEMENTATION_BUTTERWORTH:
        return build_butterworth_filter_workflow
    elif implementationName == IMPLEMENTATION_FSLMATHS:
        return build_fslmath_temporal_filter
    else:
        raise ImplementationNotFoundError(
            f"{STEP_TEMPORAL_FILTERING} implementation not found: {implementationName}"
        )


def _getIntensityNormalizationImplementation(implementationName: str):
    if implementationName == IMPLEMENTATION_10000_GLOBAL_MEDIAN:
        return build_10000_global_median_workflow
    else:
        raise ImplementationNotFoundError(
            f"{STEP_INTENSITY_NORMALIZATION} implementation not found: {implementationName}"
        )


def _getSpatialSmoothingImplementation(implementationName: str):
    if implementationName == IMPLEMENTATION_SUSAN:
        return build_SUSAN_workflow
    else:
        raise ImplementationNotFoundError(
            f"{STEP_SPATIAL_SMOOTHING} implementation not found: {implementationName}"
        )


def _getAROMARegressionImplementation(implementationName: str):
    if implementationName == IMPLEMENTATION_FSL_REGFILT:
        return build_aroma_workflow_fsl_regfilt
    if implementationName == IMPLEMENTATION_FSL_REGFILT_R:
        return build_aroma_workflow_fsl_regfilt_R
    else:
        raise ImplementationNotFoundError(
            f"{STEP_AROMA_REGRESSION} implementation not found: {implementationName}"
        )


def _getConfoundRegressionImplementation(implementationName: str):
    if implementationName == IMPLEMENTATION_FSL_GLM:
        return build_confound_regression_fsl_glm_workflow
    elif implementationName == IMPLEMENTATION_AFNI_3DTPROJECT:
        return build_confound_regression_afni_3dTproject
    else:
        raise ImplementationNotFoundError(
            f"{STEP_CONFOUND_REGRESSION} implementation not found: {implementationName}"
        )


def build_10000_global_median_workflow(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    mask_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    """Perform intensity normalization using the 10,000 global median method.

    Args:
        in_path (os.PathLike): A path to an input .nii to normalize.
        out_path (os.PathLike): A path to save the normalized image.
        mask_path (os.PathLike, optional): A path a mask to apply during the median calculation.
        base_dir (os.PathLike, optional): A path to the base directory for the workflow.
    """

    input_node = build_input_node()
    output_node = build_output_node()
    median_node = pe.Node(ImageStats(op_string="-p 50"), name="global_median")
    mul_10000_node = pe.Node(
        BinaryMaths(operation="mul", operand_value=10000), name="mul_10000"
    )
    div_median_node = pe.Node(BinaryMaths(operation="div"), name="div_median")

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    if mask_file:
        median_node.inputs.mask_file = mask_file
        median_node.inputs.op_string = "-k %s -p 50"

    workflow = pe.Workflow(
        name=f"{STEP_INTENSITY_NORMALIZATION}_{IMPLEMENTATION_10000_GLOBAL_MEDIAN}",
        base_dir=base_dir,
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    workflow.connect(input_node, "in_file", median_node, "in_file")
    workflow.connect(input_node, "in_file", mul_10000_node, "in_file")
    workflow.connect(input_node, "out_file", div_median_node, "out_file")

    workflow.connect(mul_10000_node, "out_file", div_median_node, "in_file")
    workflow.connect(median_node, "out_stat", div_median_node, "operand_value")
    workflow.connect(div_median_node, "out_file", output_node, "out_file")

    return workflow


def build_100_voxel_mean_workflow(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    """Perform intensity normalization using the 100 voxel mean method.

    Args:
        in_path (str): A path to an input .nii to normalize.
        out_path (str): A path to save the normalized image.

    Returns:
        pe.Workflow: A 100 voxel mean workflow.
    """

    if in_file != None:
        mean_image = MeanImage(in_file=in_file)
        mul_math = BinaryMaths(operation="mul", operand_value=100, in_file=in_file)
    else:
        mean_image = MeanImage()
        mul_math = BinaryMaths(operation="mul", operand_value=100)

    mean_node = pe.Node(mean_image, name="mean")
    mul100_node = pe.Node(mul_math, name="mul100")

    if out_file != None:
        div_math = BinaryMaths(operation="div", out_file=out_file)
    else:
        div_math = BinaryMaths(operation="div")
    div_mean_node = pe.Node(div_math, name="div_mean")  # operand_file=mean_path

    workflow = pe.Workflow(
        name=f"{STEP_INTENSITY_NORMALIZATION}_{IMPLEMENTATION_100_VOXEL_MEAN}",
        base_dir=base_dir,
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    workflow.connect(mul100_node, "out_file", div_mean_node, "in_file")
    workflow.connect(mean_node, "out_file", div_mean_node, "operand_file")

    return workflow


def build_SUSAN_workflow(
    in_file: os.PathLike = None,
    mask_path: os.PathLike = None,
    fwhm_mm: int = 6,
    out_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    """Builds a workflow to perform SUSAN smoothing.

    Args:
        in_file (os.PathLike, optional): The input image to smooth. Defaults to None.
        mask_path (os.PathLike, optional): A mask file specifying voxels not to use. Defaults to None.
        fwhm_mm (int, optional): Full width at half maximum in millimeters. Defaults to 6.
        out_file (os.PathLike, optional): An output path for the smoothed image. Defaults to None.

    Returns:
        pe.Workflow: A SUSAN smoothing workflow.
    """

    workflow = pe.Workflow(
        name=f"{STEP_SPATIAL_SMOOTHING}_{IMPLEMENTATION_SUSAN}", base_dir=base_dir
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    # Calculate fwhm
    fwhm_to_sigma = sqrt(8 * log(2))
    sigma = fwhm_mm / fwhm_to_sigma
    print(f"fwhm_to_sigma: {fwhm_to_sigma}")

    # Setup identity (pass through) input/output nodes
    input_node = build_input_node()
    output_node = build_output_node()

    # Setup nodes to calculate susan threshold inputs
    p2_intensity_node = pe.Node(ImageStats(op_string="-p 2"), name="p2")
    median_intensity_node = pe.Node(ImageStats(op_string="-p 50"), name="median")

    # Setup an arbitrary function node to calculate the susan threshold from two scalars with helper function
    susan_thresh_node = pe.Node(
        Function(
            inputs_names=["median_intensity", "p2_intensity"],
            output_names=["susan_threshold"],
            function=_calc_susan_threshold,
        ),
        name="susan_threshold",
    )

    # Setup susan node
    #   Usage: susan <input> <bt> <dt> <dim> <use_median> <n_usans> [<usan1> <bt1> [<usan2> <bt2>]] <output>
    #   Ref: susan {in_file} {susan_thresh} {sigma} 3 1 1 {temp_tmean} {susan_thresh} {out_file}
    tmean_image_node = pe.Node(MeanImage(), name="mean_image")
    setup_usans_node = pe.Node(
        Function(
            input_names=["tmean_image", "susan_threshold"],
            output_names=["usans_input"],
            function=_setup_usans_input,
        ),
        name="setup_usans",
    )
    susan_node = pe.Node(SUSAN(fwhm=sigma, use_median=1, dimension=3), name="SUSAN")

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
        # mean_image_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    # Map the input node to the first steps of the susan threshold calculation
    workflow.connect(input_node, "in_file", p2_intensity_node, "in_file")
    workflow.connect(input_node, "in_file", median_intensity_node, "in_file")
    workflow.connect(input_node, "in_file", susan_node, "in_file")
    workflow.connect(input_node, "in_file", tmean_image_node, "in_file")
    workflow.connect(input_node, "out_file", susan_node, "out_file")

    # Setup calculations for susan threshold
    workflow.connect(
        median_intensity_node, "out_stat", susan_thresh_node, "median_intensity"
    )
    workflow.connect(p2_intensity_node, "out_stat", susan_thresh_node, "p2_intensity")
    workflow.connect(
        susan_thresh_node, "susan_threshold", susan_node, "brightness_threshold"
    )
    workflow.connect(tmean_image_node, "out_file", setup_usans_node, "tmean_image")
    workflow.connect(
        susan_thresh_node, "susan_threshold", setup_usans_node, "susan_threshold"
    )
    workflow.connect(setup_usans_node, "usans_input", susan_node, "usans")

    # Apply Masking
    if mask_path:
        print(f"Using mask: {mask_path}")

        # Setup Masking Node to apply after smoothing
        masker_node = pe.Node(
            ApplyMask(mask_file=mask_path, output_datatype="float"), name="apply_mask"
        )
        workflow.connect(susan_node, "smoothed_file", masker_node, "in_file")
        workflow.connect(masker_node, "out_file", output_node, "out_file")

        # Add mask to the inputs of the fslstats commands
        p2_intensity_node.inputs.mask_file = mask_path
        median_intensity_node.inputs.mask_file = mask_path
        p2_intensity_node.inputs.op_string = "-k %s -p 2"
        median_intensity_node.inputs.op_string = "-k %s -p 50"
    # Tie the SUSAN output directly to output node if no mask is included
    else:
        workflow.connect(susan_node, "smoothed_file", output_node, "out_file")

    return workflow


def _calc_susan_threshold(median_intensity: float, p2_intensity: float):
    """Calculates the SUSAN threshold for a given image's median intensity
    and 2nd percentile.

    Args:
        median_intensity (float): The median value of the image.
        p2_intensity (float): The second percentile value of an image.

    Returns:
        float: The calculcated SUSAN threshold.
    """
    return (median_intensity - p2_intensity) * 0.75


def _setup_usans_input(tmean_image, susan_threshold: float):
    """Sets up the usans input for the SUSAN command.

    Args:
        tmean_image (os.PathLike): The mean image.
        susan_threshold (float): The calculated SUSAN threshold.

    Returns:
        List: A list containing the tuple (mean image, SUSAN threshold), the
        necessary format for input into SUSAN's usans parameter.
    """
    return [(tmean_image, susan_threshold)]


def build_butterworth_filter_workflow(
    hp: float,
    lp: float,
    tr: float,
    order: float = None,
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    workflow = pe.Workflow(
        name=f"{STEP_TEMPORAL_FILTERING}_{IMPLEMENTATION_BUTTERWORTH}",
        base_dir=base_dir,
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    # Setup identity (pass through) input/output nodes
    input_node = build_input_node()
    output_node = build_output_node()

    butterworth_node = pe.Node(
        ButterworthFilter(hp=hp, lp=lp, order=order, tr=tr), name="butterworth_filter"
    )

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    workflow.connect(input_node, "in_file", butterworth_node, "in_file")
    workflow.connect(input_node, "out_file", butterworth_node, "out_file")
    workflow.connect(butterworth_node, "out_file", output_node, "out_file")

    return workflow


def build_fslmath_temporal_filter(
    hp: float,
    lp: float,
    tr: float,
    order: float = None,
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    workflow = pe.Workflow(
        name=f"{STEP_TEMPORAL_FILTERING}_{IMPLEMENTATION_FSLMATHS}", base_dir=base_dir
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    # Setup identity (pass through) input/output nodes
    input_node = build_input_node()
    output_node = build_output_node()

    fwhm_to_sigma = sqrt(8 * log(2))

    hp_volumes, lp_volumes = -1, -1

    if hp != -1:
        hp_volumes = 1 / (hp * fwhm_to_sigma * tr)
    if lp != -1:
        lp_volumes = 1 / (lp * fwhm_to_sigma * tr)

    mean_image_node = pe.Node(MeanImage(), name="mean_image")
    temporal_filter_node = pe.Node(
        TemporalFilter(highpass_sigma=hp_volumes, lowpass_sigma=lp_volumes),
        name="temporal_filter",
    )
    add_node = pe.Node(BinaryMaths(operation="add"), name="add_mean")

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    workflow.connect(input_node, "in_file", mean_image_node, "in_file")
    workflow.connect(input_node, "in_file", temporal_filter_node, "in_file")
    workflow.connect(input_node, "out_file", add_node, "out_file")
    workflow.connect(mean_image_node, "out_file", add_node, "operand_file")
    workflow.connect(temporal_filter_node, "out_file", add_node, "in_file")
    workflow.connect(add_node, "out_file", output_node, "out_file")

    return workflow


def build_confound_regression_fsl_glm_workflow(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    confound_file: os.PathLike = None,
    mask_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    # TODO: This function currently returns an empy image

    workflow = pe.Workflow(
        name=f"{STEP_CONFOUND_REGRESSION}_{IMPLEMENTATION_FSL_GLM}", base_dir=base_dir
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    input_node = pe.Node(
        IdentityInterface(
            fields=["in_file", "out_file", "design_file", "mask_file"],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = pe.Node(
        IdentityInterface(fields=["out_file"], mandatory_inputs=True), name="outputnode"
    )

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file
    input_node.inputs.design_file = confound_file

    regressor_node = pe.Node(GLM(), name="fsl_glm")

    workflow.connect(input_node, "in_file", regressor_node, "in_file")
    workflow.connect(input_node, "out_file", regressor_node, "out_res_name")
    workflow.connect(input_node, "design_file", regressor_node, "design")
    workflow.connect(regressor_node, "out_res", output_node, "out_file")

    if mask_file:
        input_node.inputs.mask_file = mask_file
        workflow.connect(input_node, "mask_file", regressor_node, "mask")

    return workflow


def build_confound_regression_afni_3dTproject(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    confounds_file: os.PathLike = None,
    mask_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    # Referenc command
    # 3dTproject -input {in_file} -prefix {out_file} -ort {to_regress} -polort 0 -mask {brain_mask}

    # Something specific to confound_regression's setup is not letting it work in postproc wf builder

    workflow = pe.Workflow(
        name=f"{STEP_CONFOUND_REGRESSION}_{IMPLEMENTATION_AFNI_3DTPROJECT}",
        base_dir=base_dir,
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    input_node = pe.Node(
        IdentityInterface(
            fields=["in_file", "out_file", "confounds_file", "mask_file"],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = pe.Node(
        IdentityInterface(fields=["out_file"], mandatory_inputs=True), name="outputnode"
    )
    mean_image_node = pe.Node(MeanImage(), name="mean_image")
    add_node = pe.Node(BinaryMaths(operation="add"), name="add_mean")

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file
    if confounds_file:
        input_node.inputs.confounds_file = confounds_file

    regressor_node = pe.Node(
        TProject(polort=0, outputtype="NIFTI_GZ"), name="3dTproject"
    )

    workflow.connect(input_node, "in_file", regressor_node, "in_file")
    workflow.connect(input_node, "in_file", mean_image_node, "in_file")
    workflow.connect(input_node, "out_file", add_node, "out_file")
    workflow.connect(input_node, "confounds_file", regressor_node, "ort")
    workflow.connect(regressor_node, "out_file", add_node, "in_file")
    workflow.connect(mean_image_node, "out_file", add_node, "operand_file")
    workflow.connect(add_node, "out_file", output_node, "out_file")

    if mask_file:
        input_node.inputs.mask_file = mask_file
        workflow.connect(input_node, "mask_file", regressor_node, "mask")

    return workflow


def build_aroma_workflow_fsl_regfilt(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    mixing_file: os.PathLike = None,
    noise_file: os.PathLike = None,
    mask_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    workflow = pe.Workflow(
        name=f"{STEP_AROMA_REGRESSION}_{IMPLEMENTATION_FSL_REGFILT}", base_dir=base_dir
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    input_node = pe.Node(
        IdentityInterface(
            fields=["in_file", "out_file", "mixing_file", "noise_file", "mask_file"],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = pe.Node(
        IdentityInterface(fields=["out_file"], mandatory_inputs=True), name="outputnode"
    )

    regfilt_node = pe.Node(FilterRegressor(), name="regfilt")
    csv_to_list_node = pe.Node(
        Function(
            input_names=["csv_file"], output_names=["list"], function=_csv_to_list
        ),
        name="csv_to_list",
    )

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if mixing_file:
        input_node.inputs.mixing_file = mixing_file
    if noise_file:
        input_node.inputs.noise_file = noise_file
    if out_file:
        input_node.inputs.out_file = out_file
    if mask_file:
        input_node.inputs.mask_file = mask_file
        workflow.connect(input_node, "mask_file", regfilt_node, "mask")

    workflow.connect(input_node, "in_file", regfilt_node, "in_file")
    workflow.connect(input_node, "out_file", regfilt_node, "out_file")
    workflow.connect(input_node, "noise_file", csv_to_list_node, "csv_file")
    workflow.connect(csv_to_list_node, "list", regfilt_node, "filter_columns")
    workflow.connect(input_node, "mixing_file", regfilt_node, "design_file")
    workflow.connect(regfilt_node, "out_file", output_node, "out_file")

    return workflow


def build_aroma_workflow_fsl_regfilt_R(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    mixing_file: os.PathLike = None,
    noise_file: os.PathLike = None,
    mask_file=None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    clpipe.postprocutils.r_setup.setup_clpipe_R_lib()
    fsl_regfilt_R_script_path = pkg_resources.resource_filename(
        "clpipe", "data/R_scripts/fsl_regfilt.R"
    )

    workflow = pe.Workflow(
        name=f"{STEP_AROMA_REGRESSION}_{IMPLEMENTATION_FSL_REGFILT_R}",
        base_dir=base_dir,
    )
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    input_node = pe.Node(
        IdentityInterface(
            fields=["in_file", "out_file", "mixing_file", "noise_file"],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = pe.Node(
        IdentityInterface(fields=["out_file"], mandatory_inputs=True), name="outputnode"
    )

    regfilt_R_node = pe.Node(
        RegressAromaR(script_file=fsl_regfilt_R_script_path, n_threads=4),
        name="fsl_regfilt_R",
    )

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if mixing_file:
        input_node.inputs.mixing_file = mixing_file
    if noise_file:
        input_node.inputs.noise_file = noise_file
    if out_file:
        input_node.inputs.out_file = out_file

    workflow.connect(input_node, "in_file", regfilt_R_node, "in_file")
    # workflow.connect(input_node, "out_file", regfilt_R_node, "out_file")
    workflow.connect(input_node, "mixing_file", regfilt_R_node, "mixing_file")
    workflow.connect(input_node, "noise_file", regfilt_R_node, "noise_file")
    workflow.connect(regfilt_R_node, "out_file", output_node, "out_file")

    return workflow


def build_apply_mask_workflow(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    mask_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    workflow = pe.Workflow(name=STEP_APPLY_MASK, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    input_node = pe.Node(
        IdentityInterface(
            fields=["in_file", "out_file", "mask_file"], mandatory_inputs=False
        ),
        name="inputnode",
    )
    output_node = pe.Node(
        IdentityInterface(fields=["out_file"], mandatory_inputs=True), name="outputnode"
    )

    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file
    if mask_file:
        input_node.inputs.mask_file = mask_file

    mask_apply_node = pe.Node(BinaryMaths(operation="mul"), name="mask_apply")

    workflow.connect(input_node, "in_file", mask_apply_node, "in_file")
    workflow.connect(input_node, "mask_file", mask_apply_node, "operand_file")
    workflow.connect(mask_apply_node, "out_file", output_node, "out_file")

    return workflow


def build_trim_timepoints_workflow(
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    trim_from_beginning=None,
    trim_from_end=None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    workflow = pe.Workflow(name=STEP_TRIM_TIMEPOINTS, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    # Setup identity (pass through) input/output nodes
    input_node = build_input_node()
    output_node = build_output_node()

    slicer_node = pe.Node(
        ImageSlice(
            trim_from_beginning=trim_from_beginning, trim_from_end=trim_from_end
        ),
        name="slicer_node",
    )

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    workflow.connect(input_node, "in_file", slicer_node, "in_file")
    workflow.connect(input_node, "out_file", slicer_node, "out_file")
    workflow.connect(slicer_node, "out_file", output_node, "out_file")

    return workflow


def build_scrubbing_workflow(
    scrub_vector: list = None,
    insert_na=True,
    import_path: os.PathLike = None,
    export_path: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    workflow = pe.Workflow(name=STEP_SCRUB_TIMEPOINTS, base_dir=base_dir)
    """ Workflow for scrubbing a target file based on given scrub targets."""

    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    # Setup identity (pass through) input/output nodes
    input_node = pe.Node(
        IdentityInterface(
            fields=["in_file", "out_file", "scrub_vector", "insert_na"],
            mandatory_inputs=False,
        ),
        name="inputnode",
    )
    output_node = build_output_node()

    scrub_node = pe.Node(
        Function(
            input_names=["nii_file", "scrub_vector", "insert_na", "export_path"],
            output_names=["out_file"],
            function=scrub_image,
        ),
        name="scrub_timepoints",
    )

    # Set WF inputs and outputs
    if import_path:
        input_node.inputs.in_file = import_path
    if export_path:
        input_node.inputs.out_file = export_path
    if scrub_vector:
        input_node.inputs.scrub_vector = scrub_vector
    input_node.inputs.insert_na = insert_na

    workflow.connect(input_node, "in_file", scrub_node, "nii_file")
    workflow.connect(input_node, "scrub_vector", scrub_node, "scrub_vector")
    workflow.connect(input_node, "insert_na", scrub_node, "insert_na")
    workflow.connect(input_node, "out_file", scrub_node, "export_path")
    workflow.connect(scrub_node, "out_file", output_node, "out_file")

    return workflow


def build_resample_workflow(
    reference_image: os.PathLike = None,
    in_file: os.PathLike = None,
    out_file: os.PathLike = None,
    base_dir: os.PathLike = None,
    crashdump_dir: os.PathLike = None,
):
    workflow = pe.Workflow(name=STEP_RESAMPLE, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config["execution"]["crashdump_dir"] = crashdump_dir

    # Setup identity (pass through) input/output nodes
    input_node = build_input_node()
    output_node = build_output_node()

    resample_node = pe.Node(
        FLIRT(apply_xfm=True, reference=reference_image, uses_qform=True),
        name="resample",
    )

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    workflow.connect(input_node, "in_file", resample_node, "in_file")
    workflow.connect(input_node, "out_file", resample_node, "out_file")
    workflow.connect(resample_node, "out_file", output_node, "out_file")

    return workflow


def _csv_to_list(csv_file):
    # Imports must be in function for running as node
    import numpy as np
    from pathlib import Path

    # Read in the csv
    data = np.loadtxt(csv_file, delimiter=",", dtype=np.int64)
    data_list = list(data)

    return data_list
