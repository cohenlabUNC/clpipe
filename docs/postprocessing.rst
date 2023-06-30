===================
Postprocessing
===================

postprocess2
------------------

The ``clpipe postprocess2`` command combines the functionality of the legacy
``fmri_postprocess`` and ``glm_setup`` commands into a unified postprocessing stream.

This command allows for flexible creation of processing streams. The order of
processing steps and their specific implementations can be modified in the
configuration file. Any temporally-relevant processing steps can also be
applied to each image's corresponding confounds file.
``postprocess2`` caches its processing intermediaries
in a working directory, which allows quick re-runs of pipelines with 
new parameters.

This command will also output a detailed processing graph
for each processing stream.

Available processing steps:

	- Temporal Filtering
	- Intensity Normalization
	- Spatial Smoothing
	- AROMA Regression
	- Confound Regression
	- Apply Mask
	- Scrub Timepoints
	- Resample
	- Trim Timepoints

.. image:: resources/example_pipeline.png

Configuration Setup
===================

This command requires a new configuration block - if you using an existing
clpipe project, you will have to insert this json into your configuration file.
Otherwise, this block will be included when running "project setup."

.. code-block:: json

	"PostProcessingOptions2": {
		"WorkingDirectory": "",
		"WriteProcessGraph": true,
		"TargetImageSpace": "MNI152NLin2009cAsym",
		"TargetTasks": [],
		"TargetAcquisitions": [],
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
			...additional processing step options
		},
		"ConfoundOptions": {
			"Columns": [
				"csf", "csf_derivative1", "white_matter", "white_matter_derivative1"
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
	}

Processing Step Details
=======================

Scrub Timepoints
------------------

The ``ScrubTimepoints`` step can be used to remove timepoints from the image timeseries
based on a target variable from that image's confounds file. Timepoints scrubbed
from an image's timeseries are also removed its respective confound file.

Processing Step Options:
.. code-block:: json

	"ScrubTimepoints": {
		"TargetVariable": "framewise_displacement",
		"Threshold": 0.9,
		"ScrubAhead": 0,
		"ScrubBehind": 0,
		"ScrubContiguous": 0,
		"InsertNA": true
	}

Definitions:
* ``TargetVariable:`` Which confound variable to use as a reference for scrubbing
* ``Threshold:`` Any timepoint of the target variable exceeding this value will be scrubbed
* ``ScrubAhead:`` Set the number of timepoints to scrub ahead of target timepoints
* ``ScrubBehind:`` Set the number of timepoints to scrub behind target timepoints
* ``ScrubContiguous:`` Scrub everything between scrub targets up to this far apart
* ``InsertNA:`` Set true to replace scrubbed timepoints with NA. False removes the timepoints completely.

Configuration Definitions
===================

* ``PostProcessingOptions:`` Options for configuring post-fmriprep processing steps.

    * ``WorkingDirectory:`` Directory for caching intermediary processing files.
    * ``WriteProcessGraph:`` Set 'true' to write a processing graph alongside your output.
    * ``TargetImageSpace:`` Which space to use from your fmriprep output. This is the value that follows "space-" in the image file names.
    * ``TargetTasks:`` Which tasks to use from your fmriprep output. This is the value that follows "task-" in the image file names. Leave blank to target all tasks.
    * ``TargetAcquisitions:`` Which acquisitions to use from your fmriprep output. This is the value that follows "acq-" in the image file names. Leave blank to target all acquisitions.
    * ``ProcessingSteps:`` The default list of processing steps to use. Processing will follow the order of this list.
    * ``ProcessingStepOptions:`` The default processing options for each step.

        * ``TemporalFiltering:`` Apply temporal filtering to the image data. Also be applied to confounds.

			* ``Implementation:`` Currently limited to "fslmaths"
			* ``FilteringHighPass:`` High pass frequency for filtering. Defaults to .08 Hz. Set to -1 to remove high pass filtering.
			* ``FilteringLowPass:`` Low pass frequency for filtering. Defaults to no filter (-1). Set to -1 to remove low pass filtering.
			* ``FilteringOrder:`` Order of filter. Defaults to 2.
        * ``IntensityNormalization:`` Apply intensity normalization to the image data.

			* ``Implementation:`` Currently limited to "10000_GlobalMedian"
        * ``SpatialSmoothing:`` Apply spatial smoothing to the image data.

			* ``Implementation:`` Currently limited to "SUSAN"
			* ``FWHM:`` The size of the smoothing kernel. Specifically the full width half max of the Gaussian kernel. Scaled in millimeters.
        * ``AROMARegression:`` Regress out AROMA artifacts from the image data. Also be applied to confounds.

			* ``Implementation:`` Currently limited to "fsl_regfilt_R"
        * ``Resample:`` Resample the image into a new space.
        * ``TrimTimepoints:`` Trim timepoints from the beginning or end of an image. Also be applied to confounds.

			* ``FromEnd:`` Number of timepoints to trim from the end of each image.
			* ``FromBeginning:`` Number of timepoints to trim from the beginning of each image.
        * ``ConfoundRegression:`` Regress out the confound file values from your image. If any other processing steps are relevant to the confounds, they will be applied first.

			* ``Implementation:`` Currently limited to "afni_3dTproject"
    * ``ConfoundOptions:`` The default options to apply to the confounds files.
	
		* ``Columns:`` A list containing a subset of confound file columns to use from each image's confound file.
		* ``MotionOutliers:`` Options specific to motion outliers.

			* ``Include:`` Set 'true' to add motion outlier spike regressors to each confound file.
			* ``ScrubVar:`` Which variable in the confounds file should be used to calculate motion outliers, defaults to framewise displacement.
			* ``Threshold:`` Threshold at which to flag a timepoint as a motion outlier, defaults to .9
			* ``ScrubAhead:`` How many time points ahead of a flagged time point should be flagged also, defaults to 0.
			* ``ScrubBehind:`` If a timepoint is scrubbed, how many points before to remove. Defaults to 0.
			* ``ScrubContiguous:`` How many good contiguous timepoints need to exist. Defaults to 0.
    * ``BatchOptions:`` The batch settings for postprocessing.

        * ``MemoryUsage:`` How much memory to allocate per job.
        * ``TimeUsage:`` How much time to allocate per job.
        * ``NThreads:`` How many threads to allocate per job.


Processing Streams Setup
===================

By default, the output from running fmri_postprocess2 will appear in your
clpipe folder at data_postproc2/smooth_filter_normalize, reflecting the
defaults from PostProcessingOptions2.

However, you can utilize the power of processing streams to deploy multiple
postprocessing streams. Each processing stream you define your config file's 
ProcessingStreams block will create a new output folder named 
after the ProcessingStream setting.

Within each processing stream, you can override any of the settings in the main
PostProcessingOptions2 section. For example, in the follow json snippet,
the first processing stream will only pick "rest" tasks and defines its
own set of processing steps. The second stream does the same thing, but
specifies a filtering high pass by overriding the default value of -1 with
.009. 

Command
===================

.. click:: clpipe.cli:fmri_postprocess2_cli
	:prog: clpipe postprocess2

.. code-block:: json

	...
	"ProcessingStreams": [
		...
		{
			"ProcessingStream": "smooth_aroma-regress_filter-butterworth_normalize",
			"PostProcessingOptions": {
				"TargetTasks": [
					"rest"
				],
				"ProcessingSteps": [
					"SpatialSmoothing",
					"AROMARegression",
					"TemporalFiltering",
					"IntensityNormalization",
					"ApplyMask"
				]
			}
		},
		{
			"ProcessingStream": "smooth_aroma-regress_filter-high-only_normalize",
			"PostProcessingOptions": {
				"TargetTasks": [
					"rest"
				],
				"ProcessingSteps": [
					"SpatialSmoothing",
					"AROMARegression",
					"TemporalFiltering",
					"IntensityNormalization",
					"ApplyMask"
				],
				"ProcessingStepOptions": {
					"TemporalFiltering": {
						"FilteringHighPass": .009
					}
				}
			}
		},
	...

To run a specific stream, give the ``-processing_stream`` stream option
of ``clpipe postprocess2`` the name of the stream:

.. code-block:: console

	clpipe postprocess2 -config_file clpipe_config.json -processing_stream smooth_aroma-regress_filter-butterworth_normalize -submit


Legacy postprocess Command
------------------

Not all features of the legacy postprocess command have been implemented yet in
postprocess2, namely some which support functional connectivity, 
so the command remains available for this use.

When performing functional connectivity analysis, there are several additional 
processing steps that need to be taken after the minimal preprocessing of fMRIPrep. 
clpipe implements these steps in Python, and a fMRIprep preprocessed dataset can 
be postprocessed using the following command:

.. click:: clpipe.cli:fmri_postprocess_cli
	:prog: clpipe postprocess



Processing Checker
------------------

clpipe has a convenient function for determining which scans successfully made it 
through both preprocessing using fMRIprep and postprocessing.

This command will create a csv file listing all scans found in the BIDS dataset, 
and corresponding scans in the fMRIprep dataset and the postprocessed dataset.

For a description of the various postprocessing steps, along with references,
please see the following documentation:

1. Nuisance Regression
2. Frequency Filtering
3. Scrubbing
4. Spectral Interpolation

.. click:: clpipe.fmri_process_check:fmri_process_check
	:prog: clpipe reports fmri-process-check


SUSAN Spatial Smoothing
------------------


clpipe uses FSL's `SUSAN smoothing <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/SUSAN>`_ 
to perform spatial smoothing. This step is usually done after postprocessing. 
Options for this are configurable on a processing stream basis, 
see config file for more details.

.. click:: clpipe.susan_smoothing:susan_smoothing
	:prog: susan_smoothing


