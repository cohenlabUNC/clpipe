===============
BIDS Validation
===============

*****************
Overview
*****************

clpipe contains a convenience function to validate your datasets directly on the HPC. 
This function uses a Singularity image of the 
`BIDs Validator <https://github.com/bids-standard/bids-validator>`_.

The output of this command will appear in your `logs/bids_validation_logs` folder
by default.

Notably, fMRIPrep will refuse to run non-valid BIDS datasets, unless you turn the
option off. The same bids-validator outputs can be viewed in fMRIPrep's logs, but
you may find this stand-alone command more convenient.

*****************
Configuration
*****************

**Definitions**

.. autoclass:: clpipe.config.project.BIDSValidatorOptions

*****************
Command
*****************

.. click:: clpipe.cli:bids_validate_cli
   :prog: clpipe bids_validate
   :nested: full
