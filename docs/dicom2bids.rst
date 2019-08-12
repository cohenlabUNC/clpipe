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

The other important ingredient in converting your DICOMs to BIDS format is the conversion configuration. An example file is generated when you use the project_setup command. Below is a brief example:

.. code-block:: json

    {
    "descriptions": [
        {
            "dataType": "func",
            "modalityLabel": "bold",
            "customLabels": "task-srt",
            "criteria": {
				"SeriesDescription":"*_srt",
                "ImageType": ["ORIG*", "PRIMARY", "M", "ND", "MOSAIC"]
            }
        }
    ]
    }

This configuration file looks for all scans that have "_srt" anywhere in the SeriesDescription field of the header, converts them into NIFTI, labels them in the BIDS standards, and adds the custom label of `task-srt`. Any header field in the dicoms can be used as criteria. If multiple scans meet the criteria, then they will be labeled `run-1, run-2, ...` in order of acquisition.

To obtain the information from the header, dcm2bids has a handy helper function:

.. code-block:: console

    usage: dcm2bids_helper [-h] -d DICOM_DIR [DICOM_DIR ...] [-o OUTPUT_DIR]

    optional arguments:
        -h, --help            show this help message and exit
        -d DICOM_DIR [DICOM_DIR ...], --dicom_dir DICOM_DIR [DICOM_DIR ...] DICOM files directory
        -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Output BIDS directory, Default: current directory

            Documentation at https://github.com/cbedetti/Dcm2Bids

This command will create convert an entire folder's data, and create a temporary directory containing all the converted files, and more importantly the sidecar jsons. These jsons contain the information needed to update the conversion configuration file.

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
