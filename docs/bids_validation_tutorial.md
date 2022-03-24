# BIDS Validation


## Running the bids_validate command

Use the `bids_validate` command without the `-submit` flag to check your execution plan:

```
bids_validate -config_file clpipe_config.json
```

```
sbatch --no-requeue -n 1 --mem=3000 --time=1:0:0 --cpus-per-task=1 --job-name="BIDSValidator" --output=<your system's path>/clpipe_tutorial_project/Output-BIDSValidator-jobid-%j.out --wrap="singularity run --cleanenv -B /proj,/pine,/nas02,/nas <your validation image path>/validator.simg <your system's path>/clpipe_tutorial_project/data_BIDS"
```

If you are happy with the submission plan, add the submit flag:

```
bids_validate -config_file clpipe_config.json -submit
```

## Interpreting & Fixing the Validation Results

You should see the output of your validation at the root of your project directory, like this (it really should end up in the logs folder - we're working on it!):

```
├── analyses
├── clpipe_config.json
├── conversion_config.json
├── data_BIDS
├── data_DICOMs
├── data_fmriprep
├── data_GLMPrep
├── data_onsets
├── data_postproc
├── data_ROI_ts
├── glm_config.json
├── l1_feat_folders
├── l1_fsfs
├── l2_fsfs
├── l2_gfeat_folders
├── l2_sublist.csv
├── logs
├── Output-BIDSValidator-jobid-41362508.out
```

Now open this file - there will be two types of issues, `[ERR]` for errors and `[WARN]` for warnings. The errors must be resolved for the dataset to be considered a valid BIDS dataset. Warnings are important to review for insight into further potential problems in the data, but do not invalidate your dataset.

> Note: fMRIPrep runs BIDS validation again before it starts processing, and will not start if the dataset contains any errors!

### Error #1

Let's start with the first error:

```
	[31m1: [ERR] Files with such naming scheme are not part of BIDS specification...
		./tmp_dcm2bids/log/sub-0003_2022-03-23T155433.420971.log
			Evidence: sub-0003_2022-03-23T155433.420971.log
		./tmp_dcm2bids/log/sub-0004_2022-03-23T153854.035740.log
```

If you look closely, the BIDS validator is complaining about the tmp_dcm2bids files, which are not intended to be part of the dataset! In order to ask for this folder to not be considered part of the BIDS dataset, we need to specify this in a `.bidsignore` file.

Create a `.bidsignore` file in your BIDS directory:

```
touch data_BIDS/.bidsignore
```

Now, open this file and add the folder you'd like to ignore:

```
tmp_dcm2bids
```

Next, rerun the validation command and open your new validation results (make sure you aren't looking at the old results file again!). You should see that the error message about the tmp_dcm2bids folder is gone.

> Note: We plan to have clpipe automatically create this file soon

### Error #2

The next error should look like this:

```
[31m1: [ERR] 'IntendedFor' field needs to point to an existing file. (code: 37 - INTENDED_FOR)[39m
		./sub-0003/fmap/sub-0003_dir-AP_epi.nii.gz
			Evidence: func/sub-0003_task-rest_bold.nii.gz
```

It looks like sub-0003's 'IntendedFor' filed points to a non existent file. Let's verify this by opening the subject's .json sidecar, located at `data_BIDS/sub-0003/fmap/sub-0003_dir-AP_epi.json`

At the bottom of the file, we can see that sub-0003's IntendedFor field is pointing to a function image, but this subject has no functional images!

```
...
    "InPlanePhaseEncodingDirectionDICOM": "COL",
    "ConversionSoftware": "dcm2niix",
    "ConversionSoftwareVersion": "v1.0.20190902",
    "Dcm2bidsVersion": "2.1.6",
    "IntendedFor": "func/sub-0003_task-rest_bold.nii.gz"
}
```

Let's erase this field (don't forget to remove the comma on the line before it, too):
```
...
    "InPlanePhaseEncodingDirectionDICOM": "COL",
    "ConversionSoftware": "dcm2niix",
    "ConversionSoftwareVersion": "v1.0.20190902",
    "Dcm2bidsVersion": "2.1.6"
}
```

And try again. Now, the error message for this subject should be gone.

### Error #3

The final error is asking for the 'TaskName' on our rest data:

```
[31m1: [ERR] You have to define 'TaskName' for this file. (code: 50 - TASK_NAME_MUST_DEFINE)[39m
		./sub-0004/func/sub-0004_task-rest_bold.nii.gz
		./sub-0005/func/sub-0005_task-rest_bold.nii.gz
		./sub-0006/func/sub-0006_task-rest_bold.nii.gz
		./sub-0007/func/sub-0007_task-rest_bold.nii.gz
```

This error is asking us to include a "TaskName" field in our .json sidecar files. Luckily, we can ask dcm2bids to specify this in the `conversion_config.json` file. Open up `conversion_config.json` and add the `sidecarChanges` field to specify a task name to automatically add to our generated sidecar files:

```
{
    "descriptions": [
        {
        "dataType": "func",
        "modalityLabel": "bold",
        "customLabels": "task-rest",
        "sidecarChanges":{
            "TaskName": "rest"
        },
        "criteria": {
            "SeriesDescription": "Axial_EPI-FMRI*"
            }
        },
...
```

For this change, we will need to rerun the BIDS conversion. However, because these rest images were already successfully sorted into BIDS format, we will need to add the `-overwrite` flag to our `convert2bids` coomand (which calls dcm2bid's `--forceDcm2niix` and `--clobber` options under the hood)

Now we will have a clean slate when rerunning convert2bids, and we can see that the rest image sidecars now contain the `TaskName` field:

```
...
    "InPlanePhaseEncodingDirectionDICOM": "COL",
    "ConversionSoftware": "dcm2niix",
    "ConversionSoftwareVersion": "v1.0.20190902",
    "Dcm2bidsVersion": "2.1.6",
    "TaskName": "rest"
}
```

Finally, because we used the `-overwrite` flag, sub-0003's IntendedFor field will be re-inserted (Error #2). Repeat the fix for this problem by removing the IntendedFor field from sub-0003's sidecar .json.

Now, rerun bids_validate - you should be completely free of errors!


