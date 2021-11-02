import os

from nipype.interfaces.fsl.maths import MeanImage, BinaryMaths, MedianImage
from nipype.interfaces.fsl.utils import ImageStats
import nipype.pipeline.engine as pe

from .nodes import ButterworthFilter

RESCALING_10000_GLOBALMEDIAN = "10000_globalmedian"
RESCALING_100_VOXELMEAN = "100_voxelmean"
NORMALIZATION_METHODS = (RESCALING_10000_GLOBALMEDIAN, RESCALING_100_VOXELMEAN)

def build_postprocessing_workflow(name, in_path: os.PathLike, out_path:os.PathLike, 
    base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    
    wf = pe.Workflow(name=name, base_dir=base_dir)
    
    if crashdump_dir is not None:
        wf.config['execution']['crashdump_dir'] = crashdump_dir
    
    voxel_mean_wf = build_100_voxel_mean_workflow(None, in_path, base_dir=wf.base_dir)
    butterworth_node = pe.Node(ButterworthFilter(in_file=out_path,
                            hp=.008,lp=-1,order=2,tr=2), name="butterworth_filter")

    wf.connect([
        (butterworth_node, voxel_mean_wf, [("out_file","mean.in_file"),
                                            ("out_file","mul100.in_file")])
    ])

    return wf

def build_10000_global_median_workflow(in_path: os.PathLike, out_path:os.PathLike,
        mask_path: os.PathLike=None, base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    """Perform intensity normalization using the 10,000 global median method.

    Args:
        in_path (os.PathLike): A path to an input .nii to normalize.
        out_path (os.PathLike): A path to save the normalized image.
        mask_path (os.PathLike, optional): A path a mask to apply during the median calculation.
        base_dir (os.PathLike, optional): A path to the base directory for the workflow.
    """

    if mask_path:
        median_node = pe.Node(ImageStats(in_file=in_path, op_string="-k %s -p 50", mask_file=mask_path), name='global_median')
    else:
        median_node = pe.Node(ImageStats(in_file=in_path, op_string="-p 50"), name='global_median')

    mul_10000_node = pe.Node(BinaryMaths(in_file=in_path, operation="mul", operand_value=10000), name="mul_10000")
    div_median_node = pe.Node(BinaryMaths(operation="div", out_file=out_path), name="div_median")

    workflow = pe.Workflow(name=RESCALING_10000_GLOBALMEDIAN, base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    workflow.connect(mul_10000_node, "out_file", div_median_node, "in_file")
    workflow.connect(median_node, "out_stat", div_median_node, "operand_value")
    
    return workflow

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