========================
DICOM to BIDs conversion
========================

clpipe has several commands to facilitate the conversion of DICOM files into NiFTI files all in BIDS format. We use `dcm2bids <https://github.com/UNFmontreal/Dcm2Bids>`_, which is a flexible system for converting DICOM files. It does require the creation of a configuration file, a JSON that directs the conversion. Below we have an example of what this might look like.

One important thing to note about using the main command is the need for a specifically formatted `dicom_dir_format` option. This is to appropriately map your dicom directories to subject/sessions. All subject session folders should be named the same way. A dicom_dir_format must contain at least {session} and can contain a {subject} formatting option.  Two examples of a dicom_dir_format option are `{subject}_{session}/`, which corresponds to the following structure:

.. code-block:: console

    dicom_datadata/
        S01_pre/
            scan1/
            scan2/
            scan3
        S01-post/
            scan1/
            scan2/
            scan3/

Alternatively, you can use `{subject}/{session}/`

.. code-block:: console

    data/
        S01/
            pre/
                scan1/
            post/
                scan1/
        S02/
            pre/
                scan1/
            post/
                scan1/


You can include other text in the formatting option, so that the program ignores that text. For example, `Subject-{subject}/` used on a dataset with `Subject-01` as a folder will determine the subject id to be `01` not `Subject-01`. Note that in all examples, there is a trailing forward slash.

Finally, instead of using the command line option, this  DICOM format string can be specified in the clpipe configuration JSON.

The other important ingredient in converting your DICOMs to BIDS format is the conversion configuration. An example file is generated when you use the project_setup command. Below is a brief example:

.. code-block:: json

   {
	"descriptions": [
		{
			"dataType": "anat",
			"modalityLabel": "T1w",
			"customLabels": "",
			"criteria": {
				"SeriesDescription": "T1w_MPRAGE",
				"ImageType": ["ORIGINAL", "PRIMARY", "M", "ND", "NORM"]
			}
		},
		{
			"dataType": "anat",
			"modalityLabel": "T2w",
			"customLabels": "",
			"criteria": {
				"SeriesDescription": "T2_AX_struct"
			}
		},
		{
			"dataType": "func",
			"modalityLabel": "bold",
			"customLabels": "task-rest",
            "sidecarChanges": {
                "TaskName": "Resting State"
            },
			"criteria": {
				"SeriesDescription": "*_resting_AP_*"
			}
		},
		{
			"dataType": "func",
			"modalityLabel": "bold",
			"customLabels": "task-gngreg",
			"criteria": {
				"SeriesDescription": "*_GNGregular*"
			}
		},
		{
			"dataType": "func",
			"modalityLabel": "bold",
			"customLabels": "task-gngrew",
			"criteria": {
				"SeriesDescription": "*_GNGreward*"
			}
		},
		{
			"dataType": "dwi",
			"modalityLabel": "dwi",
			"customLabels": "acq-APref",
			"criteria": {
				"SeriesDescription": "*p2_AP_TRACEW*"
			}
		},
		{
			"dataType": "dwi",
			"modalityLabel": "dwi",
			"customLabels": "acq-PAref",
			"criteria": {
				"SeriesDescription": "*p2_PA"
			}
		},
		{
			"dataType": "dwi",
			"modalityLabel": "dwi",
			"customLabels": "acq-AP",
			"criteria": {
				"SeriesDescription": "*p2_AP"
			}
		},
        	{
            		"dataType": "fmap",
            		"modalityLabel": "epi",
            		"criteria":{
                		"SeriesDescription": "*_resting_PA*"
            	},
            		"intendedFor": [2,3]
        	}
		
		]
	}

This configuration file looks for all scans that have "_srt" anywhere in the SeriesDescription field of the header, converts them into NIFTI, labels them in the BIDS standards, and adds the custom label of `task-srt`. It does the same for anatomical scans with "MPRAGE" contained in the series description. Any header field in the dicoms can be used as criteria. If multiple scans meet the criteria, then they will be labeled `run-1, run-2, ...` in order of acquisition.

Note that for fieldmaps, one can use the "intendedFor" option to specify which BOLD images a fieldmap should be used for. There are two important points here. The first is that the "intendedFor" field is 0-indexed, in that 0 corresponds to the first entry in the converstion config, 1 corresponds to the second entry, etc, etc. In the example above, the fieldmap is intended for the resting state scan and the GNG regular scan. Additionally, the intended for field is not sensitive to multiple runs. For example, if there are 2 resting state scans, and therefore the file names look like "sub-9999_task-rest_run-01_bold.nii.gz" and "sub-9999_task-rest_run-02_bold.nii.gz" after conversion, the IntendedFor field in the fieldmap's JSON will list "sub-9999_task-rest_bold.nii.gz" This is due to an issue with the dcm2bids package, and will result in the fieldmaps not being used. The workaround is to list each run explicitly in your conversion configuration, or to modify each fieldmap JSON after it is generated.

Finally, there are several varieties of fieldmaps allowable in the BIDS format, each needing a different set of conversion config entries. For a detailed look at these types, please see `the BIDS Specification <https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#fieldmap-data>`_.


Conversion Commands
===================

To obtain the information from the header, dcm2bids has a handy helper function:

.. code-block:: console

    usage: dcm2bids_helper [-h] -d DICOM_DIR [DICOM_DIR ...] [-o OUTPUT_DIR]

    optional arguments:
        -h, --help            show this help message and exit
        -d DICOM_DIR [DICOM_DIR ...], --dicom_dir DICOM_DIR [DICOM_DIR ...] DICOM files directory
        -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Output BIDS directory, Default: current directory

            Documentation at https://github.com/cbedetti/Dcm2Bids

This command will create convert an entire folder's data, and create a temporary directory containing all the converted files, and more importantly the sidecar JSONs. These JSONs contain the information needed to update the conversion configuration file.

Once you have updated your conversion configuration file, you can convert your entire dataset with:


.. click:: clpipe.cli:convert2bids_cli
   :prog: convert2bids
   :nested: full
