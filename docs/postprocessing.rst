===================
Postprocessing
===================

Overview
==================

The ``clpipe postprocess`` command combines the functionality of the
retired ``fmri_postprocess`` and ``glm_setup`` commands into a unified postprocessing stream.

This command allows for flexible creation of processing streams. The order of
processing steps and their specific implementations can be modified in the
configuration file. Any temporally-relevant processing steps can also be
applied to each image's corresponding confounds file.
``postprocess`` caches its processing intermediaries
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

Example Pipeline
------------------

.. image:: resources/example_pipeline.png


Configuration Overview
===================

This command requires a new configuration block - if you using an existing
clpipe project, you will have to insert this json into your configuration file.
Otherwise, this block will be included when running "project setup."

Configuration Block
-------------------

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

Configuration Definitions
-------------------

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


Processing Step Options
====================

Temporal Filtering
--------------------

This step removes signals from an image's timeseries based on cutoff thresholds.

**ProcessingStepOptions Block:**

.. code-block:: json

	"TemporalFiltering": {
		"Implementation":"fslmaths",
		"FilteringHighPass": 0.008,
		"FilteringLowPass": -1,
		"FilteringOrder": 2
	}

**Definitions:**

* ``Implementation:`` fslmaths, 3dTProject
* ``FilteringHighPass:`` Values below this threshold are filtered. Defaults to .08 Hz. Set to -1 to disable.
* ``FilteringLowPass:`` Values above this threshold are filtered. Disabled by default (-1).
* ``FilteringOrder:`` Order of the filter. Defaults to 2.

**Special Case: Filtering with Scrubbed Timepoints**

When the scrubbing step is active at the same time as temporal filtering (see
Scrub Timepoints), filtering is handled with a special workflow. This for two
reasons: first, temporal filtering must be done before scrubbing, because this step
cannot tolerate NAs or non-continuous gaps in the timeseries. Second, filtering can
distribute the impact of a disruptive motion artifact throughout a timeseries, despite
scrubbing the offending timepoints aftwards. The solution to this is to interpolate
over the timepoints to be scrubbed when temporal filtering.

The following diagram shows a timeseries with a large motion artifact (blue), with the points
to be scrubbed highlighted in red:

.. image:: resources/filter_with_scrubs_example.png

The processed timeseries (orange), after filtering, shows how the scrubbed points
were interpolated to improve the performance of the filter.

*Warning*: To achieve interpolation, this special case always uses the 3dTproject
implementation, regardless of the implementation requested.



Scrub Timepoints
--------------------

The ``ScrubTimepoints`` step can be used to remove timepoints from the image timeseries
based on a target variable from that image's confounds file. Timepoints scrubbed
from an image's timeseries are also removed its respective confound file.

ProcessingStepOptions Block:

.. code-block:: json

    "ScrubTimepoints": {
        "InsertNA": true,
        "Columns": [
            {
                "TargetVariable": "cosine*",
                "Threshold": 100,
                "ScrubAhead": 0,
                "ScrubBehind": 0,
                "ScrubContiguous": 0
            },
            {
                "TargetVariable": "framewise_displacement",
                "Threshold": 0.2,
                "ScrubAhead": 1,
                "ScrubBehind": 0,
                "ScrubContiguous": 0
            }
        ]
    }

Definitions:

* ``Columns:`` Contains a list of scrub variables for multiple target variables
* ``TargetVariable:`` Which confound variable to use as a reference for scrubbing. May use wildcards to pick multiple columns with similar names.
* ``Threshold:`` Any timepoint of the target variable exceeding this value will be scrubbed
* ``ScrubAhead:`` Set the number of timepoints to scrub ahead of target timepoints
* ``ScrubBehind:`` Set the number of timepoints to scrub behind target timepoints
* ``ScrubContiguous:`` Scrub everything between scrub targets up to this far apart
* ``InsertNA:`` Set true to replace scrubbed timepoints with NA. False removes the timepoints completely.



Processing Streams Setup
===================

By default, the output from running fmri_postprocess will appear in your
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

.. click:: clpipe.cli:postprocess_cli
	:prog: clpipe postprocess

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
of ``clpipe postprocess`` the name of the stream:

.. code-block:: console

	clpipe postprocess -config_file clpipe_config.json -processing_stream smooth_aroma-regress_filter-butterworth_normalize -submit