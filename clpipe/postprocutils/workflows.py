import os

from math import sqrt, log

from nipype.interfaces.fsl.maths import MeanImage, BinaryMaths, MedianImage
from nipype.interfaces.fsl.utils import ImageStats
from nipype.interfaces.fsl import SUSAN
from nipype.interfaces.utility import Function
import nipype.pipeline.engine as pe

from .nodes import build_input_node, build_output_node, ButterworthFilter

RESCALING_10000_GLOBALMEDIAN = "globalmedian_10000"
RESCALING_100_VOXELMEAN = "voxelmean_100"
NORMALIZATION_METHODS = (RESCALING_10000_GLOBALMEDIAN, RESCALING_100_VOXELMEAN)

def build_postprocessing_workflow(name, in_file: os.PathLike, out_file:os.PathLike, 
    mask_file: os.PathLike=None, processing_steps=["temporal_filtering", "intensity_normalization", "spatial_smoothing"], base_dir: os.PathLike=None, 
    crashdump_dir: os.PathLike=None):
    
    postproc_wf = pe.Workflow(name=name, base_dir=base_dir)
    
    if crashdump_dir is not None:
        postproc_wf.config['execution']['crashdump_dir'] = crashdump_dir
    
    step_count = len(processing_steps)
    if step_count < 2:
        raise ValueError("The PostProcess workflow requires at least 2 processing steps. Steps given: {step_count}")

    current_wf = None
    prev_wf = None

    for index, step in enumerate(processing_steps):
        # Decide which wf to add next
        if step == "temporal_filtering":
            current_wf = build_butterworth_filter_workflow(hp=.008,lp=-1, tr=2, order=2, base_dir=postproc_wf.base_dir, crashdump_dir=postproc_wf.config['execution']['crashdump_dir'])
        
        elif step == "intensity_normalization":
            current_wf = build_10000_global_median_workflow(base_dir=postproc_wf.base_dir, mask_file=mask_file, crashdump_dir=postproc_wf.config['execution']['crashdump_dir'])
        
        elif step == "spatial_smoothing":
            current_wf = build_spatial_smoothing_workflow(base_dir=postproc_wf.base_dir, mask_path=mask_file, crashdump_dir=postproc_wf.config['execution']['crashdump_dir'])

        # Set inputs instead of a connection for first workflow
        if index == 0:
            current_wf.inputs.inputnode.in_file = in_file
        # Connect previous wf to current wf
        else:
            postproc_wf.connect(prev_wf, "outputnode.out_file", current_wf, "inputnode.in_file")
            
            # If we handling the last node, set its out_file
            if index == step_count - 1:
                current_wf.inputs.inputnode.out_file = out_file

        # Keep a reference to current_wf as "prev_wf" for the next loop
        prev_wf = current_wf
    
    return postproc_wf

