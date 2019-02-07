===============
BIDS Validation
===============

clpipe contains a convenience function to validate your datasets directly on the HPC. This function uses a Singularity image of the `BIDs Validator <https://github.com/bids-standard/bids-validator>`_. The command to run the BIDs validator is

.. code-block:: console

    Usage: bids_validate [OPTIONS] [BIDS_DIR]

      Runs the BIDS-Validator program on a dataset. If a configuration file has
      a BIDSDirectory specified, you do not need to provide a BIDS directory in
      the command.

    Options:
      -config_file FILE       Uses a given configuration file
      -verbose               Creates verbose validator output. Use if you want to
                             see ALL files with errors/warnings.
      -submit                Submit command to HPC.
      -interactive           Run in an interactive session. Only use in an
                             interactive compute session.
      -debug                 Produce detailed debug and traceback.
      --help                 Show this message and exit.

``bids_validate`` produces an output file titled `Output-BIDSValidator.out` at your current working directory that contains the output of the BIDS validator.
