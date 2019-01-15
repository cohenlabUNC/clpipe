# clpipe
Python pipeline for neuroimaging data

This pipeline is under development, and should not be used quite yet. If you are interested in contributing, please get in contact with Teague Henry (trhenry@email.unc.edu)


## Installation Guide for UNC-CH

1. Open a longleaf terminal session
2. Switch to python 3.6.6 using `module add python/3.6.6`
3. Install clpipe from GitHub with 
```pip3 install --user --upgrade pip3 install --user --upgrade  git+git://github.com/CohenLabUNC/clpipe.git```

All necessary dependencies should install to your local Python library, and the console commands should be immediately useable.

## Example Console Command

Eventually all documentation will be on readthedocs, but for now, here is an example of a console command that will print out the batch commands for running FMRIprep on a BIDS dataset.

```fmriprep_process -bidsDir <your/data/set> -workingDir <your/working/directory> -outputdir <your/output/directory>```

To submit all batch commands to Longleaf, use the `-submit` flag:

```fmriprep_process -bidsDir <your/data/set> -workingDir <your/working/directory> -outputdir <your/output/directory> -submit```

To preprocess only a subset of subjects, you can add their subject IDs to the end of the command:

```fmriprep_process -bidsDir <your/data/set> -workingDir <your/working/directory> -outputdir <your/output/directory> -submit some_sub_ID another_sub_ID```

To change the configuration file use the `-configFile` option:

```fmriprep_process -configFile <another.config.file> -bidsDir <your/data/set> -workingDir <your/working/directory> -outputdir <your/output/directory> -submit some_sub_ID another_sub_ID```

## Configuration Files

The core of the clpipe framework is the configuration file. These are JSON files that specify every aspect of preprocessing. They also contain log information from previous runs of a configuration file on a specific dataset. This can be used to track additional subjects being processed. Logs will not capture changes in a processing pipeline. Instead, changes in the processing pipeline need to be reflected in different output folders. Checks for this have not been implemented yet, but are on the todo. Here is an example of a configuration file.

```
{"ConfigTitle": "A Configuration File",
 "FMRIPrepPath": "SomeFMRIPREP.simg",
 "NuisanceRegression": "QuadLagged",
 "FilteringHighPass": 0.08,
 "FilteringLowPass": 0.1,
 "FilteringOrder": 12,
 "Scrubbing": "Scrub",
 "ScrubAhead": 2,
 "ScrubBehind": 2,
 "ScrubContig": 4,
 "SpatialSmoothing": "SUSAN",
 "RunLog": [{"DateRan": "12:43PM on January 15, 2019", "Subjects": "ALL", "WhatRan": "FMRIprep"}], 
 "BatchConfig": "slurmUNCConfig.json",
 "BIDSDirectory": "C:\\Users\\teagu\\Documents\\GitHub\\clpipe\\clpipe\\testBIDS",
 "WorkingDirectory": "C:\\Users\\teagu\\Documents\\GitHub\\clpipe\\working",
 "OutputDirectory": "C:\\Users\\teagu\\Documents\\GitHub\\clpipe\\output"}
```

Configuration JSONs are validated against a schema. On the TODO is a command line configuration validator
