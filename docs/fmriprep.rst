===========================
Preprocessing with fMRIprep
===========================

clpipe uses `fMRIprep <https://fmriprep.readthedocs.io/en/stable/>`_ to perform minimal preprocessing on functional MRI data. To submit your dataset for preprocessing, use the following command:

.. code-block:: console

    Usage: fmriprep_process [OPTIONS] [SUBJECTS]...

      This command runs a BIDS formatted dataset through fMRIprep. Specify
      subject IDs to run specific subjects. If left blank, runs all subjects.

    Options:
      -config_file FILE          Use a given configuration file. If left blank, uses
                                 the default config file, requiring definition of
                                 BIDS, working and output directories.
      -bids_dir DIRECTORY        Which BIDS directory to process. If a configuration
                                 file is provided with a BIDS directory, this
                                 argument is not necessary.
      -working_dir DIRECTORY      Where to generate the working directory. If a
                                 configuration file is provided with a working
                                 directory, this argument is not necessary.
      -output_dir DIRECTORY       Where to put the preprocessed data. If a
                                 configuration file is provided with a output
                                 directory, this argument is not necessary.
      -log_output_dir DIRECTORY  Where to put HPC output files (such as SLURM output
                                 files). If not specified, defaults to
                                 <outputDir>/batchOutput.
      -submit                    Flag to submit commands to the HPC
      -debug                     Flag to enable detailed error messages and
                                 traceback
      --help                     Show this message and exit.

``fmriprep_process`` creates one batch job per subject. If you find that you are running out of memory, increase the `[FMRIPrepOptions][FMRIPrepMemoryUsage]` option in the configuration file.


Getting Quality Control Reports
-------------------------------

fMRIprep produces detailed html reports for each subject, allowing users to visually inspect registration, normalization and confound plots. However, these reports do not have the images directly embedded in them, which means that directly downloading them from the HPC will not result in a usable report. There are two options:

1. Open the html reports directly on the HPC, using some sort of interactive web browser.
2. Download the reports and the images in the correct directory structure.

clpipe has a convenience function to organize and prepare a zip archive containing the reports and images, for quick download onto a personal computer.

.. code-block:: console

    Usage: get_reports [OPTIONS]

      This command creates a zip archive of fmriprep QC reports for download.

    Options:
      -config_file FILE    The configuration file for the current data processing
                           setup.  [required]
      -output_name TEXT    Path and name of the output archive. Defaults to current
                           working directory and "Report_Archive.zip"
      -debug               Print traceback on errors.
      --help               Show this message and exit.

This command uses the working directory previously specified to copy the reports and images to, then creates a zip archive containing them. This command is not a batch command, and can take a little time creating the archive, so be aware.

Once the archive is created, it can be downloaded and unzipped to a personal computer. The reports should correctly load images once opened.