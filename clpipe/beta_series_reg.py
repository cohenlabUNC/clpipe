import argparse
import os
import sys
import glob
import pandas
import numpy
import nipy.modalities.fmri.hrf
import matplotlib.pyplot as plt
from nipy import load_image
from subprocess import call
from nipy.core.image.image import Image
from nipy import save_image
import scipy.stats
from scipy.ndimage import convolve1d
from scipy.sparse import spdiags
from scipy.linalg import toeplitz


pandas.options.mode.chained_assignment = None
parser = argparse.ArgumentParser(prog="betaSeriesReg")
parser.add_argument(
    "input_BIDS",
    help="target BIDS dataset that has derivatives and fmriprep preprocessed files present",
)
parser.add_argument("task_name", help="task name to analyze.")
parser.add_argument("TR", help="TR in seconds of targetted scans")
parser.add_argument(
    "-targetsuffix",
    help="target image file suffix. Defaults to Asym_preproc.nii.gz",
    default="Asym_preproc.nii.gz",
)
parser.add_argument(
    "-session", help="session to analyze. (0 analyzes all sessions)", default=0
)
parser.add_argument("-subject", help="subject to analyze.")
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-aC",
    "--aCompCor",
    help="regress out aCompCor (NOTE: By default this supersedes all other nuisance regression (except GSR), see --override)",
    action="store_true",
)
group.add_argument(
    "-tC",
    "--tCompCor",
    help="regress out tCompCor (NOTE: By default this supersedes all other nuisance regression (except GSR), see --override)",
    action="store_true",
)
group.add_argument(
    "-ica",
    "--ICA_AROMA",
    help="regress out ICA-AROMA components (NOTE: By default this supersedes all other nuisance regression (except GSR), see --override)",
    action="store_true",
)

parser.add_argument(
    "--p_reg",
    help="which regression approach you would like to use, options are base, quad, lagged, and quadlagged",
    choices=["base", "quad", "lagged", "quadlagged"],
    default="quadlagged",
)
parser.add_argument(
    "--mot",
    help="don't include 6 parameters of motion in regression?",
    action="store_false",
)
parser.add_argument(
    "--wm", help="don't include white matter in regression?", action="store_false"
)
parser.add_argument(
    "--csf",
    help="don't include cerebro-spinal fluid in regression?",
    action="store_false",
)
parser.add_argument(
    "--gsr", help="include global signal in regression?", action="store_true"
)

parser.add_argument(
    "--nodatacheck",
    help="if option is included, will not inform user how many datasets are about to be processed, and will not require final confirmation",
    action="store_true",
)
parser.add_argument(
    "--noregcheck",
    help="if option is included, will not inform user what regression/method is used, and will not require final confirmation",
    action="store_true",
)

parser.add_argument(
    "--override",
    help="EXPERIMENTAL: combine component and nuisance regression",
    action="store_true",
)
parser.add_argument(
    "--overwrite",
    help="allow for overwriting regressor matrices and output nii.gz",
    action="store_true",
)
parser.add_argument(
    "--suffix",
    help="what suffix will be appended to denote new regressor matrix and output nii.gz (default: nuisReg)",
    default="nuisReg",
)
parser.add_argument(
    "--log_dir",
    help="log file directory name within derivatives, will create a directory if directory doesn't exist (default: nuisRegLog)",
    default="nuisRegLog",
)
parser.add_argument(
    "-q",
    "--quiet",
    help="do NOT print activity to console, activity will still be recorded in log file",
    action="store_true",
)
args = parser.parse_args()

targetdirs = args.input_BIDS + "/derivatives/fmriprep"
print(targetdirs)
if not os.path.isdir(targetdirs):
    print(
        "fmriprep directory is not present in the BIDS/derivatives directory. Have you run fmriprep? Ending function..."
    )
    sys.exit()

files = glob.glob(targetdirs + "/**/*.nii.gz", recursive=True)

targets = [i for i in files if "bold" in i]
targets = [i for i in targets if args.targetsuffix in i]
targets = [i for i in targets if "task-" + args.task_name + "_" in i]
if args.session is not 0:
    targets = [i for i in targets if "ses-" + args.session + "_" in i]
if args.subject is not None:
    targets = [i for i in targets if "sub-" + args.subject + "_" in i]

subs = [i.split("/") for i in targets]
subList = []
for file in subs:
    subtarget = [i for i in file if "sub-" in i]
    subList.extend([subtarget[0]])
uniqueSubs = set(subList)
import collections

counter = collections.Counter(subList).values()
minNum = min(counter)
maxNum = max(counter)
dataDesc = (
    "This data set contains "
    + str(len(uniqueSubs))
    + " subjects with at max "
    + str(maxNum)
    + " and at minimum "
    + str(minNum)
    + " functional scans. Does this look correct?"
)