def build_10000_global_median_workflow(in_file: os.PathLike=None, out_file:os.PathLike=None,
        mask_file: os.PathLike=None, base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    """Perform intensity normalization using the 10,000 global median method.

    Args:
        in_path (os.PathLike): A path to an input .nii to normalize.
        out_path (os.PathLike): A path to save the normalized image.
        mask_path (os.PathLike, optional): A path a mask to apply during the median calculation.
        base_dir (os.PathLike, optional): A path to the base directory for the workflow.
    """

    input_node = build_input_node()
    output_node = build_output_node()
    median_node = pe.Node(ImageStats(op_string="-p 50"), name='global_median')
    mul_10000_node = pe.Node(BinaryMaths(operation="mul", operand_value=10000), name="mul_10000")
    div_median_node = pe.Node(BinaryMaths(operation="div"), name="div_median")

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
        # mean_image_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    if mask_file:
        median_node.inputs.mask_file = mask_file
        median_node.inputs.op_string = "-k %s -p 50"


    workflow = pe.Workflow(name=RESCALING_10000_GLOBALMEDIAN, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    workflow.connect(input_node, "in_file", median_node, "in_file")
    workflow.connect(input_node, "in_file", mul_10000_node, "in_file")
    workflow.connect(input_node, "out_file", div_median_node, "out_file")

    workflow.connect(mul_10000_node, "out_file", div_median_node, "in_file")
    workflow.connect(median_node, "out_stat", div_median_node, "operand_value")
    workflow.connect(div_median_node, "out_file", output_node, "out_file")
    
    return workflow

#TODO: Rewrite to not use multiple instantiation variants
def build_100_voxel_mean_workflow(in_file: os.PathLike=None, out_file: os.PathLike=None, base_dir: os.PathLike=None,
    crashdump_dir: os.PathLike=None):
    """Perform intensity normalization using the 100 voxel mean method.

    Args:
        in_path (str): A path to an input .nii to normalize.
        out_path (str): A path to save the normalized image.
    """
    
    if in_file != None:
        mean_image = MeanImage(in_file=in_file)
        mul_math = BinaryMaths(operation='mul', operand_value=100, in_file=in_file)
    else:
        mean_image = MeanImage()
        mul_math = BinaryMaths(operation='mul', operand_value=100)
    
    mean_node = pe.Node(mean_image, name='mean')
    mul100_node = pe.Node(mul_math, name="mul100")

    if out_file != None:
        div_math = BinaryMaths(operation='div', out_file=out_file)
    else:
        div_math = BinaryMaths(operation='div')
    div_mean_node = pe.Node(div_math, name="div_mean") #operand_file=mean_path

    workflow = pe.Workflow(name=RESCALING_100_VOXELMEAN, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    workflow.connect(mul100_node, "out_file", div_mean_node, "in_file")
    workflow.connect(mean_node, "out_file",  div_mean_node, "operand_file")

    return workflow

def build_spatial_smoothing_workflow(in_file: os.PathLike=None, mask_path: os.PathLike=None, fwhm_mm: int=6, out_file: os.PathLike=None, 
    base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    
    workflow = pe.Workflow(name="spatial_smoothing", base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir
    
    # Calculate fwhm
    fwhm_to_sigma = sqrt(8 * log(2))
    sigma = fwhm_mm / fwhm_to_sigma
    print(f"fwhm_to_sigma: {fwhm_to_sigma}")

    # Setup identity (pass through) input/output nodes
    input_node = build_input_node()
    output_node = build_output_node()
    
    # Setup nodes to calculate susan threshold inputs
    p2_intensity_node = pe.Node(ImageStats(op_string="-p 2"), name='p2')
    median_intensity_node = pe.Node(ImageStats(op_string="-p 50"), name='median')
    
    # Add mask to commands
    if mask_path:
        print(f"Using mask: {mask_path}")
        p2_intensity_node.inputs.mask_file = mask_path
        median_intensity_node.inputs.mask_file = mask_path
        p2_intensity_node.inputs.op_string = "-k %s -p 2"
        median_intensity_node.inputs.op_string = "-k %s -p 50"
    
    # Setup an arbitrary function node to calculate the susan threshold from two scalars with helper function
    susan_thresh_node = pe.Node(Function(inputs_names=["median_intensity", "p2_intensity"], output_names=["susan_threshold"], function=_calc_susan_threshold), name="susan_threshold")

    # Setup susan node
    #   Usage: susan <input> <bt> <dt> <dim> <use_median> <n_usans> [<usan1> <bt1> [<usan2> <bt2>]] <output>
    susan_node = pe.Node(SUSAN(fwhm=sigma, use_median=1, dimension=3), name="SUSAN")
    
    #nmean_image_node = pe.Node(MeanImage(), name="mean_image")

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
    workflow.connect(input_node, "out_file", susan_node, "out_file")

    # Setup calculations for susan threshold
    workflow.connect(median_intensity_node, "out_stat", susan_thresh_node, "median_intensity")
    workflow.connect(p2_intensity_node, "out_stat", susan_thresh_node, "p2_intensity")
    workflow.connect(susan_thresh_node, "susan_threshold", susan_node, "brightness_threshold")
    workflow.connect(susan_node, "smoothed_file", output_node, "out_file")
    #workflow.connect(mean_image_node, "out_file", susan_node, "")
    
    if mask_path is not None:
        # run_fsl_command(glue("fslmaths {out_file} -mas {brain_mask} {out_file} -odt float"), log_file = log_file)
        pass
        
    return workflow
    
def _calc_susan_threshold(median_intensity, p2_intensity):
    return (median_intensity - p2_intensity) * .75

def build_butterworth_filter_workflow(hp: float, lp: float, tr: float, order: float, in_file: os.PathLike=None, 
    out_file: os.PathLike=None, base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    
    workflow = pe.Workflow(name="temporal_filtering", base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    # Setup identity (pass through) input/output nodes
    input_node = build_input_node()
    output_node = build_output_node()

    butterworth_node = pe.Node(ButterworthFilter(hp=hp,lp=lp,order=order,tr=tr), name="butterworth_filter")

    # Set WF inputs and outputs
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    workflow.connect(input_node, "in_file", butterworth_node, "in_file")
    workflow.connect(input_node, "out_file", butterworth_node, "out_file")
    workflow.connect(butterworth_node, "out_file", output_node, "out_file")

    return workflow