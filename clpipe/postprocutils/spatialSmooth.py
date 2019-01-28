import argparse
import os
import sys
import glob
import pandas
from subprocess import call
pandas.options.mode.chained_assignment = None
parser = argparse.ArgumentParser(prog="Spatial Smoothing")
parser.add_argument("input_BIDS", help="target BIDS dataset that has derivatives and fmriprep preprocessed files present")
parser.add_argument("-targetsuffix", help="target image file suffix. Defaults to Asym_preproc.nii.gz", default = "Asym_preproc.nii.gz")

group = parser.add_mutually_exclusive_group()
group.add_argument("-fwhm" ,help="full width at half maximum for Gaussian Kernel in mm (default = 4mm)",default = 4.0)
group.add_argument("-sigma" ,help="alternative to FWHM, sigma for Gaussian Kernel in mm (fwhm = sigma*sqrt(8*ln(2))")

parser.add_argument("--nodatacheck", help="if option is included, will not inform user how many datasets are about to be processed, and will not require final confirmation", default=False)
parser.add_argument("--nosmoothcheck", help="if option is included, will not inform user what regression/method is used, and will not require final confirmation", default=False)
parser.add_argument("--overwrite", help="allow for overwriting regressor matrices and output nii.gz", action="store_true")
parser.add_argument("--suffix", help="what suffix will be appended to denote output nii.gz (default: spatSmooth)", default = "spatSmooth")
parser.add_argument("--log_dir", help="log file directory name within derivatives, will create a directory if directory doesn't exist (default: nuisRegLog)", default = "spatSmoothLog")
parser.add_argument("-q","--quiet", help="do NOT print activity to console, activity will still be recorded in log file", action = "store_true")
args = parser.parse_args()

targetdirs = args.input_BIDS +"/derivatives/fmriprep"

if not os.path.isdir(targetdirs):
    print("fmriprep directory is not present in the BIDS/derivatives directory. Have you run fmriprep? Ending function...")
    sys.exit()

files = glob.glob(targetdirs+"/**/*.nii.gz", recursive = True)

targets = [i for i in files if "bold" in i]
targets = [i for i in targets if args.targetsuffix in i]
targets = sorted(targets)
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
import math
sigma = None
if args.sigma is not None:
    sigma = args.sigma
    response = "You are performing spatial smoothing with sigma specified at " + str(
        sigma) + ". This corresponds with a FWHM of " + str(
        sigma * math.sqrt(8 * math.log(2))) + ". Does this look correct?"
    if not args.nosmoothcheck:
        print(response)
        while True:
            userinput = input("y/n: ")
            if userinput == "n":
                print("Ending this script. Please check your dataset and try again.")
                sys.exit()
            if userinput != "y" and userinput != "n":
                continue
            else:
                break
else:
    sigma = float(args.fwhm)/math.sqrt(8 * math.log(2))
    response = "You are performing spatial smoothing with FWHM specified at " + str(args.fwhm) +\
        ". This corresponds with a sigma of " + str(sigma) + ". Does this look correct?"
    if not args.nosmoothcheck:
        print(response)
        while True:
            userinput = input("y/n: ")
            if userinput == "n":
                print("Ending this script. Please check your dataset and try again.")
                sys.exit()
            if userinput != "y" and userinput != "n":
                continue
            else:
                break

print("\nImpulse drive is engaged. Beginning Spatial Smoothing.")

if not os.path.exists(args.input_BIDS+"/derivatives/"+args.log_dir):
    os.makedirs(args.input_BIDS+"/derivatives/"+args.log_dir)
from datetime import datetime
time= str(datetime.now())

logFile = open(args.input_BIDS+"/derivatives/"+args.log_dir+"/"+time+"_"+args.suffix+".txt","w+")
logFile.write("Spatial Smoothing log file for "+ args.suffix +" suffixed run at " + time + "\n\n")
logFile.write(dataDesc+"\n\n")
logFile.write(response+"\n\n")
logFile.write("Begin Processing Log"+"\n")



for i in targets:

    bits2 = i.split(args.targetsuffix)
    nonniibit = args.targetsuffix.split(".nii.gz")[0]
    outputFile = bits2[0] + nonniibit + "_" + args.suffix + ".nii.gz"
    if os.path.exists(outputFile) and not args.overwrite:
        if not args.quiet: print("File " + outputFile +" already exists and --overwrite was not flagged. File will NOT be overwritten!")
        if not args.quiet: print("Due to a smoothed file existence, spatial smoothing was NOT performed on " +i)
        logFile.write("File " + outputFile +" already exists and --overwrite was not flagged. File will NOT be overwritten!\n")
        logFile.write("Due to a smoothed file existence, spatial smoothing was NOT performed on " + i + "\n\n")
    if os.path.exists(outputFile) and args.overwrite:
        if not args.quiet: print("File " + outputFile + " already exists and --overwrite was flagged. File will be overwritten!")
        logFile.write("File " + outputFile +" already exists and --overwrite was flagged. File will be overwritten!\n")
        fslCommand = "fslmaths " + i + " -kernel gauss " +str(sigma) + " " + outputFile
        if not args.quiet: print("Calling: "+fslCommand)
        logFile.write("Calling: "+fslCommand + "\n")
        return_code = call(fslCommand, shell=True)
        if not args.quiet: print("Completed spatial smoothing for " + i +"\n")
        logFile.write("Completed spatial smoothing for " + i + "\n\n")
    if not os.path.exists(outputFile):
        fslCommand = "fslmaths " + i + " -kernel gauss " + str(sigma) + " " + outputFile
        if not args.quiet: print("Calling: " + fslCommand)
        logFile.write("Calling: " + fslCommand + "\n")
        return_code = call(fslCommand, shell=True)
        logFile.write(str(return_code) + "\n")
        if not args.quiet: print("Completed spatial smoothing for "+ i +"\n")
        logFile.write("Completed spatial smoothing for "+ i + "\n\n")
logFile.close()
