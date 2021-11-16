import os

from math import sqrt, log

from nipype.interfaces.fsl.maths import MeanImage, BinaryMaths, MedianImage
from nipype.interfaces.fsl.utils import ImageStats
from nipype.interfaces.fsl import SUSAN
from nipype.interfaces.utility import Function
import nipype.pipeline.engine as pe

from .nodes import ButterworthFilter

RESCALING_10000_GLOBALMEDIAN = "10000_globalmedian"
RESCALING_100_VOXELMEAN = "100_voxelmean"
NORMALIZATION_METHODS = (RESCALING_10000_GLOBALMEDIAN, RESCALING_100_VOXELMEAN)

def build_postprocessing_workflow(name, in_path: os.PathLike, out_path:os.PathLike, 
    mask_path: os.PathLike=None, temporal_filter=True, intensity_normalize=True, base_dir: os.PathLike=None, 
    crashdump_dir: os.PathLike=None):
    
    wf = pe.Workflow(name=name, base_dir=base_dir)
    
    if crashdump_dir is not None:
        wf.config['execution']['crashdump_dir'] = crashdump_dir
    
    # The most recently added node or wf
    previous_step = None

    # Initialize WF Components
    butterworth_node = pe.Node(ButterworthFilter(hp=.008,lp=-1,order=2,tr=2), name="butterworth_filter")
    normalize_10000_gm_wf = build_10000_global_median_workflow(base_dir=wf.base_dir, mask_path=mask_path, crashdump_dir=wf.config['execution']['crashdump_dir'])
    smoothing_wf = build_spatial_smoothing_workflow(base_dir=wf.base_dir, mask_path=mask_path, crashdump_dir=wf.config['execution']['crashdump_dir'])

    butterworth_node.inputs.in_file = in_path

    wf.connect([
            (butterworth_node, normalize_10000_gm_wf, [("out_file","global_median.in_file"),
                                                       ("out_file","mul_10000.in_file")])
    ])
    wf.connect([
            (normalize_10000_gm_wf, smoothing_wf, [("div_median.out_file","p2.in_file"),
                                                   ("div_median.out_file","median.in_file"),
                                                   ("div_median.out_file", "SUSAN.in_file")])
    ])

    smoothing_wf.inputs.SUSAN.out_file = out_path
    
    return wf

def build_10000_global_median_workflow(in_path: os.PathLike=None, out_path:os.PathLike=None,
        mask_path: os.PathLike=None, base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    """Perform intensity normalization using the 10,000 global median method.

    Args:
        in_path (os.PathLike): A path to an input .nii to normalize.
        out_path (os.PathLike): A path to save the normalized image.
        mask_path (os.PathLike, optional): A path a mask to apply during the median calculation.
        base_dir (os.PathLike, optional): A path to the base directory for the workflow.
    """

    median_node = pe.Node(ImageStats(op_string="-p 50"), name='global_median')
    mul_10000_node = pe.Node(BinaryMaths(operation="mul", operand_value=10000), name="mul_10000")
    div_median_node = pe.Node(BinaryMaths(operation="div"), name="div_median")

    if in_path:
        median_node.inputs.in_file = in_path
        mul_10000_node.inputs.in_file = in_path

    if out_path:
        div_median_node.inputs.out_file = out_path

    if mask_path:
        median_node.inputs.mask_file = mask_path
        median_node.inputs.op_string = "-k %s -p 50"


    workflow = pe.Workflow(name=RESCALING_10000_GLOBALMEDIAN, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    workflow.connect(mul_10000_node, "out_file", div_median_node, "in_file")
    workflow.connect(median_node, "out_stat", div_median_node, "operand_value")
    
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
    
    fwhm_to_sigma = sqrt(8 * log(2))
    sigma = fwhm_mm / fwhm_to_sigma
    print(f"fwhm_to_sigma: {fwhm_to_sigma}")
    
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
    
    # Use an arbitrary function node to calculate the susan threshold from two scalars with helper function
    susan_thresh_node = pe.Node(Function(inputs_names=["median_intensity", "p2_intensity"], output_names=["susan_threshold"], function=_calc_susan_threshold), name="susan_threshold")

    # Setup calculations for susan threshold
    workflow.connect(median_intensity_node, "out_stat", susan_thresh_node, "median_intensity")
    workflow.connect(p2_intensity_node, "out_stat", susan_thresh_node, "p2_intensity")

    # Setup susan command
    #   Usage: susan <input> <bt> <dt> <dim> <use_median> <n_usans> [<usan1> <bt1> [<usan2> <bt2>]] <output>
    susan_node = pe.Node(SUSAN(fwhm=sigma, use_median=1, dimension=3), name="SUSAN")
    
    #nmean_image_node = pe.Node(MeanImage(), name="mean_image")

    # Set WF inputs and outputs
    if in_file:
        p2_intensity_node.inputs.in_file = in_file
        median_intensity_node.inputs.in_file = in_file
        susan_node.inputs.in_file = in_file
        #mean_image_node.inputs.in_file = in_file
    if out_file:
        susan_node.inputs.out_file = out_file

    workflow.connect(susan_thresh_node, "susan_threshold", susan_node, "brightness_threshold")
    #workflow.connect(mean_image_node, "out_file", susan_node, "")
    
    if mask_path is not None:
        # run_fsl_command(glue("fslmaths {out_file} -mas {brain_mask} {out_file} -odt float"), log_file = log_file)
        pass
        
    return workflow
    
def _calc_susan_threshold(median_intensity, p2_intensity):
    return (median_intensity - p2_intensity) * .75