===============
BIDS Validation
===============

*****************
Overview
*****************

clpipe contains a convenience function to validate your datasets directly on the HPC. 
This function uses a Singularity image of the 
`BIDs Validator <https://github.com/bids-standard/bids-validator>`_.

BIDS Validate checks that the entire BIDS folder of your project is in the correct format for 
fMRIPrep to work successfully. fMRIPrep runs BIDS Validate automatically, but if there is an 
issue your job will fail and this will impact your Longleaf priority. Running BIDS Validate prior 
to launching fMRIPrep ensures that fMRIPrep will not fail for this reason.

The output of this command will appear in your `logs/bids_validation_logs` folder
by default. Within the outputted log file, sections that begin with [ERR] refer to errors, whereas [WARN] 
refer to warnings. Warnings are ignorable and would not interfere with fMRIprep.

Notably, fMRIPrep will refuse to run non-valid BIDS datasets, unless you turn the
option off. The same bids-validator outputs can be viewed in fMRIPrep's logs, but
you may find this stand-alone command more convenient.

*****************
Configuration
*****************

**Definitions**

.. autoclass:: clpipe.config.options.BIDSValidatorOptions

*****************
Command
*****************

.. click:: clpipe.cli:bids_validate_cli
   :prog: clpipe bids_validate
   :nested: full

*************************
BIDS validation example 1
*************************

Let’s say you acquire two runs of a resting state despite only expecting one. In this case, those 
resting state functional files in data_BIDS are appended with “run-01”, “run-02”, etc. To fix this,
you may choose to delete the first acquired resting state and rename the last resting state file to 
redcat the “run-02” portion of the file name.

If you run BIDS validation after this, you may see an error that looks like this:

.. code-block:: console

    ./sub-215/fmap/sub-215_dir-AP_epi.nii.gz
                    Evidence: func/sub-215_task-rest_run-01_bold.nii.gz
    ./sub-215/fmap/sub-215_dir-AP_epi.nii.gz
                    Evidence: func/sub-215_task-rest_run-02_bold.nii.gz
    ./sub-215/fmap/sub-215_dir-PA_epi.nii.gz
                    Evidence: func/sub-215_task-rest_run-01_bold.nii.gz
    ./sub-215/fmap/sub-215_dir-PA_epi.nii.gz
                    Evidence: func/sub-215_task-rest_run-02_bold.nii.gz


In this case, the “IntendedFor” field of your fieldmaps’ json file is still pointing toward the 
previous resting state files, which include “run-01” or “run-02” in the file name. Because these 
files do not exist, BIDS validation will print the error above.

To fix this, go to the fieldmap(s) of interest’s json files. Identify the “IntendedFor” field and edit 
the resting state’s name to match what exists in the func folder. After doing this, BIDS validation
should be successful.

*************************
BIDS validation example 2
*************************


Let’s say you change the subject folder of one of your participants from “sub-058” to “sub-
058_v1”. You may have done this to try some sort of change in the BIDS file that you want to 
compare to another version of this participant’s BIDS data; if you change the name of the subject
folder and rerun BIDS conversion on that person’s DICOMs, it would not recognize the folder 
“sub-058v1” and therefore would not overwrite the folder’s contents – it would create a new 
folder named “sub-058”.

If you run BIDS validation after this, you may see an error that looks like this:

.. code-block:: console

    31m1: [ERR] Files with such naming scheme are not part of BIDS specification. This error is 
    most commonly caused by typos in file names that make them not BIDS compatible. Please consult 
    the specification and make sure your files are named correctly. If this is not a file naming issue (for 
    example when including files not yet covered by the BIDS specification) you should include a 
    ".bidsignore" file in your dataset (see https://github.com/bids-standard/bids-validator#bidsignore for 
    details). Please note that derived (processed) data should be placed in /derivatives folder and source 
    data (such as DICOMS or behavioural logs in proprietary formats) should be placed in the /sourcedata 
    folder. (code: 1 - NOT_INCLUDED)39m
                                    ./sub-058v1/anat/sub-058_T1w.json
                                                    Evidence: sub-058_T1w.json
                                    ./sub-058v1/anat/sub-058_T1w.nii.gz
                                                    Evidence: sub-058_T1w.nii.gz
                                    ./sub-058v1/fmap/sub-058_dir-AP_epi.json
                                                    Evidence: sub-058_dir-AP_epi.json
                                    ./sub-058v1/fmap/sub-058_dir-AP_epi.nii.gz
                                                    Evidence: sub-058_dir-AP_epi.nii.gz
                                    ./sub-058v1/fmap/sub-058_dir-PA_epi.json
                                                    Evidence: sub-058_dir-PA_epi.json
                                    ./sub-058v1/fmap/sub-058_dir-PA_epi.nii.gz
                                                    Evidence: sub-058_dir-PA_epi.nii.gz
                                    ./sub-058v1/func/sub-058_task-restPost_bold.json
                                                    Evidence: sub-058_task-restPost_bold.json
                                    ./sub-058v1/func/sub-058_task-restPost_bold.nii.gz
                                                    Evidence: sub-058_task-restPost_bold.nii.gz
                                    ./sub-058v1/func/sub-058_task-restPost_events.tsv
                                                    Evidence: sub-058_task-restPost_events.tsv
                                    ./sub-058v1/func/sub-058_task-restPost_sbref.json
                                                    Evidence: sub-058_task-restPost_sbref.json
                                    31m... and 17 more files having this issue (Use --verbose to see them all)

In this case, BIDS validation is throwing an error because the subject ID in the folder name does 
not match the subject ID of the files within it. For BIDS conversion to run successfully, the files 
would also need to be changed to “sub-058v1” rather than “sub-058” or the folder name would 
need to be changed back to “sub-058”.