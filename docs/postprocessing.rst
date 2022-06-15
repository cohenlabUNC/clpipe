===================
Postprocessing fMRI
===================

When performing functional connectivity analysis, there are several additional processing steps that need to be taken after the minimal preprocessing of fMRIPrep. clpipe implements these steps in Python, and a fMRIprep preprocessed dataset can be postprocessed using the following command:

.. code-block:: console

   Usage: fmri_postprocess [OPTIONS] [SUBJECTS]...

  This command runs an fMRIprep'ed dataset through additional processing, as
  defined in the configuration file. To run specific subjects, specify their
  IDs. If no IDs are specified, all subjects are ran.

    Options:
    -config_file PATH        Use a given configuration file. If left blank, uses
                             the default config file, requiring definition of
                             BIDS, working and output directories.
    -target_dir DIRECTORY    Which fmriprep directory to process. If a
                             configuration file is provided with a BIDS
                             directory, this argument is not necessary. Note,
                             must point to the ``fmriprep`` directory, not its
                             parent directory.
    -target_suffix TEXT      Which file suffix to use. If a configuration file
                             is provided with a target suffix, this argument is
                             not necessary. Defaults to "preproc_bold.nii.gz"
    -output_dir DIRECTORY    Where to put the postprocessed data. If a
                             configuration file is provided with a output
                             directory, this argument is not necessary.
    -output_suffix TEXT      What suffix to append to the postprocessed files.
                             If a configuration file is provided with a output
                             suffix, this argument is not necessary.
    -task TEXT               Which task to postprocess. If left blank, defaults
                             to all tasks.
    -TR TEXT                 The TR of the scans. If a cofig file is not
                             provided, this option is required. If a config file
                             is provided, this information is found from the
                             sidecar jsons.
    -processing_stream TEXT  Optional processing stream selector.
    -log_dir DIRECTORY       Where to put HPC output files. If not specified,
                             defaults to <outputDir>/batchOutput.
    -beta_series             Flag to activate beta-series correlation
                             correlation. ADVANCED METHOD, refer to the
                             documentation.
    -submit                  Flag to submit commands to the HPC.
    -batch / -single         Submit to batch, or run in current session. Mainly
                             used internally.
    -debug                   Print detailed processing information and traceback
                             for errors.
    --help                   Show this message and exit.



Processing Checker
------------------

clpipe has a convenient function for determining which scans successfully made it through both preprocessing using fMRIprep and postprocessing.

.. code-block:: console

    Usage: fmri_process_check [OPTIONS]

      This command checks a BIDS dataset, an fMRIprep'ed dataset and a
      postprocessed dataset, and creates a CSV file that lists all scans across
      all three datasets. Use to find which subjects/scans failed processing.

    Options:
      -config_file FILE  The configuration file for the current data processing
                        setup.  [required]
      -output_file TEXT  Path and name of the output CSV. Defaults to config
                        file directory and "Checker-Output.csv"
      -debug            Print traceback and detailed processing messages.
      --help            Show this message and exit.


This command will create a csv file listing all scans found in the BIDS dataset, and corresponding scans in the fMRIprep dataset and the postprocessed dataset.

For a description of the various postprocessing steps, along with references, please see the following documentation:




1. Nuisance Regression
2. Frequency Filtering
3. Scrubbing
4. Spectral Interpolation
