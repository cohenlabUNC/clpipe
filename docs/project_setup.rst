========================
Project Setup
========================

clpipe contains a convenience command for setting up the directories and configuration 
files for a given neuroimaging project, in a way that makes it simple to 
change configuration option.

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

.. click:: clpipe.project_setup:project_setup_cli
	:prog: project_setup
	:nested: full