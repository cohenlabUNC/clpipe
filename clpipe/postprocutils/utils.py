import logging
import nipype.pipeline.engine as pe
from pathlib import Path
import os

from typing import List


DEFAULT_GRAPH_STYLE = "colored"


def find_sub_list(sl, l):
    results = []
    sll = len(sl)
    for ind in (i for i, e in enumerate(l) if e == sl[0]):
        if l[ind : ind + sll] == sl:
            results.append((ind, ind + sll))

    return results


def get_scrub_vector(fdts, fd_thres=0.3, fd_behind=1, fd_ahead=1, fd_contig=3):
    """Given a vector of timepoints for scrubbing, create a list of indexes representing
    scrub targets based given behind, ahead, and contigous selections.

    Args:
        fdts (_type_): the input vector, a timeseries to scrub
        fd_thres (float, optional): the cutoff threshold for inclusion
        fd_behind (int, optional):
        fd_ahead (int, optional):
        fd_contig (int, optional):

    Returns:
        _type_: the fully prepared scrub target vector
    """
    import numpy

    # index all timepoints that exceed the threshold as the base scrub targets
    scrubTargets = [i for i, e in enumerate(fdts) if e > fd_thres]

    # Generate scrub indexes behind the base targets
    for t in numpy.arange(0, fd_behind + 1):
        scrubTargetsAdd = scrubTargets - t
        scrubTargets.extend(scrubTargetsAdd)

    # Generate scrub indexes ahead of the base targets
    for t in numpy.arange(0, fd_ahead + 1):
        scrubTargetsAdd = scrubTargets + t
        scrubTargets.extend(scrubTargetsAdd)

    # Remove duplicates by converting to a set temporarily
    scrubTargets = list(set(scrubTargets))
    # Remove negatives
    scrubTargets = [e for i, e in enumerate(scrubTargets) if e >= 0]
    # Remove items outside the bounds of the original set of indexes
    scrubTargets = [e for i, e in enumerate(scrubTargets) if e <= len(fdts) - 1]
    # Convert to a set again
    # TODO: is this necessary? Duplicates already removed above
    scrubTargets = set(scrubTargets)
    # Create a vector of 0s representing points not to scrub
    scrubVect = [0] * len(fdts)
    # Populate the 0 vector with 1s representing scrub targets
    scrubVect = [1 if i in scrubTargets else 0 for i, e in enumerate(scrubVect)]

    # Ensure fd_config number of consecutive points
    if fd_contig > 0:
        target = [0] * fd_contig
        contigSets = find_sub_list(target, scrubVect)
        scrubVectTemp = [1] * len(fdts)
        for conSet in contigSets:
            scrubVectTemp[conSet[0] : conSet[1]] = target
        scrubVect = scrubVectTemp
    return scrubVect


def get_scrub_vector_node(confounds_file, scrub_configs):
    """Wrapper for call to get_scrub_vector, but includes extracting column"""
    import pandas as pd
    from clpipe.postprocutils.utils import get_scrub_vector

    # Get the column to be used for thresholding
    confounds_df = pd.read_csv(confounds_file, sep="\t")
    target_timeseries = confounds_df[scrub_configs["TargetVariable"]]

    scrub_vector = get_scrub_vector(
        target_timeseries,
        scrub_configs["Threshold"],
        scrub_configs["ScrubBehind"],
        scrub_configs["ScrubAhead"],
        scrub_configs["ScrubContiguous"],
    )
    return scrub_vector


def get_scrub_targets(scrub_vector: list):
    """Given a scrubbing vector of 1s and 0s, convert this into a list of indexes."""

    return [i for i, e in enumerate(scrub_vector) if e == 1]


def scrub_data(data, fdts):
    import numpy

    scrubTargets = get_scrub_targets(fdts)
    data[scrubTargets, :] = numpy.nan
    return data


def scrub_image(nii_file, scrub_vector, insert_na=True, export_path=None):
    """Scrub the targets from the given image."""
    import nibabel as nib
    import numpy as np
    from pathlib import Path

    from clpipe.postprocutils.utils import get_scrub_targets

    image = nib.load(nii_file)
    data = image.get_fdata()
    affine = image.affine
    orig_shape = data.shape

    # Reorganize the data to be 2D with time on X
    data = data.reshape((np.prod(np.shape(data)[:-1]), data.shape[-1]))
    data = np.transpose(data)

    # Get the scrub indexes
    scrub_targets = get_scrub_targets(scrub_vector)
    if insert_na:
        # Replace scrub targets with NA
        data[scrub_targets, :] = np.nan
        new_shape = orig_shape
    else:
        # Remove the scrub targets
        data = np.delete(data, scrub_targets, axis=0)
        new_shape = (
            orig_shape[0],
            orig_shape[1],
            orig_shape[2],
            orig_shape[3] - len(scrub_targets),
        )

    # Swap the data back to original format
    data = np.transpose(data)
    data = data.reshape(new_shape)

    if export_path is None:
        # Crude way to figure out .nii vs .nii.gz
        path_stem = Path(nii_file).stem
        if path_stem[-4:] == ".nii":
            path_stem = Path(path_stem).stem
            out_path = Path(path_stem + "_scrubbed.nii.gz")
        else:
            out_path = Path(path_stem + "_scrubbed.nii")
        out_path = str(out_path.absolute())
    else:
        out_path = export_path

    out_image = nib.Nifti1Image(data, affine)
    nib.save(out_image, out_path)

    return out_path


def calc_filter(hp, lp, tr, order):
    from scipy.signal import butter

    nyq = 1 / (tr * 2)
    l = lp / nyq
    h = hp / nyq

    if l > 0 >= h:
        sos = butter(order, l, analog=False, btype="lowpass", output="sos")
    if l <= 0 < h:
        sos = butter(order, h, analog=False, btype="highpass", output="sos")
    if l > 0 and h > 0:
        sos = butter(order, [h, l], analog=False, btype="bandpass", output="sos")
    if l <= 0 and h <= 0:
        sos = "none"
    return sos