fileNameList = []
for file in subs:
    fileName = file[len(file) - 1]
    fileNameList.extend([fileName])

onsetfiles = glob.glob(args.input_BIDS + "/**/*_events.tsv", recursive=True)
onsetfiles = [i for i in onsetfiles if "task-" + args.task_name + "_" in i]
if args.session is not 0:
    onsetfiles = [i for i in onsetfiles if "ses-" + args.session + "_" in i]
if args.subject is not None:
    onsetfiles = [i for i in onsetfiles if "sub-" + args.subject + "_" in i]
fileNameList = [i.split("bold")[0] for i in fileNameList]
fileNameList = [i + "events.tsv" for i in fileNameList]

targetOnsetList = []
for file in fileNameList:
    indexSet = []
    for i, j in enumerate(onsetfiles):
        if file in j:
            indexSet.extend([i])
    if len(indexSet) is not 1:
        targetOnsetList.extend(["NotFound"])
    else:
        targetOnsetList.extend([onsetfiles[indexSet[0]]])

onsetcounter = [1 if i is not "NotFound" else 0 for i in targetOnsetList]
proportion = sum(onsetcounter) / len(fileNameList) * 100

dataDesc = (
    "This data set contains "
    + str(len(uniqueSubs))
    + " subjects with at max "
    + str(maxNum)
    + " and at minimum "
    + str(minNum)
    + " functional scans with specified task and session. "
    + str(proportion)
    + " have onset files. Does this look correct?"
)
if not args.nodatacheck:
    print(dataDesc)
    while True:
        userinput = input("y/n: ")
        if userinput == "n":
            print("Ending this script. Please check your dataset and try again.")
            sys.exit()
        if userinput != "y" and userinput != "n":
            continue
        else:
            break

regParamLabels = []

paramCounter = 0
types = ""
if args.mot:
    paramCounter = 6
    types = types + " the 6 parameters of motion"
    regParamLabels.extend(["X", "Y", "Z", "RotX", "RotY", "RotZ"])
if args.csf:
    paramCounter = paramCounter + 1
    types = types + " CSF signal"
    regParamLabels.extend(["CSF"])
if args.wm:
    paramCounter = paramCounter + 1
    types = types + " WM signal"
    regParamLabels.extend(["WhiteMatter"])
if args.gsr:
    paramCounter = paramCounter + 1
    types = types + " GSR"
    regParamLabels.extend(["GlobalSignal"])

if args.p_reg == "quadlagged":
    factor = 4
    desc = (
        "and contains main effects, quadratic and temporal derivatives (lag-1 differences) and squares of the derivatives of "
        + types
        + ". "
    )
if args.p_reg == "lagged":
    factor = 2
    desc = (
        "and contains main effects and temporal derivatives (lag-1 differences) of "
        + types
        + ". "
    )
if args.p_reg == "quad":
    factor = 2
    desc = "and contains main effects and quadratic effects of " + types + ". "
if args.p_reg == "base":
    factor = 1
    desc = "and contains main effects of " + types + ". "

pnum = paramCounter * factor
regNums = (
    "The nuisance regression has " + str(pnum) + " parameters (plus overall intercept) "
)
regDesc = regNums + desc

scrub = ""

compLabels = []
if args.aCompCor:
    responses = "You have chosen to regress out aCompCor components. "
if args.tCompCor:
    responses = "You have chosen to regress out tCompCor components. "
if args.ICA_AROMA:
    responses = "You have chosen to regress out ICA-AROMA components. "

printout = ""
gsrWarning = "No GSR is being performed. "
if args.gsr:
    gsrWarning = "WARNING: GSR is being performed. "
if args.aCompCor or args.tCompCor or args.ICA_AROMA:
    printout = printout + responses
    if args.override:
        overrid = "WARNING: You have chosen to perform full nuisance regression in addition to a component approach. "
        printout = (
            printout + overrid + regDesc + scrub + gsrWarning + " Is this correct?"
        )
        if not args.noregcheck:
            print(printout)
            while True:
                userinput = input("y/n: ")
                if userinput == "n":
                    print(
                        "Ending this script. Please check your options and try again."
                    )
                    sys.exit()
                if userinput != "y" and userinput != "n":
                    continue
                else:
                    break
    else:
        printout = printout + scrub + gsrWarning + " Is this correct?"
        if not args.noregcheck:
            print(printout)
            while True:
                userinput = input("y/n: ")
                if userinput == "n":
                    print(
                        "Ending this script. Please check your options and try again."
                    )
                    sys.exit()
                if userinput != "y" and userinput != "n":
                    continue
                else:
                    break
