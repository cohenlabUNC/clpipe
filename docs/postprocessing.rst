===================
Postprocessing fMRI
===================

When performing functional connectivity analysis, there are several additional processing steps that need to be taken after the minimal preprocessing of fMRIPrep. clpipe implements these steps in Python, and a fMRIprep preprocessed dataset can be postprocessed using the following command:

.. code-block:: console

    usage: fmri_postprocess [options] [subjects...]
        options:
            -configFile, Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.
            -targetDir, Which fmriprep directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary. Note, must point to the ``fmriprep`` directory, not its parent directory.
            -targetSuffix, Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to 'preproc_bold.nii.gz'
            -outputDir, Where to put the postprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.
            -outputSuffix, What suffix to append to the postprocessed files. If a configuration file is provided with a output suffix, this argument is not necessary.
            -task, Which task to postprocess. If left blank, defaults to all tasks
            -TR, The TR of the scans. If a config file is not provided, this option is required. If a config file is provided, this information is found from the sidecar jsons.
            -logOutputDir, Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.
            -submit, Flag to submit commands to the HPC.
            -batch/single, submit to batch, or run in current session. Mainly used internally.
        subjects..., A list of subject IDs to process. If left blank, then all subjects are processed.


Processing Checker
------------------

clpipe has a convenient function for determining which scans successfully made it through both preprocessing using fMRIprep and postprocessing.

.. code-block:: console

    usage: fmri_process_check [options]
        options:
            -configFile, REQUIRED. The configuration file for the current processing run.
            -outputFile, The path and name for the output. Defaults to Checker-Output.csv, in the same directory as the configuration file.

This command will create a csv file listing all scans found in the BIDS dataset, and corresponding scans in the fMRIprep dataset and the postprocessed dataset.

For a description of the various postprocessing steps, along with references, please see the following documentation:




1. Nuisance Regression
2. Frequency Filtering
3. Scrubbing
4. Spectral Interpolation