def apply_filter(sos, arr):
    from scipy.signal import sosfilt

    if sos is "none":
        return arr
    else:
        toReturn = sosfilt(sos, arr, axis=0)
        return toReturn


def regress(pred, target):
    import numpy

    A = numpy.linalg.pinv(pred)
    logging.info(str(A.shape))
    beta = numpy.matmul(A, target)
    predVal = numpy.matmul(pred, beta)
    toReturn = target - predVal
    return toReturn


def notch_filter(motion_params, band, tr):
    from scipy.signal import iirnotch, filtfilt
    import numpy

    logging.basicConfig(level=logging.INFO)
    logging.info("Using Respiratory Notch Filter at " + str(band) + " frequencies.")
    fs = 1 / tr
    if band[1] > fs / 2:
        logging.info("Respiratory band is above Nyquist frequency of acquisition")
        logging.info("Original band: " + str(band))
        band[1] = abs(((band[1] + fs / 2) % fs) - fs / 2)
        band[0] = abs(((band[0] + fs / 2) % fs) - fs / 2)
        band.sort()
        logging.info("Aliased band: " + str(band))
    mid = (band[1] + band[0]) / 2
    bw = band[1] - band[0]
    Q = mid / bw
    filter = iirnotch(mid, Q, fs=fs)
    filt_motion_params = filtfilt(filter[0], filter[1], motion_params, axis=0)
    diffs = numpy.diff(filt_motion_params, axis=0)
    diffs[:, 3:6] = diffs[:, 3:6] * 50
    filt_fd = numpy.sum(abs(diffs), axis=1)
    filt_fd = numpy.pad(filt_fd, (1, 0), mode="constant", constant_values=[numpy.nan])
    return filt_fd


def draw_graph(
    wf: pe.Workflow,
    graph_name: str,
    out_dir: Path,
    graph_style: str = DEFAULT_GRAPH_STYLE,
    logger: logging.Logger = None,
):
    graph_image_path = out_dir / f"{graph_name}.dot"
    if logger:
        logger.info(f"Drawing confounds workflow graph: {graph_image_path}")

        wf.write_graph(dotfilename=graph_image_path, graph2use=graph_style)


def plot_image_sample(
    image_path: os.PathLike,
    title: str = "image_sample.png",
    display_mode: str = "mosaic",
):
    """Plots a sample volume from the midpoint of the given 4D image
    to allow quick
    visual inspection of the fidelity of processing results.

    Args:
        image_path (os.PathLike): Path to the 4D image to plot.
        title (str, optional): The title for the plot.
              Defaults to "image_sample.png".
        display_mode (str, optional): Method for displaying the plot.
              Defaults to "mosaic".
    """

    # main_image = load_img(image_path)

    # # Grab a slice from the midpoint
    # image_slice = index_img(
    #   main_image, int(main_image.shape[IMAGE_TIME_DIMENSION_INDEX] / 2))

    # # Create a save path in the same directory as the image_path
    # output_path = Path(image_path).parent / title

    plotting.plot_epi(
        image_slice, title=title, output_file=output_path, display_mode=display_mode
    )


def nii_to_matrix(nii_file, save_df=False):
    """Transform a .nii file to a 2D, time by (x, y, z) matrix."""
    import numpy as np
    import nibabel as nib
    from pathlib import Path

    nii_img = nib.load(nii_file)
    img_data = nii_img.get_fdata()
    orig_shape = nii_img.shape
    affine = nii_img.affine

    # data = data.astype(np.float32)

    # Transform the data to time by (x, y z), a 2d array
    img_2d_matrix = img_data.reshape(
        (np.prod(np.shape(img_data)[:-1]), img_data.shape[-1])
    )
    img_2d_matrix_transposed = np.transpose(img_2d_matrix)

    if save_df:
        import pandas as pd

        # Build the output path
        nii_file = Path(nii_file)
        path_stem = nii_file.stem
        tsv_file = Path(path_stem + ".tsv")
        tsv_file = str(tsv_file.absolute())
        img_df = pd.DataFrame(img_2d_matrix_transposed)
        img_df.to_csv(tsv_file, sep="\t", header=None, index=False)

    return img_2d_matrix_transposed, orig_shape, affine


def matrix_to_nii(matrix, orig_shape, affine):
    """Transform a a 2D, time by (x, y, z) matrix back to a .nii file."""
    import numpy as np
    import nibabel as nib

    data = np.transpose(matrix)
    data = data.reshape(orig_shape)
    # data32 = np.float32(data)
    out_image = nib.Nifti1Image(data, affine)

    return out_image

def expand_columns(tsv_file, column_names):
    import pandas as pd
    import fnmatch

    df = pd.read_csv(tsv_file, sep="\t")
    column_list = df.columns

    # Change to file handle
    # column_list = timeseries[0]
    expanded_columns = []
    for pattern in column_names:
        matching_columns = []
        if "*" in pattern:
            matching_columns = fnmatch.filter(column_list, pattern)
        elif pattern in column_list:
            matching_columns = [pattern]
        else:
            # TODO: Raising warning -
            # Import logger and hook into nypipe logging
            pass
        expanded_columns.extend(matching_columns)
    return [*set(expanded_columns)]  # Removes duplicates from list

def vector_to_txt(vector):
    """Convert an input vector to a txt file."""
    from pathlib import Path

    fname = Path("vector.txt")

    f = open(fname, "w")
    for x in vector:
        f.write(f"{x}\n")
    f.close()

    return str(fname.resolve())
