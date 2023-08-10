=======================
ROI Extraction
=======================


clpipe comes with a variety of functional and anatomical atlases, 
which can be used to extract ROI time series data from functional scans.

By default, ROIs are calculated with respect an image's fMRIPrep brain mask.
ROIs with a with a percentage of voxels outside of this mask exceeding "PropVoxels" 
will be set to "nan". 
If any ROI has no voxels in the brain mask, then all ROIs will 
be extracted without respect to the brain mask, and then ROIs with 
fewer than "PropVoxels" voxels will be set to "nan". This is a workaround for 
the limitations on Nilearn's ROI extractor functions.

ROI Extraction Options
----------------

.. autoclass:: clpipe.config.project.ROIOptions

.. click:: clpipe.cli:fmri_roi_extraction_cli
	:prog: clpipe roi extract

Viewing Available Atlases
----------------

To view the available built-in atlases, you can use the ``get_available_atlases`` 
command.

.. click:: clpipe.cli:get_available_atlases_cli
	:prog: clpipe roi atlases
