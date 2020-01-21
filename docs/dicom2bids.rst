========================
DICOM to BIDs conversion
========================

clpipe has several commands to facilitate the conversion of DICOM files into NiFTI files all in BIDS format. We use `dcm2bids <https://https://github.com/cbedetti/Dcm2Bids>`_, which is a flexible system for converting DICOM files. It does require the creation of a configuration file, a Json that directs the conversion. Below we have an example of what this might look like.

One important thing to note about using the main command is the need for a specifically formatted `dicom_dir_format` option. This is to appropriately map your dicom directories to subject/sessions. All subject session folders should be named the same way. A dicom_dir_format must contain at least {session} and can contain a {subject} formatting option.  Two examples of a dicom_dir_format option are `{subject}_{session}`, which corresponds to the following structure:

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

Alternatively, you can use `{subject}/{session}`

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


You can include other text in the formatting option, so that the program ignores that text. For example, `Subject-{subject}` used on a dataset with `Subject-01` as a folder will determine the subject id to be `01` not `Subject-01`.

dcm2bids Helper Function
------

To obtain the information from the header needed to complete the conversion config json, dcm2bids has a handy helper function:

.. code-block:: console

    usage: dcm2bids_helper [-h] -d DICOM_DIR [DICOM_DIR ...] [-o OUTPUT_DIR]

    optional arguments:
        -h, --help            show this help message and exit
        -d DICOM_DIR [DICOM_DIR ...], --dicom_dir DICOM_DIR [DICOM_DIR ...] DICOM files directory
        -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Output BIDS directory, Default: current directory

            Documentation at https://github.com/cbedetti/Dcm2Bids

This command will create convert an entire folder's data, and create a temporary directory containing all the converted files, and more importantly the sidecar jsons. These jsons contain the information needed to update the conversion configuration file.

Note: If you are doing a longitudinal study and the sessions are different from each other, you should do this separately for each session. Ex:

.. code-block:: console

	dcm2bids_helper -d data_DICOMs/1005/01 -o temp_s1
	dcm2bids_helper -d data_DICOMs/1005/02 -o temp_s2


Conversion Config
------

The other important ingredient in converting your DICOMs to BIDS format is the conversion configuration. An example file is generated when you use the project_setup command in the project directory. Below is a brief example:

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
			"criteria": {
				"SeriesDescription": "*_resting_*"
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
		}
		
		]
	}

This configuration file looks for all scans that have "_srt" anywhere in the SeriesDescription field of the header, converts them into NIFTI, labels them in the BIDS standards, and adds the custom label of `task-srt`. It does the same for anatomical scans with "MPRAGE" contained in the series description. Any header field in the dicoms can be used as criteria. If multiple scans meet the criteria, then they will be labeled `run-1, run-2, ...` in order of acquisition.

Params:

* ``dataType:`` “anat”,”func”,”dwi” [required]
* ``modalityLabel:`` “T1w”,”T2w”,“bold”,”dwi” [required]
* ``customLabels:`` What to name the ouput. Must be 'task-XXX'. May have restrictions for other modalities.
* ``Criteria:`` How to select your scan from the DICOM header. Everything in criteria, when used in combination, needs to be unique to a run type (MPRage, T2-weighted, resting state, each task scan individually, DWI scans, etc--note that if you have different acquisition directions need to include that as well)

Converting to Bids
------

Once you have updated your conversion configuration file, you can convert your entire dataset with:

.. code-block:: console

    convert2bids [OPTIONS]

        Options:
            -config_file PATH       The configuration file for the study, use if you
                                    have a custom batch configuration.
        -conv_config_file PATH      The configuration file for the study, use if you
                                    have a custom batch configuration.
        -dicom_dir TEXT             The folder where subject dicoms are located.
        -dicom_dir_format TEXT      Format string for how subjects/sessions are
                                    organized within the dicom_dir.
        -BIDS_dir TEXT              The dicom info output file name.
        -overwrite                  Overwrite existing BIDS data?
        -log_dir TEXT               Where to put the log files. Defaults to Batch_Output
                                    in the current working directory.
        -subject TEXT               A subject  to convert using the supplied configuration
                                    file.  Use to convert single subjects, else leave empty.
        -session TEXT               A session  to convert using the supplied configuration
                                    file.  Use in combination with -subject to convert single
                                    subject/sessions, else leave empty.
        --help                      Show this message and exit.
