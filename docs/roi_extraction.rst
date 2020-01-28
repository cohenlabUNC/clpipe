=======================
ROI Extraction
=======================


clpipe comes with a variety of functional and anatomical atlases, which can be used to extract ROI time series data from functional scans.

.. code-block:: console

    Usage: fmri_roi_extraction [OPTIONS] [SUBJECTS]...

    Options:
      -config_file PATH          Use a given configuration file. If left blank,
                                 uses the default config file, requiring
                                 definition of BIDS, working and output
                                 directories. This will extract all ROI sets
                                 specified in the configuration file.
      -target_dir DIRECTORY      Which postprocessed directory to process. If a
                                 configuration file is provided with a target
                                 directory, this argument is not necessary.
      -target_suffix TEXT        Which target suffix to process. If a
                                 configuration file is provided with a target
                                 suffix, this argument is not necessary.
      -output_dir DIRECTORY      Where to put the ROI extracted data. If a
                                 configuration file is provided with a output
                                 directory, this argument is not necessary.
      -task TEXT                 Which task to process. If none, then all tasks
                                 are processed.
      -atlas_name TEXT           What atlas to use. Please refer to documentation,
                                 or use the command get_available_atlases to see
                                 which are available. When specified for a custom
                                 atlas, this is what the output files will be
                                 named.
      -custom_atlas TEXT         A custom atlas image, in .nii or .nii.gz for
                                 label or maps, or a .txt tab delimited set of ROI
                                 coordinates if for a sphere atlas. Not needed if
                                 specified in config.
      -custom_label TEXT         A custom atlas label file. Not needed if
                                 specified in config.
      -custom_type TEXT          What type of atlas? (label, maps, or spheres).
                                 Not needed if specified in config.
      -radius TEXT               If a sphere atlas, what radius sphere, in mm. Not
                                 needed if specified in config.
      -overlap_ok                Are overlapping ROIs allowed?
      -overwrite                 Overwrite existing files?
      -log_output_dir DIRECTORY  Where to put HPC output files (such as SLURM
                                 output files). If not specified, defaults to
                                 <outputDir>/batchOutput.
      -submit                    Flag to submit commands to the HPC
      -single                    Flag to directly run command. Used internally.
      -debug                     Flag to enable detailed error messages and
                                 traceback
      --help                     Show this message and exit.


By default, ROIs are calculated with respect to the brain mask, and ROIs with fewer than the "PropVoxels" option voxels will be set to NAN. If any ROI has no voxels in the brain mask, then all ROIs will be extracted without respect to the brain mask, and then ROIs with fewer than "PropVoxels" voxels will be set to NAN. This is a workaround for the limitations on Nilearn's ROI extractor functions.

Viewing Built-In Atlases
-----

To view the available built-in atlases, you can use the ``get_available_atlases`` command.

Outputs:

* ``Atlast Label:`` XXX--name of the atlas
* ``Atlas Type:`` “Label” (functionally defined),”Sphere” (spherical) or “Map” (ROIs can be overlapping)
* ``Atlas Citation:`` XXX--paper citation for the atlas
