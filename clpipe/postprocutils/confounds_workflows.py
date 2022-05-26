import os
import copy
from typing import List

from nipype.interfaces.utility import Function, IdentityInterface
import nipype.pipeline.engine as pe

from .workflows import build_postprocessing_workflow
# The list of temporal-based processing steps applicable to confounds
CONFOUND_STEPS = {"TemporalFiltering", "AROMARegression", "DropTimepoints"}


def build_confounds_processing_workflow(postprocessing_config: dict, confounds_file: os.PathLike=None, 
    out_file: os.PathLike=None, mixing_file: os.PathLike=None, noise_file: os.PathLike=None, tr: float = None,
    name:str = "Confounds_Processing_Pipeline", processing_steps: list=None, column_names: list=None,
    base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    """ Builds a processing workflow specifically for a given confounds file. If any temporal postprocessing
    steps are included, those steps will be run on the confounds file as well.

    Args:
        postprocessing_config (dict): The instructions for postprocessing.
        confound_file (os.PathLike, optional): The input confounds file. Defaults to None.
        out_file (os.PathLike, optional): The processed confounds file. Defaults to None.
        mixing_file (os.PathLike, optional): The AROMA mixing file. Defaults to None.
        noise_file (os.PathLike, optional): The AROMA noise file. Defaults to None.
        tr (int, optional): The repetition time. Defaults to None.
        name (str, optional): Name of the workflow. Defaults to "Confounds_Processing_Pipeline".
        processing_steps (list, optional): List of processing steps. Defaults to None.
        column_names (list, optional): List of confounds column names to keep. Defaults to None.

    Returns:
        pe.Workflow: A confound processing workflow.
    """
    
    if processing_steps is None:
        processing_steps = postprocessing_config["ProcessingSteps"]
    if column_names is None:
        column_names = postprocessing_config["ConfoundOptions"]["Columns"]

    # Force use of the R variant of fsl_regfilt for confounds
    if "AROMARegression" in processing_steps:
        postprocessing_config = copy.deepcopy(postprocessing_config)
        postprocessing_config["ProcessingStepOptions"]["AROMARegression"]["Algorithm"] = "fsl_regfilt_R"

    motion_outliers = False
    try:
        motion_outliers = postprocessing_config["ConfoundOptions"]["MotionOutliers"]["Include"]
    except KeyError:
        motion_outliers = False

    confounds_wf = pe.Workflow(name=name, base_dir=base_dir)
    if crashdump_dir is not None:
        confounds_wf.config['execution']['crashdump_dir'] = crashdump_dir
       
    input_node = pe.Node(IdentityInterface(fields=['in_file', 'out_file', 'columns', 'mixing_file', 'noise_file', 'mask_file'], mandatory_inputs=False), name="inputnode")
    output_node = pe.Node(IdentityInterface(fields=['out_file'], mandatory_inputs=True), name="outputnode")

    # Set WF inputs and outputs
    if confounds_file:
        input_node.inputs.in_file = confounds_file
    if out_file:
        input_node.inputs.out_file = out_file

    # Select any of the postprocessing steps that apply to confounds
    confounds_processing_steps = []
    for step in processing_steps:
        if step in CONFOUND_STEPS:
            confounds_processing_steps.append(step)

    # Setup the confounds file prep workflow
    current_wf = build_confounds_prep_workflow(column_names, base_dir=base_dir, crashdump_dir=crashdump_dir)
    confounds_wf.connect(input_node, "in_file", current_wf, "inputnode.in_file")

    # Setup postprocessing workflow if any relevant postprocessing steps are included
    if confounds_processing_steps:
       pass

    # Provide motion outlier columns if requested
    if motion_outliers:

        threshold = postprocessing_config["ConfoundOptions"]["MotionOutliers"]["Threshold"]
        scrub_var = postprocessing_config["ConfoundOptions"]["MotionOutliers"]["ScrubVar"]
        scrub_ahead = postprocessing_config["ConfoundOptions"]["MotionOutliers"]["ScrubAhead"]
        scrub_behind = postprocessing_config["ConfoundOptions"]["MotionOutliers"]["ScrubBehind"]
        scrub_contiguous = postprocessing_config["ConfoundOptions"]["MotionOutliers"]["ScrubContiguous"]

        
    else:
        confounds_wf.connect(select_headers_node, "headers", nii_to_tsv_node, "headers")
        confounds_wf.connect(nii_to_tsv_node, "tsv_file", output_node, "out_file")

    confounds_wf.connect(current_wf, "outputnode.out_file", output_node, "out_file")

    return confounds_wf


def build_confounds_prep_workflow(column_names: List, in_file: os.PathLike=None, out_file: os.PathLike=None, 
    base_dir: os.PathLike=None, crashdump_dir: os.PathLike=None):
    """ Prepares a confound file for processing by selecting a subset of columns and replacing NAs with 
    the column mean.

    Args:
        column_names List: A list of columns from the input confounds file to keep
        in_file (os.PathLike, optional): The input confounds file. Defaults to None.
        out_file (os.PathLike, optional): The prepped confounds file. Defaults to None.

    Returns:
        pe.Workflow: An intial confounds prep workflow
    """
    workflow = pe.Workflow(name="Confounds_Prep", base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    input_node = pe.Node(IdentityInterface(fields=['in_file', 'out_file', 'columns'], mandatory_inputs=False), name="inputnode")
    output_node = pe.Node(IdentityInterface(fields=['out_file'], mandatory_inputs=True), name="outputnode")

    tsv_select_node = pe.Node(Function(input_names=["tsv_file", "column_names"], output_names=["tsv_subset_file"], function=_tsv_select_columns), name="tsv_select_columns")
    tsv_replace_nas_node = pe.Node(Function(input_names=["tsv_file"], output_names=["tsv_no_na"], function=_tsv_replace_nas_with_column_mean), name="tsv_replace_nas") 
    
    if in_file:
        input_node.inputs.in_file = in_file
    if out_file:
        input_node.inputs.out_file = out_file

    input_node.inputs.column_names = column_names

    # Setup input connections
    workflow.connect(input_node, "in_file", tsv_select_node, "tsv_file")
    workflow.connect(input_node, "column_names", tsv_select_node, "column_names")

    # Select desired columns from input tsv, replace n/a values with column mean, and convert it to a .nii file
    workflow.connect(tsv_select_node, "tsv_subset_file", tsv_replace_nas_node, "tsv_file")
    
    workflow.connect(tsv_replace_nas_node, "tsv_no_na", output_node, "out_file")

    return workflow


def build_confounds_postprocessing_workflow(postprocessing_config: dict, confounds_processing_steps: List, mixing_file: os.PathLike, tr: float,
    noise_file: os.PathLike, in_file: os.PathLike=None, out_file: os.PathLike=None, base_dir=None, crashdump_dir=None):
    """ Wraps the postprocessing workflow builder. Converts the confounds file into a .nii file to run in the postprocessing workflow,
        then converts the processed image back into a .tsv.

    Args:
        postprocessing_config (dict): The instructions for postprocessing.
        confounds_processing_steps (List): The confound-specific postprocessing steps to run.
        tr (float): Repetition time.
        mixing_file (os.PathLike): The AROMA mixing file. Defaults to None.
        noise_file (os.PathLike): The AROMA noise file. Defaults to None.
        in_file (os.PathLike, optional): The confounds file. Defaults to None.
        out_file (os.PathLike, optional): The postprocessed confounds file. Defaults to None.
    """


    workflow = pe.Workflow(name="Confounds_Postprocessing", base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    # TODO: Replace
    input_node = pe.Node(IdentityInterface(fields=['in_file', 'out_file', 'mixing_file', 'noise_file'], mandatory_inputs=False), name="inputnode")
    output_node = pe.Node(IdentityInterface(fields=['out_file'], mandatory_inputs=True), name="outputnode")

    if out_file:
        input_node.inputs.out_file = out_file

    tsv_to_nii_node = pe.Node(Function(input_names=["tsv_file"], output_names=["nii_file"], function=_tsv_to_nii), name="tsv_to_nii")
    nii_to_tsv_node = pe.Node(Function(input_names=["nii_file", "tsv_file", "headers"], output_names=["tsv_file"], function=_nii_to_tsv), name="nii_to_tsv")
    select_headers_node = pe.Node(Function(input_names=["tsv_file"], output_names=["headers"], function=_tsv_select_headers), name="tsv_select_headers")

    # Build the inner postprocessing workflow
    postproc_wf = build_postprocessing_workflow(postprocessing_config, processing_steps=confounds_processing_steps, name="Confounds_Apply_Postprocessing", 
        mixing_file=mixing_file, noise_file=noise_file, tr=tr)

    # Input the .nii file into the postprocessing workflow
    workflow.connect(tsv_to_nii_node, "nii_file", postproc_wf, "inputnode.in_file")

    # Convert the output of the postprocessing workflow back to .tsv format
    workflow.connect(postproc_wf, "outputnode.out_file", nii_to_tsv_node, "nii_file")


def build_confounds_add_motion_outliers_workflow(threshold, scrub_var, scrub_ahead, scrub_behind, scrub_contiguous, 
    in_file=None, out_file=None, base_dir=None, crashdump_dir=None):
    workflow = pe.Workflow(name="Confounds_Add_Motion_Outliers", base_dir=base_dir)
    if crashdump_dir is not None:
        workflow.config['execution']['crashdump_dir'] = crashdump_dir

    # TODO: Replace
    input_node = pe.Node(IdentityInterface(fields=['in_file', 'out_file', 'columns'], mandatory_inputs=False), name="inputnode")
    output_node = pe.Node(IdentityInterface(fields=['out_file', 'headers'], mandatory_inputs=True), name="outputnode")

    add_motion_outliers_node = pe.Node(Function(input_names=["confounds_file", "scrub_var", "threshold", "scrub_ahead", "scrub_behind", "scrub_contiguous"], 
            output_names=["out_file"], function=_add_motion_outliers), name="add_motion_outliers")
    add_motion_outliers_node.inputs.threshold = threshold
    add_motion_outliers_node.inputs.scrub_var = scrub_var
    add_motion_outliers_node.inputs.scrub_ahead = scrub_ahead
    add_motion_outliers_node.inputs.scrub_behind = scrub_behind
    add_motion_outliers_node.inputs.scrub_contiguous = scrub_contiguous

    combine_confounds_node = pe.Node(Function(input_names=["base_file", "append_file"], 
        output_names=["out_file"], function=_combine_confounds_files), name="combine_confounds")            

    workflow.connect(input_node, "in_file", add_motion_outliers_node, "confounds_file")
    workflow.connect(input_node, "in_file", combine_confounds_node, "base_file")
    workflow.connect(add_motion_outliers_node, "out_file", combine_confounds_node, "append_file")

    workflow.connect(combine_confounds_node, "out_file", output_node, "out_file")


def _add_motion_outliers(confounds_file, scrub_var, threshold, scrub_ahead, scrub_behind, scrub_contiguous):
    from pathlib import Path
    import pandas as pd
    from clpipe.postprocutils.utils import scrub_setup
    from clpipe.glm_setup import _construct_motion_outliers

    confounds_df = pd.read_csv(confounds_file, sep="\t")

    # Get the column to be used for thresholding
    timepoints = confounds_df[scrub_var]

    # Gather the scrub indexes
    scrub_targets = scrub_setup(timepoints, threshold, scrub_behind, scrub_ahead, scrub_contiguous)
    # Create outlier columns
    mot_outliers = _construct_motion_outliers(scrub_targets)
    # Give the outlier columns names
    mot_outliers.columns=[f"motion_outlier_{i}" for i in range(1, len(mot_outliers.columns) + 1)]
    # Cast to int
    mot_outliers = mot_outliers.astype(int)

    # Build the output path
    out_folder = Path(confounds_file).parent
    out_file = out_folder / "motion_outliers.tsv"

    mot_outliers.to_csv(out_file, sep="\t", index=False)

    return str(out_file.absolute())


def _combine_confounds_files(base_confounds_file, append_confounds_file):
    from pathlib import Path
    import pandas as pd

    base_confounds_df = pd.read_csv(base_confounds_file, sep="\t")
    append_confounds_df = pd.read_csv(append_confounds_file, sep="\t")

    # Concat append df with base df
    combined_confounds_df = pd.concat([base_confounds_df, append_confounds_df],axis=1)

    # Build the output path
    out_file = Path(base_confounds_file).stem
    out_file = Path(out_file + "_combined.tsv")

    combined_confounds_df.to_csv(out_file, sep="\t", index=False)

    return str(out_file.absolute())



def _tsv_select_columns(tsv_file, column_names):
    # Imports must be in function for running as node
    import pandas as pd
    from pathlib import Path

    df = pd.read_csv(tsv_file, sep="\t")
    df = df[column_names]

    # Build the output path
    tsv_file = Path(tsv_file).stem
    tsv_subset_file = Path(tsv_file + "_subset.tsv")

    df.to_csv(tsv_subset_file, sep="\t", index=False)

    return str(tsv_subset_file.absolute())


def _tsv_replace_nas_with_column_mean(tsv_file):
    # Imports must be in function for running as node
    import pandas as pd
    from pathlib import Path

    df = pd.read_csv(tsv_file, sep="\t")

    # Get all of the columns with n/a values
    na_columns = df.columns[df.isna().any()].tolist()

    # Replace n/a values with column mean
    for column in na_columns:
        df[column] = df[column].fillna(df[column].mean())

    # Build the output path
    tsv_file = Path(tsv_file).stem
    tsv_subset_file = Path(tsv_file + "_replace-nas.tsv")

    df.to_csv(tsv_subset_file, sep="\t", index=False)

    return str(tsv_subset_file.absolute())


def _tsv_select_headers(tsv_file):
    import pandas as pd

    df = pd.read_csv(tsv_file, sep="\t")
    
    return list(df.columns)


def _tsv_to_nii(tsv_file):
    # Imports must be in function for running as node
    import pandas as pd
    import numpy as np
    import nibabel as nib
    from pathlib import Path

    # Read in the confound tsv
    # skiprows=1 skips the header row
    df = pd.read_csv(tsv_file, sep="\t")
    matrix = df.to_numpy()

    # Transpose the matrix so that time is on axis 1
    transposed_matrix = np.swapaxes(matrix, 0, 1)

    # Pad the input matrix with two extra dimensions so that the confounds are on the
    # 1st dimension (x) and time is on the 4th dimension - NIFTI standard
    padded_tensor = np.expand_dims(transposed_matrix, (1, 2))

    # Build an identity affine
    affine = np.eye(4)

    # Build the output path
    tsv_file = Path(tsv_file)
    path_stem = tsv_file.stem
    nii_path = Path(path_stem + ".nii")

    # Build wrapper NIFTI image
    image = nib.Nifti1Image(padded_tensor, affine)
    nib.save(image, nii_path)

    return str(nii_path.absolute())


def _nii_to_tsv(nii_file, tsv_file=None, headers=None):
    # Imports must be in function for running as node
    import numpy as np
    import pandas as pd
    import nibabel as nib
    from pathlib import Path

    nii_img = nib.load(nii_file)
    img_data = nii_img.get_fdata()

    # remove the y and z dimension for conversion back to x, time matrix
    squeezed_img_data = np.squeeze(img_data, (1, 2))
    # transpose the data back
    transposed_matrix = np.swapaxes(squeezed_img_data, 0, 1)

    if not tsv_file:
        # Build the output path
        nii_file = Path(nii_file)
        path_stem = nii_file.stem
        tsv_file = Path(path_stem + ".tsv")
        tsv_file = str(tsv_file.absolute())

    transposed_df = pd.DataFrame(transposed_matrix, columns=headers)
    transposed_df.to_csv(tsv_file, sep="\t", index=False)
    
    return tsv_file