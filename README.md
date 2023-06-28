# clpipe 
[![DOI](https://zenodo.org/badge/165096390.svg)](https://zenodo.org/badge/latestdoi/165096390)

Python pipeline for neuroimaging data. Documentation at https://clpipe.readthedocs.io/en/latest/index.html

If you run into issues, find bugs, or have feature requests, please create an issue in this repository. 
If you have longer questions about the pipeline, or specific questions about the design choices, 
please get in contact with the creator of this pipeline, Teague Henry (ycp6wm@virginia.edu)

If you use clpipe to process data for a publication,
please cite the Zenodo repository linked above. 
A manuscript describing clpipe is being prepared, and once published,
will be the citation for the pipeline.

## Installation Guide for UNC-CH

### Module Method (recommended)
1. Ensure you are a member of the *rc_hng_psx* group
2. Open a Longleaf terminal session
3. Make the HNG modules available with the following command: `module use /proj/hng/software/modules`
4. Now save this module source to your default collection: `module save`
5. Once HNG modules are added, the clpipe module can be added and/or saved at any time: `module add clpipe`

All clpipe commands should now be accessible.

### Manual Installation
1. Open a Longleaf terminal session
2. Switch to python 3.7 using `module add python/3.7.14`
3. Install clpipe from GitHub with 
```pip3 install --user --upgrade  git+https://github.com/cohenlabUNC/clpipe.git```

All necessary dependencies should install to your local Python library, 
and the console commands should be immediately useable.