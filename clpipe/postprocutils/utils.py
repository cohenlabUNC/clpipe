import pkg_resources
import sys
import getpass
sys.path.insert(0,"/nas/longleaf/home/"+getpass.getuser()+"/.local/lib/python3.6/site-packages")
import numpy
from scipy.signal import butter, sosfilt, iirnotch, filtfilt
import logging


def find_sub_list(sl, l):
    results = []
    sll = len(sl)
    for ind in (i for i, e in enumerate(l) if e == sl[0]):
        if l[ind:ind + sll] == sl:
            results.append((ind, ind + sll))

    return results


def scrub_setup(fdts, fd_thres=.3, fd_behind=1, fd_ahead=1, fd_contig=3):
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
            scrubVectTemp[conSet[0]:conSet[1]] = target
        scrubVect = scrubVectTemp
    return scrubVect


def scrub_image(data, fdts):
    scrubTargets = [i for i, e in enumerate(fdts) if e == 1]
    data[scrubTargets, :] = numpy.nan
    return data


def calc_filter(hp, lp, tr, order):
    nyq = 1 / (tr * 2)
    l = lp / nyq
    h = hp / nyq

    if l > 0 >= h:
        sos = butter(order, l, analog=False, btype='lowpass', output='sos')
    if l <= 0 < h:
        sos = butter(order, h, analog=False, btype='highpass', output='sos')
    if l > 0 and h > 0:
        sos = butter(order, [h, l], analog=False, btype='bandpass', output='sos')
    if l <= 0 and h <= 0:
        sos = "none"
    return sos


def apply_filter(sos, arr):
    if sos is "none":
        return arr
    else:
        toReturn = sosfilt(sos, arr, axis=0)
        return toReturn


def regress(pred, target):

    A = numpy.linalg.pinv(pred)
    logging.info(str(A.shape))
    beta = (numpy.matmul(A, target))
    predVal = numpy.matmul(pred, beta)
    toReturn = target - predVal
    return toReturn

def notch_filter(motion_params, band, tr):
    logging.basicConfig(level=logging.INFO)
    logging.info('Using Respiratory Notch Filter at ' + str(band) + ' frequencies.')
    fs = 1/tr
    if band[1] > fs/2:
        logging.info('Respiratory band is above Nyquist frequency of acquisition')
        logging.info('Original band: ' + str(band))
        band[1] = abs(((band[1] + fs/2) % fs) - fs/2)
        band[0] = abs(((band[0] + fs/2) % fs) - fs/2)
        band.sort()
        logging.info('Aliased band: ' + str(band))
    mid = (band[1]+band[0])/2
    bw = band[1]-band[0]
    Q = mid/bw
    filter = iirnotch(mid, Q, fs=fs)
    filt_motion_params = filtfilt(filter[0], filter[1], motion_params, axis=0)
    diffs = numpy.diff(filt_motion_params, axis = 0)
    diffs[:, 3:6] =diffs[:, 3:6]*50
    filt_fd = numpy.sum(abs(diffs), axis = 1)
    filt_fd = numpy.pad(filt_fd, (1,0), mode='constant', constant_values=[numpy.nan])
    return filt_fd


from pathlib import Path
def meta_config_search(start_path: Path):
    if start_path is None:
        start_path = Path.cwd()
    for path in start_path.iterdir():
        print(f"Searching: {path}")
        if path.name == ".clpipe":
            return path
    meta_config_search(start_path.parent())

