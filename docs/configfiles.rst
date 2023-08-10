===================
Configuration Files
===================

Most commands in clpipe require a configuration file path
via their '-config_file' option. These configuration files are JSONs that contain 
all aspects of the preprocessing and postprocessing streams that 
you want applied to your dataset. 
To create a configuration file for your dataset use the following command:

.. code-block:: console

    get_config_file -outputFile <adirectory/yourfilename>.json

This command will create a default configuration file with whatever name you specified. 
The top of the default configuration file looks like this:

.. literalinclude:: ../clpipe/data/defaultConfig.json
   :language: json
   :lines: 1-20

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
We describe the various sections of the config now.

Header
------


.. autoclass:: clpipe.config.project.ProjectOptions





Processing Streams
------------------

* ``ProcessingStreams:`` A list of processing streams, consisting of the following:

    *``ProcessingStream:``: The name of the processing stream
            *``PostProcessingOptions:``: A list of options to overwrite.
            *``BetaSeriesOptions:``: A list of options to overwrite.

These options are for specific processing streams, and allow the user to overwrite the defaults.


ROI Extraction Options
----------------------
*```ROIExtractionOptions:``` Options for ROI extraction
    * ``TargetDirectory:`` What directory holds your fMRIPrep preprocessed data.
    * ``TargetSuffix:`` What suffix do your preprocessed fMRI NiFTi files have? Default is preproc_bold.nii.gz.
    * ``OutputDirectory:`` Where you want your postprocessed files to go.
    * ``Atlases``: A list of atlas names. Please refer to the ROI extraction documentation for a full list of included atlases.

Other Options
-------------

* ``RunLog:`` This list contains a record of how a given configuration file is used.
* ``BatchConfig:`` What batch configuration file to use. For more information see For Advanced Users/Batch Configuration.
