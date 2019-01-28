import argparse
import os
import sys
import glob
import pandas
import numpy
from nipy import load_image
from subprocess import call
from nipy.core.image.image import Image
from nipy import save_image
import utils as utils
import spec_interpolate as spec_interpolate

pandas.options.mode.chained_assignment = None
parser = argparse.ArgumentParser(prog="filtReg")
parser.add_argument("input_BIDS", help="target BIDS dataset that has derivatives and fmriprep preprocessed files present")
parser.add_argument("TR", help = "TR in seconds of targetted scans")
parser.add_argument("-targetsuffix", help="target image file suffix. Defaults to Asym_preproc.nii.gz", default = "Asym_preproc.nii.gz")
parser.add_argument("-task", help = "task to perform confound regression and filtering (default = rest)", default = "rest")
parser.add_argument("-session", help="session to analyze. (0 analyzes all sessions)", default = 0)
parser.add_argument("-subject", help= "subjects to analyze.", default = None)

parser.add_argument("-lp", "--lowpass", help = "frequency in Hz for lowpass filter (default = no filter)", default = "-1")
parser.add_argument("-hp", "--highpass", help = "frequency in Hz for highpass filter (default = no filter)", default = "-1")
parser.add_argument("-o", "--order", help = "order of filter, for sharper filter choose higher order. (default = 2)", default = "2")

parser.add_argument("-int_ofreq", help = "oversampling frequency for spectral interpolation, larger is smoother. Default = 4", default = "4")
parser.add_argument("-int_hifreq", help = "percent frequency to interpolate across. reduce to remove high frequency flucuations. Default = 1 (no removal of high frequency)", default = "1")

group = parser.add_mutually_exclusive_group()
group.add_argument("-aC", "--aCompCor",help="regress out aCompCor (NOTE: By default this supersedes all other nuisance regression (except GSR), see --override)", action="store_true")
group.add_argument("-tC", "--tCompCor",help="regress out tCompCor (NOTE: By default this supersedes all other nuisance regression (except GSR), see --override)", action="store_true")
group.add_argument("-ica", "--ICA_AROMA",help="regress out ICA-AROMA components (NOTE: By default this supersedes all other nuisance regression (except GSR), see --override)", action="store_true")

parser.add_argument("--p_reg", help="which regression approach you would like to use, options are base, quad, lagged, and quadlagged",
                    choices = ["base", "quad", "lagged", "quadlagged"], default="quadlagged")
parser.add_argument("--mot", help="don't include 6 parameters of motion in regression?", action="store_false")
parser.add_argument("--wm", help="don't include white matter in regression?", action="store_false")
parser.add_argument("--csf", help="don't include cerebro-spinal fluid in regression?", action="store_false")
parser.add_argument("--gsr", help="include global signal in regression?", action="store_true")
parser.add_argument("--no_means", help = "Do not add back in mean voxel level after all qc steps", action = "store_true")
parser.add_argument("--scrub", help = "what type of scrubbing? spike removes any  defaults to none", action = "store_true")
parser.add_argument("-fd_thres", help = "what FD threshold to perform scrubbing (defaults to .3)", default = ".3")

parser.add_argument("-scrub_ahead", help = "how many timepoints ahead of bad frame to remove? Defaults to 1", default = "1")
parser.add_argument("-scrub_behind", help = "how many timepoints behind of bad frame to remove? Defaults to 1", default = "1")
parser.add_argument("-scrub_contig", help = "how many temporally contingous timepoints are required? Defaults to 3", default = "3")

parser.add_argument("--nodatacheck", help="if option is included, will not inform user how many datasets are about to be processed, and will not require final confirmation", action = "store_true")
parser.add_argument("--noregcheck", help="if option is included, will not inform user what regression/method is used, and will not require final confirmation", action = "store_true")

parser.add_argument("--override", help="EXPERIMENTAL: combine component and nuisance regression", action="store_true")
parser.add_argument("--overwrite", help="allow for overwriting regressor matrices and output nii.gz", action="store_true")
parser.add_argument("--suffix", help="what suffix will be appended to output nii.gz (default: filtReg)", default = "filtReg")
parser.add_argument("--log_dir", help="log file directory name within derivatives, will create a directory if directory doesn't exist (default: nuisRegLog)", default = "nuisRegLog")
parser.add_argument("-q","--quiet", help="do NOT print activity to console, activity will still be recorded in log file", action = "store_true")
parser.add_argument("-batch", help = "Run in batch mode, automatically submits each subject as a separate job.", action = "store_true")

argstring = sys.argv
print(argstring)
args = parser.parse_args()

print(args)

targetdirs = args.input_BIDS +"/derivatives/fmriprep"
print(targetdirs)
if not os.path.isdir(targetdirs):
    print("fmriprep directory is not present in the BIDS/derivatives directory. Have you run fmriprep? Ending function...")
    sys.exit()

