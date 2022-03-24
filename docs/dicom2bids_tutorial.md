# BIDS Conversion

The goal of this processing step is to convert "raw" DICOM format images into BIDS format. If your data is already in BIDS format, move on to the BIDS Validation step.

Due to the manual labeling necessary for DICOM to BIDS conversion, this is one of the most difficult parts of clpipe to setup - do not be discourged by this early step!

> Note: This tutorial is a clpipe implmentation of the [dcm2bids](https://unfmontreal.github.io/Dcm2Bids/docs/2-tutorial/) tutorial, which clpipe uses for dcm to BIDS conversion.

## Obtaining Sample Raw Data

To obtain the raw DICOM data necessary for this tutorial, run the following commands:

```
cd data_DICOMs
git clone git@github.com:neurolabusc/dcm_qa_nih.git
cd ..
```

Let's examine this data:

```
dcm_qa_nih/In/
├── 20180918GE
│   ├── mr_0004
│   ├── mr_0005
│   ├── mr_0006
│   ├── mr_0007
│   └── README-Study.txt
└── 20180918Si
 ├── mr_0003
 ├── mr_0004
 ├── mr_0005
 ├── mr_0006
 └── README-Study.txt
```

This dataset contains two sets of data, one from a GE scanner, containing functional images, and another from a Siemens, containing field map images. The labels in the form `mr_000x` are subject ids, which will be important for setting up our bids conversion.

> Note: The BIDS data generated in this step will also be used in the BIDS Validation tutorial, but tutorials starting from fMRIprep and on we will use a different BIDS dataset


## clpipe_config.json Setup

Open clpipe_config.json and navigate to the "DICOMToBIDSOptions":

```
"DICOMToBIDSOptions": {
	"DICOMDirectory": "<your system's path>/clpipe_tutorial_project/data_DICOMs",
	"BIDSDirectory": "<your system's path>/clpipe_tutorial_project/data_BIDS",
	"ConversionConfig": "<your system's path>/clpipe_tutorial_project/conversion_config.json",
	"DICOMFormatString": "",
	"TimeUsage": "1:0:0",
	"MemUsage": "5000",
	"CoreUsage": "2",
	"LogDirectory": "<your system's path>/clpipe_tutorial_project/logs/DCM2BIDS_logs"
}
```

This section tells clpipe how to run your BIDS conversion. Note that clpipe has been automatically configured to point to your DICOM directory, "DICOMDirectory", which will serve as the input to the dcm2bids command. The output folder, "BIDSDirectory", is also already set. These can be modified to point to new locations if necessary - for example, you may want to create more than one BIDS directory for testing purposes.

The option "DICOMFormatString" must be set to run your bids conversion. This configuration tells clpipe how to identify subjects and (if relevant) sessions within `data_DICOMs`. To pick up on the subject ids in our example dataset, the placeholder `{subject}` should be given in place of a specific subject's directory:

```
"DICOMFormatString": "dcm_qa_nih/In/20180918GE/{subject}"
```

If your data contained an addtional folder layer corresponding to session ids, you would similarily mark this with a `{session}` placeholder

The "ConversionConfig" command gives a path to your automatically generated conversion_config.json file. Let's open that file now:

```
{
	"descriptions": [
		{
			"dataType": "func",
			"modalityLabel": "bold",
			"customLabels": "task-srt",
			"criteria": {
				"SeriesDescription": "*_srt",
				"ImageType": [
					"ORIG*",
					"PRIMARY",
					"M",
					"ND",
					"MOSAIC"
				]
			}
		}
	]
}
```
The conversion file contains a list of descriptions, each of which attempts to map raw DICOM images to a given critera. clpipe has prepopulated the conversion config file with an example description.

The "critera" item gives a list of critera by which to match DICOM images. The other tags specify the format of the output NIfTI image that match this critera. "dataType" and "modalityLabel" configure the name of your output

More information on setting up clpipe for BIDS conversion can be found in the [clpipe documentation](https://clpipe.readthedocs.io/en/latest/dicom2bids.html#).


## Setting up the Conversion File
From here, follow the [Dcm2Bids tutorial](https://unfmontreal.github.io/Dcm2Bids/docs/2-tutorial/#dicom-to-nifti-conversion) and stop before the "Running dcm2bids" section - clpipe will handling running dcm2bids for you. The helper command `dcm2bids_helper` will be available to you via the clpipe installation, and should be used as indicated in the tutorial to help you get started. You should also skip the "Building the configuration file" step because, as shown above, clpipe has already created this file.

You can find a supplentary explanation and another example of a conversion_config.json file in the [clpipe documentation](https://clpipe.readthedocs.io/en/latest/dicom2bids.html#)


## Running the Conversion
Now you are ready to launch the conversion with clpipe, which will convert your raw DICOMs into NIfTI format, then rename and sort them into the BIDS standard.

If everything has been set up correctly, running the conversion only takes a simple call to the [CLI application](https://clpipe.readthedocs.io/en/latest/dicom2bids.html#conversion-commands) with the configuration file as an argument:

```
convert2bids -config_file clpipe_config.json
```

clpipe will then print out a "plan" for executing your jobs:

```
dcm_qa_nih/In/20180918GE/*
/nas/longleaf/home/willasc/data/clpipe/clpipe_tutorial_project/data_DICOMs/dcm_qa_nih/In/20180918GE/{subject}/
sbatch --no-requeue -n 1 --mem=5000 --time=1:0:0 --cpus-per-task=2 --job-name="convert_sub-mr_0004" --output=/nas/longleaf/home/willasc/data/clpipe/clpipe_tutorial_project/logs/DCM2BIDS_logs/Output-convert_sub-mr_0004-jobid-%j.out --wrap="dcm2bids -d <your system's path>/clpipe_tutorial_project/data_DICOMs/dcm_qa_nih/In/20180918GE/mr_0004/ -o <your system's path>/clpipe/clpipe_tutorial_project/data_BIDS -p mr_0004 -c <your system's path>/clpipe_tutorial_project/conversion_config.json"
sbatch --no-requeue -n 1 --mem=5000 --time=1:0:0 --cpus-per-task=2 --job-name="convert_sub-mr_0005" --output=<your system's path>/clpipe_tutorial_project/logs/DCM2BIDS_logs/Output-convert_sub-mr_0005-jobid-%j.out --wrap="dcm2bids -d <your system's path>clpipe_tutorial_project/data_DICOMs/dcm_qa_nih/In/20180918GE/mr_0005/ -o <your system's path>/clpipe_tutorial_project/data_BIDS -p mr_0005 -c <your system's path>/clpipe_tutorial_project/conversion_config.json"
...
```

Each `sbatch` command here will submit a separate job to the cluster.

Check that your output looks correct, especially the subject ids, then run again with the `-submit` flag to run your conversions in parallel:

```
convert2bids -config_file clpipe_config.json -submit
```

clpipe should then report that you have submitted 4 jobs to the cluster:

```
dcm_qa_nih/In/20180918GE/*
/nas/longleaf/home/willasc/data/clpipe/clpipe_tutorial_project/data_DICOMs/dcm_qa_nih/In/20180918GE/{subject}/
Submitted batch job 38210854
Submitted batch job 38210855
Submitted batch job 38210856
Submitted batch job 38210857
```


Now, your BIDS directory should look something like this:

```
├── CHANGES
├── code
├── dataset_description.json
├── derivatives
├── participants.json
├── participants.tsv
├── README
├── sourcedata
├── sub-mr_0004
│   └── func
│       ├── sub-mr_0004_task-rest_bold.json
│       └── sub-mr_0004_task-rest_bold.nii.gz
└── tmp_dcm2bids
```

But wait a second! You were expecting four subjects to be in your BIDS directory, but only `sub-mr_0004` is present. The next section will guide you through how to tune your `conversion_config.json` file to pick up all of the images you need.

## Iterating on Your Conversion

Inevitably, you will probably not get the conversion completely correct on the first try, and some files may have been missed.

The folder `tmp_dcm2bids` contains all of the images that were not matched to any of the patterns described in your `conversion_config.json` file, as well as helpful log files:

```
└── tmp_dcm2bids
    ├── log
    │   ├── sub-mr_0004_2022-02-17T103129.039268.log
    │   ├── sub-mr_0005_2022-02-17T103129.116426.log
    │   ├── sub-mr_0006_2022-02-17T103129.082788.log
    │   └── sub-mr_0007_2022-02-17T103129.191004.log
    ├── sub-mr_0004
    ├── sub-mr_0005
    │   ├── 005_mr_0005_Axial_EPI-FMRI_(Sequential_I_to_S)_20180918114023.json
    │   └── 005_mr_0005_Axial_EPI-FMRI_(Sequential_I_to_S)_20180918114023.nii.gz
    ├── sub-mr_0006
    │   ├── 006_mr_0006_Axial_EPI-FMRI_(Interleaved_S_to_I)_20180918114023.json
    │   └── 006_mr_0006_Axial_EPI-FMRI_(Interleaved_S_to_I)_20180918114023.nii.gz
    └── sub-mr_0007
        ├── 007_mr_0007_Axial_EPI-FMRI_(Sequential_S_to_I)_20180918114023.json
        └── 007_mr_0007_Axial_EPI-FMRI_(Sequential_S_to_I)_20180918114023.nii.gz
```

As the raw data folder we have pointed clpipe toward, `20180918GE`, contains functional data, we will look at the `"func"` list item in our `conversion_config.json` to adjust:

```
{
	"dataType": "func",
	"modalityLabel": "bold",
	"customLabels": "task-rest",
	"criteria": {
		"SeriesDescription": "Axial_EPI-FMRI*",
		"SidecarFilename": "*Interleaved_I_to_S*"
	}
}
```

Sidecars are .json files that have the same name as the `.nii.gz` main image file, and contain additional metadata for the image; they are part of the BIDS standard.

This configuration is trying to match on a side car with the pattern `"*Interleaved_I_to_S*"`, but we can see in the `tmp_dcm2bids` folder that none of the subjects here match this pattern. If we want to pick up the remaining subjects, we can relax this critera by removing it from `conversion_config.json` :

```
{
	"dataType": "func",
	"modalityLabel": "bold",
	"customLabels": "task-rest",
	"criteria": {
		"SeriesDescription": "Axial_EPI-FMRI*"
	}
}
```

> Note: Take special care to remove the comma following the "SeriesDescription" list item - using commas in a single-item list will result in invalid JSON that will cause an error

And rerunning the conversion:

```
convert2bids -config_file clpipe_config.json -submit
```

Now, all subjects should be present in your BIDS directory along with their resting state images:

```
...
├── sub-mr_0004
│   └── func
│       ├── sub-mr_0004_task-rest_bold.json
│       └── sub-mr_0004_task-rest_bold.nii.gz
├── sub-mr_0005
│   └── func
│       ├── sub-mr_0005_task-rest_bold.json
│       └── sub-mr_0005_task-rest_bold.nii.gz
├── sub-mr_0006
│   └── func
│       ├── sub-mr_0006_task-rest_bold.json
│       └── sub-mr_0006_task-rest_bold.nii.gz
├── sub-mr_0007
│   └── func
│       ├── sub-mr_0007_task-rest_bold.json
│       └── sub-mr_0007_task-rest_bold.nii.gz
└── tmp_dcm2bids
```


## Adding an Additional Data Source

Our raw data folder at `data_DICOMs/dcm_qa_nih/In/20180918Si` contains additonal images for our sample study. These are field maps that correspond to our functional resting state images. 

Due to the location of these field maps being in a separate folder from the functional data, they are a distinct source of data from the point of view of clpipe. Although we could combine the functional images and field maps into one folder, under their respective subjects, often we only want to read from source data.

We can point clpipe to this additional data by modifying the `clpipe_config.json` to point to its path in `DICOMToBIDSOptions`, under `DICOMFormatString`:

```
"DICOMToBIDSOptions": {
	"DICOMDirectory": "<your system's path>/clpipe_tutorial_project/data_DICOMs",
	"BIDSDirectory": "<your system's path>/clpipe_tutorial_project/data_BIDS",
	"ConversionConfig": "<your system's path>/clpipe_tutorial_project/conversion_config.json",
	"DICOMFormatString": "dcm_qa_nih/In/20180918Si/{subject}",
	"TimeUsage": "1:0:0",
	"MemUsage": "5000",
	"CoreUsage": "2",
	"LogDirectory": "<your system's path>/clpipe_tutorial_project/logs/DCM2BIDS_logs"
}
```

We pick up a new subject this way:

```
├── sub-mr_0003
│   └── fmap
│       ├── sub-mr_0003_dir-AP_epi.json
│       └── sub-mr_0003_dir-AP_epi.nii.gz
```

However, our tmp_dcm2bids now contains more images that were not picked up. The images with "EPI" in the title are the field maps that our critera did not match:

```
├── sub-mr_0004
    │   ├── 004_mr_0004_Axial_EPI-FMRI_(Interleaved_I_to_S)_20180918114023.json
    │   └── 004_mr_0004_Axial_EPI-FMRI_(Interleaved_I_to_S)_20180918114023.nii.gz
    ├── sub-mr_0005
    │   ├── 005_mr_0005_EPI_PE=RL_20180918121230.json
    │   └── 005_mr_0005_EPI_PE=RL_20180918121230.nii.gz
    ├── sub-mr_0006
    │   ├── 006_mr_0006_EPI_PE=LR_20180918121230.json
    │   └── 006_mr_0006_EPI_PE=LR_20180918121230.nii.gz
```

Like our last iteration, we can adjust the conversion_config.json file to pick up these images. However, the two fmap critera we have already are properly picking up on the AP/PA field maps. Create two new critera to match the field maps found in `sub-mr_0005` and `sub-mr_0006`, one from LR and another for RL:

```
{
	"dataType": "fmap",
	"modalityLabel": "epi",
	"customLabels": "dir-RL",
	"criteria": {
		"SidecarFilename": "*EPI_PE=RL*"
	},
	"intendedFor": 0
},
{
	"dataType": "fmap",
	"modalityLabel": "epi",
	"customLabels": "dir-LR",
	"criteria": {
		"SidecarFilename": "*EPI_PE=LR*"
	},
	"intendedFor": 0
}
```

> Note: The "intendedFor" field points the fieldmap critera to the index of its corresponding functional image critera. In this case, we only have one functional image critera, for the resting state image, which is listed first (index 0). Therefore, it is important that the resting image critera stays first in the list; otherwise, these indexes would need to be updated.

After running the conversion again, you should now see that `sub-mr_0005` and `sub-mr_0006` have fieldmap images in addition to their functional scans:

```
├── sub-mr_0005
│   ├── fmap
│   │   ├── sub-mr_0005_dir-RL_epi.json
│   │   └── sub-mr_0005_dir-RL_epi.nii.gz
│   └── func
│       ├── sub-mr_0005_task-rest_bold.json
│       └── sub-mr_0005_task-rest_bold.nii.gz
├── sub-mr_0006
│   ├── fmap
│   │   ├── sub-mr_0006_dir-LR_epi.json
│   │   └── sub-mr_0006_dir-LR_epi.nii.gz
│   └── func
│       ├── sub-mr_0006_task-rest_bold.json
│       └── sub-mr_0006_task-rest_bold.nii.gz
```