===================
Overview
===================

*****************
Configuration Files
*****************

clpipe is driven by configuration files, and most commands in clpipe require a configuration file path
via their '-config_file' option. These configuration files are JSONs that contain 
all aspects of the preprocessing and postprocessing streams that 
you want applied to your dataset. 
clpipe provides you with a default configuration file after using the `project_setup`
command. To create addition configuration files for your dataset, use the following command:

.. click:: clpipe.cli:get_config_file
	:prog: clpipe config get

This command will create a default configuration file with whatever name you specified. 
The top of the default configuration file looks like this:

.. code-block:: json

    {
        "project_title": "test_project",
        "contributors": "SET CONTRIBUTORS",
        "project_directory": "/nas/longleaf/home/user/clpipe",
        "email_address": "SET EMAIL ADDRESS",
        "source": {
            "source_url": "fw://",
            "dropoff_directory": "",
            "temp_directory": "",
            "commandline_opts": "-y",
            "time_usage": "1:0:0",
            "mem_usage": "10G",
            "core_usage": "2"
        },
        "convert2bids": {
            "dicom_directory": "/nas/longleaf/home/user/clpipe/data_DICOMs",
            "bids_directory": "/nas/longleaf/home/user/clpipe/data_BIDS",
            "conversion_config": "/nas/longleaf/home/user/clpipe/conversion_config.json",
            "dicom_format_string": "",
            "time_usage": "1:0:0",
            "mem_usage": "5000",
            "core_usage": "2",
            "log_directory": "/nas/longleaf/home/user/clpipe/logs/DCM2BIDS_logs"
        },
        ...
    }

The configuration file consists of some project-level metadata, such as "ProjectTitle",
and a set of Option blocks that contain their own sub-settings. Each Option block
corresponds to a clpipe command, and controls the input parameters for that step.
For example, "DICOMtoBIDSOptions" corresponds to the convert2bids command. You can
find explanations for each specific Option block on the documenation page for its
corresponding command.

All of these fields have what the designers of clpipe consider to 
be reasonable defaults for processing. 
Additionally, users at UNC-CH on the Longleaf cluster with access to the 
HNG group should be able to use the default options with no change. 
Other users will have to modify several fields. 

Described here are the project-level meta fields of the configuration file:

.. autoclass:: clpipe.config.options.ProjectOptions

*****************
The Command Line Interface
*****************

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
        project_setup       Initialize a clpipe project.
        convert2bids        Convert DICOM files to BIDS format.
        bids_validate       Validate if a directory BIDS standard.
        templateflow_setup  Installs the templates for preprocessing listed in...
        preprocess          Submit BIDS-formatted images to fMRIPrep.
        postprocess         Additional processing for GLM or connectivity...
        glm                 General Linear Model (GLM) Commands.
        roi                 Region of Interest (ROI) Commands.
        flywheel_sync       Sync your DICOM data with Flywheel.
        reports             Generate reports for your project.
        config              Configuration-related commands.

clpipe commands can be called with the following format: ``clpipe <command>```
To see the documentation for a particular command, include the ``-help`` option:

.. code-block:: console

    > clpipe setup -help

    Usage: clpipe project_setup [OPTIONS]

    Initialize a clpipe project.

    Options:
        -project_title TEXT     Choose a title for your project.  [required]
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
    
    > clpipe glm launch -help 

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


*****************
Job Submission
*****************

.. autoclass:: clpipe.config.options.ParallelManagerConfig