files = glob.glob(targetdirs+"/**/*.nii.gz", recursive = True)

targets = [i for i in files if "bold" in i]
targets = [i for i in targets if args.targetsuffix in i]
targets = [i for i in targets if "task-"+args.task +"_" in i]
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
dataDesc = "This data set contains " + str(len(uniqueSubs)) + " subjects with at max " +          str(maxNum) +" and at minimum " + str(minNum) +" functional scans. Does this look correct?"

fileNameList = []
for file in subs:
    fileName = file[len(file)-1]
    fileNameList.extend([fileName])


dataDesc = "This data set contains " + str(len(uniqueSubs)) + " subjects with at max " + str(maxNum) +" and at minimum " + str(minNum) +\
           " functional scans with specified task and session. "+" Does this look correct?"
if not args.nodatacheck:
    print(dataDesc)
    while True:
        userinput = input("y/n: ")
        if userinput == "n":
            print("Ending this script. Please check your dataset and try again.")
            sys.exit()
        if userinput != "y" and userinput !="n":
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
    paramCounter = paramCounter+1
    types = types + " CSF signal"
    regParamLabels.extend(["CSF"])
if args.wm:
    paramCounter = paramCounter+1
    types = types + " WM signal"
    regParamLabels.extend(["WhiteMatter"])
if args.gsr:
    paramCounter = paramCounter+1
    types = types + " GSR"
    regParamLabels.extend(["GlobalSignal"])

if args.p_reg == "quadlagged":
    factor = 4
    desc = "and contains main effects, quadratic and temporal derivatives (lag-1 differences) and squares of the derivatives of " +types +". "
if args.p_reg == "lagged":
    factor = 2
    desc = "and contains main effects and temporal derivatives (lag-1 differences) of " +types +". "
if args.p_reg == "quad":
    factor = 2
    desc = "and contains main effects and quadratic effects of " +types +". "
if args.p_reg == "base":
    factor = 1
    desc = "and contains main effects of " +types +". "

pnum = paramCounter*factor
regNums = "The nuisance regression has " +str(pnum) +" parameters (plus overall intercept) "
regDesc = regNums + desc

scrub=""

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
        printout = printout+overrid+regDesc+scrub + gsrWarning +" Is this correct?"
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
    else:
        printout = printout + scrub + gsrWarning + " Is this correct?"
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
else:
    printout = printout+regDesc+scrub +gsrWarning +" Is this correct?"
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
#END OF PREPARATION SECTION

print("\nSacrifice is ready. Beginning confound removal.")

if not os.path.exists(args.input_BIDS+"/derivatives/"+args.log_dir):
    os.makedirs(args.input_BIDS+"/derivatives/"+args.log_dir)
from datetime import datetime
time= str(datetime.now())

if args.batch and args.subject is None:
    for sub in uniqueSubs:
        argStringJoined = " ".join(argstring[1:])
        argStringNoBatch = argStringJoined.replace("-batch", "")
        command = "python3 /proj/hng/cohenlab/projects/fmripostprep/FiltReg.py " + argStringNoBatch + " -subject " +str(sub).split("-")[1] + " --nodatacheck --noregcheck"
        toSubmit = '''sbatch --ntasks=4 --time=8:00:00 --mem=30000 --wrap="{command}"'''.format(command = command)
        call(toSubmit, shell=True)
