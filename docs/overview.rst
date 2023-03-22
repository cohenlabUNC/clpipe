===================
Overview - NEW
===================

The Command Line Interface
------------------

clpipe provides a unifed command line interface (CLI) under the ``clpipe`` command.

Running this command on its own will show you a subset of clpipe's processing commands:

.. code-block:: console

    > clpipe

    Usage: clpipe [OPTIONS] COMMAND [ARGS]...

    Welcome to clpipe.

    Please choose one of the commands below for more information.

    If you're not sure where to begin, please see the documentation at:
    https://clpipe.readthedocs.io/en/latest/index.html

    Options:
        -version, -v   Display clpipe's version.
        -help          Show this message and exit.

    Commands:
        project_setup  Initialize a clpipe project.
        convert2bids   Convert DICOM files to BIDS format.
        bids_validate  Validate if a directory BIDS standard.
        preprocess     Submit BIDS-formatted images to fMRIPrep.
        postprocess    Additional processing for connectivity analysis.
        postprocess2   Additional processing for GLM or connectivity analysis.
        glm            General Linear Model (GLM) Commands.
        roi            Region of Interest (ROI) Commands.
        flywheel_sync  Sync your DICOM data with Flywheel.
        reports        Generate reports for your project.

clpipe commands can be called with the following format: ``clpipe <command>```
To see the documentation for a particular command, include the ``-help`` option:

.. code-block:: console

    > clpipe setup -help

    Usage: clpipe project_setup [OPTIONS]

    Initialize a clpipe project.

    Options:
        -project_title TEXT     [required]
        -project_dir DIRECTORY  Where the project will be located.  [required]
        -source_data DIRECTORY  Where the raw data (usually DICOMs) are located.
        -move_source_data       Move source data into project/data_DICOMs folder.
                                USE WITH CAUTION.
        -symlink_source_data    Symlink the source data into project/data_dicoms.
                                Usually safe to do.
        -debug                  Flag to enable detailed error messages and
                                traceback.
        -help                   Show this message and exit.

Here is an example of the same command being used:

.. code-block:: console

    > clpipe setup -project_title "My Project" -project_dir . -debug


Some of the clpipe commands, like ``glm`` and ``roi``, contain their own nested sub-commands,
which can be accessed like this: ``clpipe <command> <sub-command>``

These commands contain their own help dialogue as well:

.. code-block:: console

    Usage: clpipe glm launch [OPTIONS] LEVEL MODEL

    Launch all prepared .fsf files for L1 or L2 GLM analysis.

    LEVEL is the level of anlaysis, L1 or L2

    MODEL must be a a corresponding L1 or L2 model from your GLM configuration
    file.

    Options:
        -glm_config_file, -g FILE  The path to your clpipe configuration file.
                                    [required]
        -test_one                  Only submit one job for testing purposes.
        -submit, -s                Flag to submit commands to the HPC.
        -debug, -d                 Flag to enable detailed error messages and
                                    traceback.
        -help                      Show this message and exit.
