===================
Configuration Files
===================

Most command line functions in clpipe can take a configuration file in the '-configFile' option. These configuration files are JSONs that contain all aspects of the preprocessing and postprocessing streams that you want applied to your dataset. To create a configuration file for your dataset use the following command

.. code-block:: console

    get_config_file -outputFile <adirectory/yourfilename>.json

This command will create a default configuration file with whatever name you specified. The default configuration file looks like this

.. code-block :: json

   {
	"ProjectTitle": "A Neuroimaging Project",
	"Authors/Contributors": "SET AUTHOR",
	"ProjectDirectory": "",
	"EmailAddress": "SET EMAIL ADDRESS",
	"SourceOptions": {
		"SourceURL": "fw://",
		"DropoffDirectory": "",
		"TempDirectory": "",
		"CommandLineOpts": "-y",
		"TimeUsage": "1:0:0",
		"MemUsage": "10000",
		"CoreUsage": "1"
	},
	"DICOMToBIDSOptions": {
		"DICOMDirectory": "",
		"BIDSDirectory": "",
		"ConversionConfig": "",
		"DICOMFormatString": "",
		"TimeUsage": "1:0:0",
		"MemUsage": "5000",
        "CoreUsage": "2",
        "LogDirectory": ""
	},
	"BIDSValidationOptions": {
		"BIDSValidatorImage": "/proj/hng/singularity_imgs/validator.simg",
		"LogDirectory": ""
	},
	"FMRIPrepOptions": {
		"BIDSDirectory": "",
		"WorkingDirectory": "SET WORKING DIRECTORY",
		"OutputDirectory": "",
		"FMRIPrepPath": "/proj/hng/singularity_imgs/fmriprep_22.1.1.sif",
		"FreesurferLicensePath": "/proj/hng/singularity_imgs/license.txt",
		"UseAROMA": false,
		"CommandLineOpts": "",
		"TemplateFlowToggle": true,
		"TemplateFlowPath": "/proj/hng/singularity_imgs/template_flow",
		"TemplateFlowTemplates": [
			"MNI152NLin2009cAsym", 
			"MNI152NLin6Asym", 
			"OASIS30ANTs", 
			"MNIPediatricAsym", 
			"MNIInfant"
		],
		"FMapCleanupROIs": 3,
		"FMRIPrepMemoryUsage": "50000",
		"FMRIPrepTimeUsage": "16:0:0",
		"NThreads": "12",
        "LogDirectory": "",
		"DockerToggle": false,
		"DockerFMRIPrepVersion": ""
	},
	"PostProcessingOptions": {
		"WorkingDirectory": "",
		"WriteProcessGraph": true,
		"TargetDirectory": "",
		"TargetImageSpace": "MNI152NLin2009cAsym",
		"TargetTasks": [],
		"TargetAcquisitions": [],
		"OutputDirectory": "",
		"ProcessingSteps": [
			"SpatialSmoothing",
			"TemporalFiltering",
			"IntensityNormalization",
			"ApplyMask"
		],
		"ProcessingStepOptions": {
			"TemporalFiltering": {
				"Implementation":"fslmaths",
				"FilteringHighPass": 0.008,
				"FilteringLowPass": -1,
				"FilteringOrder": 2
			}, 
			"IntensityNormalization": {
				"Implementation": "10000_GlobalMedian"
			}, 
			"SpatialSmoothing": {
				"Implementation": "SUSAN",
      			"FWHM": 6
			},
			"AROMARegression":{
				"Implementation": "fsl_regfilt"
			},
			"ScrubTimepoints":{
				"TargetVariable": "framewise_displacement",
				"Threshold": 0.9,
				"ScrubAhead": 0,
				"ScrubBehind": 0,
				"ScrubContiguous": 0,
				"InsertNA": true
			},
			"Resample":{
				"ReferenceImage": "SET REFERENCE IMAGE"
			},
			"TrimTimepoints": {
				"FromEnd": 0,
				"FromBeginning": 0
			},
			"ConfoundRegression": {
				"Implementation": "afni_3dTproject"
			}
		},
		"ConfoundOptions": {
			"Columns": [
				"csf", "csf_derivative1", 
				"white_matter", "white_matter_derivative1"
			],
			"MotionOutliers": {
				"Include": true,
				"ScrubVar": "framewise_displacement",
				"Threshold": 0.9,
				"ScrubAhead": 0,
				"ScrubBehind": 0,
				"ScrubContiguous": 0
			}
		},
		"BatchOptions": {
			"MemoryUsage": "20000",
			"TimeUsage": "2:0:0",
			"NThreads": "1"
		}	
	},
	"ProcessingStreams": [
		{
			"ProcessingStream": "smooth_aroma-regress_filter_normalize",
			"PostProcessingOptions": {
				"ProcessingSteps": [
					"SpatialSmoothing",
					"AROMARegression",
					"TemporalFiltering",
					"IntensityNormalization"
				]
			}
		},
		{
			"ProcessingStream": "filter_confound-regress",
			"PostProcessingOptions": {
				"ProcessingSteps": [
					"TemporalFiltering",
					"ConfoundRegression"
				]
			}
		},
		{
			"ProcessingStream": "smooth_aroma-regress_filter_normalize_fwhm-8",
			"PostProcessingOptions": {
				"ProcessingSteps": [
					"SpatialSmoothing",
					"AROMARegression",
					"TemporalFiltering",
					"IntensityNormalization"
				],
				"ProcessingStepOptions": {
					"SpatialSmoothing": {
						"FWHM": 8
					}
				}
			}
		}
	],
	"BetaSeriesOptions": {
		"TargetDirectory": "",
		"TargetSuffix": "preproc_bold.nii.gz",
		"OutputDirectory": "",
		"OutputSuffix": "betaseries.nii.gz",
		"ConfoundSuffix": "desc-confounds_regressors.tsv",
		"Regress": true,
		"NuisanceRegression": "QuadLagged",
		"WhiteMatter": true,
		"CSF": true,
		"GlobalSignalRegression": true,
		"FilteringHighPass": 0.008,
		"FilteringLowPass": -1,
		"FilteringOrder": 2,
		"TaskSpecificOptions": [
			{
				"Task": "",
				"ExcludeColumnInfo": "trial_type",
				"ExcludeTrialTypes": ["block"]
			}
		],
      "LogDirectory": ""
    },
	"ROIExtractionOptions": {
		"TargetDirectory": "",
		"TargetSuffix": "",
		"OutputDirectory": "",
		"Atlases": ["power"],
		"RequireMask": true,
		"PropVoxels": 0.5,
        "MemoryUsage":"20000",
        "TimeUsage": "2:0:0",
        "NThreads": "1",
        "LogDirectory": ""
	},
	"ReHoExtraction": {
		"TargetDirectory": "",
		"TargetSuffix": "",
		"ExclusionFile": "",
		"WorkingDirectory":"",
		"MaskDirectory": "",
		"MaskSuffix":  "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
		"MaskFileOverride": "",
		"OutputDirectory": "",
		"OutputSuffix": "",
		"Neighborhood": "vertices",
		"LogDirectory": ""
	},
	"T2StarExtraction": {
		"TargetDirectory": "",
		"TargetSuffix": "",
		"ExclusionFile": "",
		"WorkingDirectory":"",
		"MaskDirectory": "",
		"MaskSuffix":  "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
		"MaskFileOverride": "",
		"OutputDirectory": "",
		"OutputSuffix": "",
		"LogDirectory": ""
	},
	"RunLog": [],
	"StatusCache": "",
	"BatchConfig": "slurmUNCConfig.json"
}