else:
    printout = printout + regDesc + scrub + gsrWarning + " Is this correct?"
    if not args.noregcheck:
        print(printout)
        while True:
            userinput = input("y/n: ")
            if userinput == "n":
                print("Ending this script. Please check your options and try again.")
                sys.exit()
            if userinput != "y" and userinput != "n":
                continue
            else:
                break
# END OF PREPARATION SECTION

print("\nSacrifice is ready. Beginning confound removal.")

if not os.path.exists(args.input_BIDS + "/derivatives/" + args.log_dir):
    os.makedirs(args.input_BIDS + "/derivatives/" + args.log_dir)
from datetime import datetime

time = str(datetime.now())


print(targets)
print(targetOnsetList)

for i in targets:
    indexTarget = targets.index(i)
    print(i)
    print(targetOnsetList[indexTarget] + "\n")

logFile = open(
    args.input_BIDS
    + "/derivatives/"
    + args.log_dir
    + "/"
    + time
    + "_"
    + args.suffix
    + ".txt",
    "w+",
)
logFile.write("Log file for " + args.suffix + " suffixed run at " + time + "\n\n")
logFile.write(dataDesc + "\n\n")
logFile.write(printout + "\n\n")
logFile.write("Begin Processing Log" + "\n")

for i in targets:
    indexTarget = targets.index(i)
    if not args.quiet:
        print("Finding nuisance regressor file for " + i)
    # logFile.write("Finding nuisance regressor file for " + i + "\n")
    bits = i.split("_")
    comTarget = bits.index("bold") + 1
    bits = bits[0:(comTarget)]
    targetRegs = "_".join(bits) + "_confounds.tsv"
    compLabels = []
    if not os.path.exists(targetRegs):
        if not args.quiet:
            print("Did not find confound file for" + i)
        # logFile.write("Did not find confound file for " + i + "\n")
    else:
        if not args.quiet:
            print("Found confound file for" + i + ", " + targetRegs)
        # logFile.write("Found confound file for" + i+", "+ targetRegs + "\n")
        confounds = pandas.read_table(targetRegs, dtype="float", na_values="n/a")
        if args.aCompCor or args.tCompCor or args.ICA_AROMA:
            if args.aCompCor:
                targetCompLabels = [
                    col for col in confounds.columns if "aCompCor" in col
                ]
                compLabels.extend(targetCompLabels)
            if args.tCompCor:
                targetCompLabels = [
                    col for col in confounds.columns if "tCompCor" in col
                ]
                compLabels.extend(targetCompLabels)
            if args.ICA_AROMA:
                targetCompLabels = [
                    col for col in confounds.columns if "AROMAAggrComp" in col
                ]
                compLabels.extend(targetCompLabels)
            if args.override:
                targetConfounds = confounds[regParamLabels]
                if args.p_reg == "lagged":
                    targetConfoundsLagged = targetConfounds.diff()
                    targetConfounds = pandas.concat(
                        [targetConfounds, targetConfoundsLagged], axis=1
                    )
                    targetConfounds["intercept"] = 1
                if args.p_reg == "quad":
                    targetConfoundsQuad = targetConfounds.pow(2)
                    targetConfounds = pandas.concat(
                        [targetConfounds, targetConfoundsQuad], axis=1
                    )
                    targetConfounds["intercept"] = 1
                if args.p_reg == "quadlagged":
                    targetConfoundsLagged = targetConfounds.diff()
                    targetConfounds = pandas.concat(
                        [targetConfounds, targetConfoundsLagged], axis=1
                    )
                    targetConfoundsQuad = targetConfounds.pow(2)
                    targetConfounds = pandas.concat(
                        [targetConfounds, targetConfoundsQuad], axis=1
                    )
                    targetConfounds["intercept"] = 1
                targetCompConfounds = confounds[compLabels]
                targetConfounds = pandas.concat(
                    [targetConfounds, targetCompConfounds], axis=1
                )
            else:
                targetConfounds = confounds[compLabels]
                targetConfounds["intercept"] = 1
                if args.gsr:
                    pandas.concat([targetConfounds, confounds["GlobalSignal"]], axis=1)
        else:
            targetConfounds = confounds[regParamLabels]
            if args.p_reg == "lagged":
                targetConfoundsLagged = targetConfounds.diff()
                targetConfounds = pandas.concat(
                    [targetConfounds, targetConfoundsLagged], axis=1
                )
                targetConfounds["intercept"] = 1
            if args.p_reg == "quad":
                targetConfoundsQuad = targetConfounds.pow(2)
                targetConfounds = pandas.concat(
                    [targetConfounds, targetConfoundsQuad], axis=1
                )
                targetConfounds["intercept"] = 1
            if args.p_reg == "quadlagged":
                targetConfoundsLagged = targetConfounds.diff()
                targetConfounds = pandas.concat(
                    [targetConfounds, targetConfoundsLagged], axis=1
                )
                targetConfoundsQuad = targetConfounds.pow(2)
                targetConfounds = pandas.concat(
                    [targetConfounds, targetConfoundsQuad], axis=1
                )
                targetConfounds["intercept"] = 1
        targetConfounds = targetConfounds.fillna(0)
        onsetData = pandas.read_table(targetOnsetList[indexTarget], na_values="n/a")

        if onsetData.shape[0] is not 0:
            # Preparing the Onset Time Points in accordance to Mumford's original script
            # TODO: Add in code to remove particular types of stimuli from the analysis.
            TR = float(args.TR)
            ntp = len(targetConfounds)
            time_res = TR / 16.0
            timeCourse = numpy.arange(0, 32 + TR / 16.0, (TR / 16.0))
            time_up = numpy.arange(0, TR * ntp, TR / 16.0)
            n_up = len(time_up)
            hrf = nipy.modalities.fmri.hrf.spm_hrf_compat(timeCourse)
            eventArray = numpy.zeros((len(targetConfounds), len(onsetData)))
            indexSample = numpy.arange(0, TR * ntp / (TR / 16.0), TR / (TR / 16.0))
            indexSample = indexSample.astype("int")

            sigN2 = ((100 / TR) / (numpy.sqrt(2.0))) ** 2.0
            K = toeplitz(
                1
                / numpy.sqrt(2.0 * numpy.pi * sigN2)
                * numpy.exp((-1 * numpy.array(range(ntp)) ** 2.0 / (2 * sigN2)))
            )
            K = spdiags(1.0 / numpy.sum(K.T, 0).T, 0, ntp, ntp) * K
            H = numpy.zeros((ntp, ntp))  # Smoothing matrix, s.t. H*y is smooth line
            X = numpy.hstack(
                (numpy.ones((ntp, 1)), numpy.arange(1, ntp + 1).T[:, numpy.newaxis])
            )
            for k in range(ntp):
                W = numpy.diag(K[k, :])
                Hat = numpy.dot(numpy.dot(X, numpy.linalg.pinv(numpy.dot(W, X))), W)
                H[k, :] = Hat[k, :]

            F = numpy.eye(ntp) - H

            for index, row in onsetData.iterrows():
                ev_loop = numpy.zeros(n_up)
                index1 = numpy.logical_and(
                    (time_up >= row["onset"]),
                    (time_up <= row["onset"] + row["duration"]),
                )
                ev_loop[index1] = 1
                ev_loop = numpy.convolve(ev_loop, hrf)
                ev_loop = ev_loop[: -(len(hrf) - 1)]
                ev_loop = ev_loop[indexSample]
                eventArray[:, index] = ev_loop
            image = load_image(i)
            data = image.get_data()
            orgImageShape = data.shape[:-1]
            coordMap = image.coordmap
            data = data.reshape((numpy.prod(numpy.shape(data)[:-1]), data.shape[-1]))
            data = numpy.transpose(data)

            data = data - data.mean(axis=0)
            data = numpy.nan_to_num(data)
            data = numpy.dot(F, data)
            bits2 = i.split(args.targetsuffix)
            nonniibit = args.targetsuffix.split(".nii.gz")[0]
            outputFile = bits2[0] + nonniibit + "_" + args.suffix + ".nii.gz"
            betaDim = orgImageShape + (eventArray.shape[1],)
            betas = numpy.zeros(betaDim)
            for trial in numpy.arange(0, eventArray.shape[1]):
                print(trial)
                regressor = numpy.transpose(
                    numpy.stack(
                        [
                            eventArray[:, trial],
                            eventArray.sum(axis=1) - eventArray[:, trial],
                        ],
                        0,
                    )
                )
                regressor = numpy.concatenate((regressor, targetConfounds), 1)
                regressor = numpy.dot(F, regressor)
                A = numpy.linalg.pinv(regressor)
                beta = (numpy.matmul(A, data))[0, :]
                beta[abs(beta) < 0.00000000000001] = 0
                beta = beta.reshape(orgImageShape)
                betas[:, :, :, trial] = beta
            betaImage = Image(betas, coordMap)
            outputFile = targetRegs = "_".join(bits) + "_betaSeries.nii.gz"
            save_image(betaImage, outputFile)
        else:
            print("Onset File has no events? Skipping")
