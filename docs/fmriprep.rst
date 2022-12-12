===========================
Preprocessing with fMRIprep
===========================

clpipe uses `fMRIprep <https://fmriprep.readthedocs.io/en/stable/>`_ to perform minimal
preprocessing on functional MRI data. 

``fmriprep_process`` creates one batch job per subject. 
If you find that you are running out of memory, 
increase the `[FMRIPrepOptions][FMRIPrepMemoryUsage]` option in the configuration file.

To submit your dataset for preprocessing, 
use the following command:

.. click:: clpipe.cli:fmriprep_process_cli
   :prog: fmriprep_process
   :nested: full




Getting Quality Control Reports
-------------------------------

fMRIprep produces detailed html reports for each subject, allowing users to visually 
inspect registration, normalization and confound plots. However, these reports do not 
have the images directly embedded in them, which means that directly downloading them 
from the HPC will not result in a usable report. There are two options:

1. Open the html reports directly on the HPC, using some sort of interactive web browser.
2. Download the reports and the images in the correct directory structure.

clpipe has a convenience function to organize and prepare a zip archive containing 
the reports and images, for quick download onto a personal computer.

This command uses the working directory previously specified to copy the reports and 
images to, then creates a zip archive containing them. This command is not a batch
 command, and can take a little time creating the archive, so be aware.

Once the archive is created, it can be downloaded and unzipped to a personal computer. 
The reports should correctly load images once opened.

.. click:: clpipe.get_reports:get_reports
   :prog: get_reports
   :nested: full
