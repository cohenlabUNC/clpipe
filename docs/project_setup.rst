========================
Project Setup
========================

clpipe contains a convenience command for setting up the directories and configuration files for a given neuroimaging project, in a way that makes it simple to change configuration options:

.. code-block:: console

    Usage: project_setup [OPTIONS]

    Options:
        -project_title TEXT     Any useful descriptor. Printed at the config but not otherwise used.  [required]
        -project_dir PATH       Where the project will be located.  [required]
        -source_data DIRECTORY  Where the raw data (usually DICOMs) are located.
        -symlink_source_data    symlink the source data into project/data_dicoms.
                                Usually safe to do.
        -submit                 Flag to submit commands to the HPC
        -debug                  Flag to enable detailed error messages and
                                traceback.
        --help                  Show this message and exit.

This command will create the necessary directory structures, as well as create a default configuration file with many directory fields already filled out. For example,

.. code-block:: console

    |-- analyses
    |-- clpipe_config.json
    |-- conversion_config.json
    |-- data_BIDS
    |   |-- CHANGES
    |   |-- code
    |   |-- dataset_description.json
    |   |-- derivatives
    |   |-- participants.json
    |   |-- participants.tsv
    |   |-- README
    |   |-- sourcedata
    |-- data_DICOMs -> /symlink/to/your/dicoms
    |-- data_fmriprep
    |-- data_postproc
    |   |-- betaseries_default
    |   |-- betaseries_noGSR
    |   |-- betaseries_noScrub
    |   |-- postproc_default
    |   |-- postproc_noGSR
    |   |-- postproc_noScrub
    |-- data_ROI_ts
    |   |-- postproc_default
    |-- logs
    |   |-- betaseries_logs
    |   |-- DCM2BIDS_logs
    |   |-- postproc_logs
    |   |-- ROI_extraction_logs
    |-- scripts

