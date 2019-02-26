========================
DICOM to BIDs conversion
========================

clpipe has several commands to facilitate the conversion of DICOM files into NiFTI files all in BIDS format. We use `heudiconv <https://github.com/nipy/heudiconv>`_, which is a flexible system for converting DICOM files. It does require the creation of a heuristic file, a Python script that directs the conversion. The heudiconv Github repository has a variety of examples. One key part of writing the heuristic file is obtaining the scan information. The `dicom_to_nifti_to_bids_converter_setup` function (described below) will quickly extract a scan info spreadsheet, that will help in the writing of the heuristic file.

One important thing to note about using these commands is the need for a specially formatted dicom_directory path. This is due to some idiosyncrasies in heudiconv. First, the dicoms should be organized in the same way for all subjects, and for all sessions. So, a valid directory structure for two subjects would be

.. code-block:: console
    data/
        sub-1/
            sess-1/
                scan1/
                scan2/
        sub-2/
            sess-1/
                scan1/
            sess-2/
                scan1/
But this would not be a valid directory structure:

.. code-block:: console
    data/
        subject-1/
            session-1/
                scan1/
                scan2/
        sub-2/
            sess-1/
                scan1/
            sess-2/
                scan1/

With a valid directory structure, the subject ID and session ID are specified using `{subject}` and `{session}` so the dicom_directory path for the valid directory structure above would be:

.. code-block:: console
    data/sub-{subject}/ses-{session}/*/*

The `*` are wildcard characters, and allow for heudiconv to iterate through folders. In the above example, there are two `*` because following the session directory there is a scan directory, and within those scan directories there are the dicom files themselves.


.. code-block:: console

    Usage: dicom_to_nifti_to_bids_converter_setup [OPTIONS]

  This command can be used to compute and extract a dicom information
  spreadsheet so that a heuristic file can be written. Users should specify
  a subject with all scans of interest present, and run this command on all
  sessions of interest.

    Options:
      -config_file PATH      The configuration file for the study, use if you have
                             a custom batch configuration.
      -subject TEXT          A subject that has all scans of interest present.
                             [required]
      -session TEXT          A session indicator, if sessions are present
      -dicom_directory TEXT  The specially formatted dicom directory string.
                             Please see help pages at
                             https://clpipe.readthedocs.io/en/latest/index.html
                             for more details  [required]
      -output_file TEXT      The dicom info output file name.
      -submit                Submission job to HPC.
      --help                 Show this message and exit.


Following the writing of the heuristic file, the whole dataset (or subject subsets) can be converted with:

.. code-block:: console

    Usage: dicom_to_nifti_to_bids_converter [OPTIONS] [SUBJECTS]...

    This command uses heudiconv to convert dicoms into BIDS formatted NiFTI files. Users can specify any number of subjects, or leave subjects blank to convert all subjects.

    Options:
      -config_file PATH       The configuration file for the study.
      -heuristic_file TEXT    A heuristic file to use
      -dicom_directory TEXT   The specially formatted dicom directory string.
                              Please see help pages at
                              https://clpipe.readthedocs.io/en/latest/index.html
                              for more details
      -output_directory TEXT  Where to output the converted dataset
      -log_output_dir TEXT    Where to put the log files. Defaults to Batch_Output
                              in the current working directory.
      -submit                 Submit jobs to HPC
      -debug                  Debug flag for traceback
      --help                  Show this message and exit.
