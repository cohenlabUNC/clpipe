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
1. Open a Longleaf terminal session
2. Add the following line to your `~/.bashrc` file:
`module use /proj/hng/software/modules`
3. Add the latest version of clpipe with `module add clpipe`

All clpipe commands should now be accessible.

### Manual Installation

1. Open a Longleaf terminal session
2. Switch to python 3.7 using `module add python/3.7.14`
3. Install clpipe from GitHub with 
```pip3 install --user --upgrade  git+https://github.com/cohenlabUNC/clpipe.git```

All necessary dependencies should install to your local Python library, 
and the console commands should be immediately useable.

## Contribution Guide

### Dev Environment Setup

#### Docker Container

### Committing & Branching

### Release Strategy

#### Versioning Scheme

clpipe follows the `x.y.z` versioning scheme, where x is a breaking update, y introduces
major features, and z indicates minor updates.

#### Release Branch

When enough changes to the `develop` branch have been made, they can be merged together into
the main branch as a **release**. In order to allow futher development on the `develop`
branch to continue, a new branch should be created off of `develop` that is specific to that release.
The release branch should be named after the version `develop` was on when the release
branch was created - for example, `release-1.7.3`, if `develop` was on version 1.7.3.

#### Incrementing Develop

As soon as a release branch is created, the `develop` branch should have its version
updated in `setup.py`, usually by the minor value. For example, from `1.7.2` to `1.7.3`. If a major feature or breaking change
is included in subsequent development, the version should be updated to reflect this before release.

#### Release Branch PR to Main

#### Release Tagging, Documentation, and Artifact Distribution

