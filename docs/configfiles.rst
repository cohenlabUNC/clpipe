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


Beta Series Options
-------------------

These options are for the beta series calculations. This is a complex method, please see DOCUMENTATION NOT COMPLETE, for implementation details.

* ``BetaSeriesOptions`` Options for various postprocessing steps.

    * ``TargetDirectory:`` What directory holds your fMRIPrep preprocessed data.
    * ``TargetSuffix:`` What suffix do your preprocessed fMRI NiFTi files have? Default is preproc_bold.nii.gz.
    * ``OutputDirectory:`` Where you want your postprocessed files to go.
    * ``OutputSuffix:`` What suffix do you want appended to your postprocessed files? Make sure to end it with .nii.gz.
    * ``ConfoundSuffix:`` What suffix does the confound regressors file have. Default is confound_regressor.txt.
    * ``Regress:`` True/False. Do you want to perform nuisance regression on the data. Default True. For more info see Postprocessing/Nuisance Regression.
    * ``RegressionParameters:`` These are the headers for the various regression parameters in the fmriprep confound file. The defaults are for the latest fmriprep version. Change only if you are using a much earlier version of fmriprep.
    * ``NuisanceRegression:`` What type of nuisance regression do you want to perform. Default to QuadLagged (33 Parameter Regression). For more information see Postprocessing/Nuisance Regression.
    * ``WhiteMatter:`` True/False. Include mean whitematter signal into nuisance regression. Defaults to True.
    * ``CSF:`` True/False. Include mean cerebral spinal fluid signal into nuisance regression. Defaults to True.
    * ``GlobalSignalRegression:`` True/False. Include global signal into nuisance regression. Defaults to True.
    * ``FilteringHighPass:`` High pass frequency for filtering. Defaults to .08 Hz. For more information on filtering see Postprocessing/Frequency Filtering. Set to -1 to remove high pass filtering.
    * ``FilteringLowPass:`` Low pass frequency for filtering. Defaults to no filter (-1). For more information on filtering see Postprocessing/Frequency Filtering. Set to -1 to remove low pass filtering.
    * ``FilteringOrder:`` Order of filter. Defaults to 2. For more information on filtering see Postprocessing/Frequency Filtering.
    * ``TaskSpecificOptions:`` A list of option blocks, one for each task you are interested in using beta series with.
            * ``Task:`` Task name, must match BIDS task- signifier.
            * ``ExcludeColumnInfo`` The name of the column in the BIDS formatted events files that contain the information about the trials needed to be excluded from the beta series analysis. (for example, if you have events nested within blocks, then you would want to exclude the block "events")
            * ``ExcludeTrialType:`` A list of trial types to exclude.
    * ``LogDirectory:`` Where cluster output files are stored.


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
