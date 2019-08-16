=======================
SUSAN Spatial Smoothing
=======================


clpipe uses FSL's `SUSAN smoothing <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/SUSAN>`_ to perform spatial smoothing. This step is usually done after postprocessing. Options for this are configurable on a processing stream basis, see config file for more details.

.. code-block:: console


    Usage: susan_smoothing [OPTIONS] [SUBJECTS]...

    Options:
      -config_file PATH        Use a given configuration file. If left blank, uses
                               the default config file, requiring definition of
                               BIDS, working and output directories.
      -target_dir DIRECTORY    Which directory to process. If a configuration file
                               is provided.
      -target_suffix TEXT      Which file suffix to use. If a configuration file
                               is provided with a target suffix, this argument is
                               not necessary. Defaults to "preproc_bold.nii.gz"
      -output_dir DIRECTORY    Where to put the postprocessed data. If a
                               configuration file is provided with a output
                               directory, this argument is not necessary.
      -output_suffix TEXT      What suffix to append to the smoothed files. If a
                               configuration file is provided with a output
                               suffix, this argument is not necessary.
      -task TEXT               Which task to smooth. If left blank, defaults to
                               all tasks.
      -processing_stream TEXT  Optional processing stream selector.
      -log_dir DIRECTORY       Where to put HPC output files. If not specified,
                               defaults to <outputDir>/batchOutput.
      -submit                  Flag to submit commands to the HPC.
      -batch / -single         Submit to batch, or run in current session. Mainly
                               used internally.
      -debug                   Print detailed processing information and traceback
                               for errors.
      --help                   Show this message and exit.