All of these fields are required and have what the designers of clpipe consider to 
be reasonable defaults for processing. 
Additionally, users at UNC-CH on the Longleaf cluster with access to the 
HNG group should be able to use the default options with no change. 
Other users will have to modify several fields. 
We describe the various sections of the config now.

Header
------


* ``ProjectTitle:`` The title of your project. Not used in processing.
* ``Authors/Contributors`` Members of the project team. Not used in processing.
* ``ProjectDirectory`` Where the project is. Not used in processing.


FMRIPrep Options
----------------

.. autoclass:: clpipe.config.project.FMRIPrepOptions
	:members:


Postprocessing Options
----------------------

These are the processing options for function connectivity postprocessing only. Beta Series or GLM are separate option blocks.
Note: These are the master options, and changes in ```ProcessingStreams``` are changes from the master options.

* ``PostProcessingOptions:`` Options for various postprocessing steps.

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
    * ``OversamplingFreq``: The oversampling frequency for the spectral interpolation. Defaults to 4. For more information on spectral interpolation see Postprocessing/Spectral Interpolation.
    * ``PercentFrequencySample:`` Proportion (0 to 1, 1 being 100%) of spectrum to use in spectral interpolation. Defaults to 1. For more information on spectral interpolation see Postprocessing/Spectral Interpolation.
    * ``Scrubbing:`` True/False. Use scrubbing. Defaults to true. For more information on scrubbing see Postprocessing/Scrubbing.
    * ``ScrubFDThreshold:`` At what framewise displacement to scrub. Defaults to .3.
    * ``ScrubAhead:`` If a timepoint is scrubbed, how many points after to remove. Defaults to 2.
    * ``ScrubBehind:`` If a timepoint is scrubbed, how many points before to remove. Defaults to 2.
    * ``ScrubContig:`` How many good contiguous timepoints need to exist. Defaults to 4.
    * ``PostProcessingMemoryUsage:`` How much memory (RAM) per subject to request, in Mbs. Defaults to 20000Mb or 20Gb.
    * ``PostProcessingMemoryUsage:`` How much time per subject to request. Format is Hours:Mins:Seconds. Defaults to 8 hours.
    * ``NThreads:`` How many CPUs to request. Defaults to 1. Do not modify lightly.
    * ``SpectralInterpolationBinSize:`` How many voxels per bin to work on in spectral interpolation. Increasing this reduces time but increases memory usage. Defaults to 5000.
    * ``BIDSValidatorImage:`` Where the BIDS validator Singularity image is.
    * ``LogDirectory:`` Where cluster output files are stored.

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

SUSAN Smoothing
---------------

* ``SUSANOptions`` Options for FSL's SUSAN smoothing procedure
    * ``BrightnessThreshold``: The voxel intensity threshold used to distinguish where to smooth. It should be above background level, but below the contrast between edges.
    * ``FWHM``: The size of the smoothing kernel. Specifically the full width half max of the Gaussian kernel. Scaled in millimeters. 0 uses a 3x3x3 voxel smoother.

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