else:

    for i in targets:
        indexTarget = targets.index(i)
        print(i)

    logFile = open(args.input_BIDS+"/derivatives/"+args.log_dir+"/"+time+"_"+args.suffix+".txt","w+")
    logFile.write("Log file for "+ args.suffix +" suffixed run at " + time + "\n\n")
    logFile.write(dataDesc+"\n\n")
    logFile.write(printout+"\n\n")
    logFile.write("Begin Processing Log"+"\n")

    for i in targets:

        indexTarget = targets.index(i)
        if not args.quiet: print("Finding nuisance regressor file for " + i)
        bits = i.split("_")
        comTarget = bits.index("bold")+1
        bits = bits[0:(comTarget)]
        targetRegs = '_'.join(bits)+"_confounds.tsv"
        compLabels = []
        if not os.path.exists(targetRegs):
            if not args.quiet: print("Did not find confound file for" + i)
            #logFile.write("Did not find confound file for " + i + "\n")
        else:
            if not args.quiet: print("Found confound file for" + i+", "+ targetRegs)
            #logFile.write("Found confound file for" + i+", "+ targetRegs + "\n")
            confounds = pandas.read_table(targetRegs,dtype="float",na_values="n/a")
            confounds = confounds.fillna(0)
            if args.aCompCor or args.tCompCor or args.ICA_AROMA:
                if args.aCompCor:
                    targetCompLabels = [col for col in confounds.columns if 'aCompCor' in col]
                    compLabels.extend(targetCompLabels)
                if args.tCompCor:
                    targetCompLabels = [col for col in confounds.columns if 'tCompCor' in col]
                    compLabels.extend(targetCompLabels)
                if args.ICA_AROMA:
                    targetCompLabels = [col for col in confounds.columns if 'AROMAAggrComp' in col]
                    compLabels.extend(targetCompLabels)
                if args.override:
                    targetConfounds = confounds[regParamLabels]
                    if args.p_reg == "lagged":
                        targetConfoundsLagged = targetConfounds.diff()
                        targetConfounds = pandas.concat([targetConfounds,targetConfoundsLagged], axis=1)
                    if args.p_reg == "quad":
                        targetConfoundsQuad = targetConfounds.pow(2)
                        targetConfounds = pandas.concat([targetConfounds,targetConfoundsQuad], axis=1)
                    if args.p_reg == "quadlagged":
                        targetConfoundsLagged = targetConfounds.diff()
                        targetConfounds = pandas.concat([targetConfounds,targetConfoundsLagged], axis=1)
                        targetConfoundsQuad = targetConfounds.pow(2)
                        targetConfounds = pandas.concat([targetConfounds, targetConfoundsQuad], axis=1)
                    targetCompConfounds = confounds[compLabels]
                    targetConfounds = pandas.concat([targetConfounds,targetCompConfounds], axis=1)
                else:
                    targetConfounds = confounds[compLabels]
                    if args.gsr:
                        pandas.concat([targetConfounds,confounds["GlobalSignal"]], axis = 1)
            else:
                targetConfounds = confounds[regParamLabels]
                if args.p_reg == "lagged":
                    targetConfoundsLagged = targetConfounds.diff()
                    targetConfounds = pandas.concat([targetConfounds,targetConfoundsLagged], axis=1)
                if args.p_reg == "quad":
                    targetConfoundsQuad = targetConfounds.pow(2)
                    targetConfounds = pandas.concat([targetConfounds,targetConfoundsQuad], axis=1)
                if args.p_reg == "quadlagged":
                    targetConfoundsLagged = targetConfounds.diff()
                    targetConfounds= pandas.concat([targetConfounds,targetConfoundsLagged], axis=1)
                    targetConfoundsQuad = targetConfounds.pow(2)
                    targetConfounds = pandas.concat([targetConfounds,targetConfoundsQuad], axis=1)

            targetConfounds =targetConfounds.fillna(0)

            scrubToggle = False
            if args.scrub:
                scrubToggle = True
                scrub_ahead = int(args.scrub_ahead)
                scrub_behind = int(args.scrub_behind)
                scrub_contig = int(args.scrub_contig)
                fd_thres = float(args.fd_thres)
                fdts = confounds['FramewiseDisplacement']
                scrubTargets = utils.scrub_setup(fdts, fd_thres, scrub_behind, scrub_ahead, scrub_contig)

            tr = float(args.TR)
            lp = float(args.lowpass)
            hp = float(args.highpass)
            filterToggle = False
            if lp >0 or hp >0:
                print("Calculating Spectral Filter")
                filterToggle = True
                ord = int(args.order)
                filt = utils.calc_filter(hp, lp, tr, ord)
                filtConfounds = utils.apply_filter(filt, targetConfounds)


            image = load_image(i)
            data = image.get_data()
            orgImageShape = data.shape
            coordMap = image.coordmap
            data = data.reshape((numpy.prod(numpy.shape(data)[:-1]), data.shape[-1]))
            data = numpy.transpose(data)
            row_means = data.mean(axis=0)
            data = (data - data.mean(axis=0))


            if scrubToggle and filterToggle:
                print("Interpolating Scrubbed Values")
                ofreq = int(args.int_ofreq)
                hfreq = float(args.int_hifreq)
                data = spec_interpolate.spec_inter(data, tr, ofreq, scrubTargets, hfreq)
                print("Interpolation Complete")

            if filterToggle:
                print("Applying Spectral Filtering and Nuisance Regression")
                data = utils.apply_filter(filt, data)
                data = utils.regress(filtConfounds, data)
                print("Spectral Filtering and Nuisance Regression Complete")
            else:
                print("Applying Nuisance Regression")
                data = utils.regress(targetConfounds, data)
                print("Nuisance Regression Complete")

            if scrubToggle:
                data = utils.scrub_image(data, scrubTargets)

            if not args.no_means:
                data = (data + row_means)

            data = numpy.transpose(data)
            data = data.reshape(orgImageShape)
            outImage = Image(data, coordMap)
            outputFile = '_'.join(bits)+ "_"+args.suffix+".nii.gz"

            save_image(outImage,outputFile)
            if scrubToggle:
               toOut = numpy.vstack([numpy.arange(1, len(scrubTargets)+1, 1),numpy.asarray(scrubTargets)]).T
               numpy.savetxt('_'.join(bits)+ "_scrubTargets.csv", toOut,delimiter=",")




