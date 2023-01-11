===========================
Unified CLI
===========================

clpipe provides a unifed command line interface under the "clpipe" command.
This interface uses the same processing functions as clpipe's traditional commands,
except the are grouped together and given slightly different names. Unifying the
commands makes them easier to find and conceptualize in relation to one another without
having to rely too much on documentation.

Running this command on its own will show you a subset of clpipe's processing commands,
in the order that they are intended to be used:

.. code-block:: console

    > clpipe

    Usage: clpipe [OPTIONS] COMMAND [ARGS]...

    Welcome to clpipe. Please choose a processing command.

    Options:
    -v, --version  Display clpipe's version.
    --help         Show this message and exit.

    Commands:
    setup         Set up a clpipe project
    bids          BIDS Commands
    preprocess    Submit BIDS-formatted images to fMRIPrep
    postprocess   Additional preprocessing for connectivity analysis
    postprocess2  Additional preprocessing for GLM or connectivity analysis
    glm           GLM Commands
    status        Check the status of your project


NOTE - ROI extraction has yet to be added because one of its dependencies causes the CLI
to output an un-hidable warning

To see the options for a particular sub-command, call this command after "clpipe" and
ask for --help:

.. code-block:: console

    > clpipe setup --help

    Usage: clpipe setup [OPTIONS]

    Set up a clpipe project

    Options:
    -project_title TEXT     [required]
    -project_dir DIRECTORY  Where the project will be located.  [required]
    -source_data DIRECTORY  Where the raw data (usually DICOMs) are located.
    -move_source_data       Move source data into project/data_DICOMs folder.
                            USE WITH CAUTION.
    -symlink_source_data    Symlink the source data into project/data_dicoms.
                            Usually safe to do.
    -debug                  Flag to enable detailed error messages and traceback
    --help                  Show this message and exit.

This command can be used just like the original project_setup command in clpipe:

.. code-block:: console

    > clpipe setup -project_title "My Project" -project_dir . -debug


Some of the clpipe commands, like bids and glm, contain their own nested sub commands,
which can be viewed by calling the top command:

.. code-block:: console

    > clpipe bids

    Usage: clpipe bids [OPTIONS] COMMAND [ARGS]...

    BIDS Commands

    Options:
    --help  Show this message and exit.

    Commands:
    convert   Convert DICOM files to BIDS format
    validate  Check that the given directory conforms to the BIDS standard

These commands contain their own help dialouge as well:

.. code-block:: console

    > clpipe bids validate --help

    Usage: clpipe bids validate [OPTIONS] [BIDS_DIR]

    Check that the given directory conforms to the BIDS standard

    Options:
    -config_file FILE  Uses a given configuration file
    -log_dir FILE      Where to put HPC output files (such as SLURM output
                        files)
    -verbose           Creates verbose validator output. Use if you want to see
                        ALL files with errors/warnings.
    -submit            Flag to submit commands to the HPC
    -interactive       Run in an interactive session. Only use in an interactive
                        compute session.
    -debug             Flag to enable detailed error messages and traceback
    --help             Show this message and exit.

Here we perform the command equivalent to "bids_validate":

.. code-block:: console

    > clpipe bids validate -config_file path/to/my/config -submit

Finally, here is an equivalent command taking advantage of short option names:

.. code-block:: console

    > clpipe bids validate -c path/to/my/config -s

Here is a description of all available commands:

.. click:: clpipe.cli:cli
   :prog: clpipe
   :nested: full