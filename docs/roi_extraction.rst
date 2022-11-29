=======================
ROI Extraction
=======================


clpipe comes with a variety of functional and anatomical atlases, 
which can be used to extract ROI time series data from functional scans.

By default, ROIs are calculated with respect to the brain mask, 
and ROIs with fewer than the "PropVoxels" option voxels will be set to NAN. 
If any ROI has no voxels in the brain mask, then all ROIs will 
be extracted without respect to the brain mask, and then ROIs with 
fewer than "PropVoxels" voxels will be set to NAN. This is a workaround for 
the limitations on Nilearn's ROI extractor functions.

.. click:: clpipe.cli:fmri_roi_extraction_cli
	:prog: fmri_roi_extraction
	:nested: full

To view the available built-in atlases, you can use the ``get_available_atlases`` 
command.

.. click:: clpipe.cli:get_available_atlases_cli
	:prog: get_available_atlases
	:nested: full
