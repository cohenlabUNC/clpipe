.. clpipe: A MRI Processing Pipeline for HPCs documentation master file, created by
   sphinx-quickstart on Sat Jan 26 16:29:17 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to clpipe: A MRI Processing Pipeline for high performance clusters!
===========================================================================

.. image:: https://zenodo.org/badge/165096390.svg
   :target: https://zenodo.org/badge/latestdoi/165096390

clpipe was developed to streamline the processing of MRI data using the high performance cluster at University of North Carolina at Chapel Hill. It uses `fmriprep <https://fmriprep.readthedocs.io/en/stable/>`_ for preprocessing fMRI data and implements a variety of additional processing steps important for functional connectivity analyses such as nuisance regression and filtering. Also included in clpipe are a variety of console commands for validation and checking the results of preprocessing. Please report any bugs, issues or feature requests on our `Github page<https://github.com/cohenlabUNC/clpipe>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   project_setup
   configfiles
   dicom2bids
   bidsvalidation
   fmriprep
   postprocessing
   susan
   roi_extraction
   glm

