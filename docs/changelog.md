# Change Log

## 1.9.0 (Sep 15, 2023)

### Enhancements

- `postprocess` - postprocess2 is now named postprocess, replacing the original postprocessing functionality
- `postprocess` - Wildcards can now be used in the `target_variables` of the scrub configuration to select multiple columns with similar names, such as non_steady_state_outliers*
- `postprocess` - BIDS index now saves to the user's working directory
- `postprocess` - Logs now saved in folders according to stream, like the output and working directories
- `postprocess` - Distributor-level slurm jobs removed, simplifying job structure and removing the distributor log folder
- `postprocess` - Individual images now get their own rolling log files
- `postprocess` - Slurm output files are now saved to a separate `slurm_out` folder
- `postprocess` - There are now a default processing streams setup and named specifically for the GLM and functional connectivity analyses
- `glm` - GLM setup command now completely removed, in favor of using the GLM postprocessing stream
- `documentation` - Expanded documentation for Postprocessing section
- `documentation` - Sections reorganized and made more consistent with each other.
- `project_setup` - Now prompts for name of project if not given.
- `config update` - Converts config to new format and offers to backup old version


### Bug Fixes
- `postprocess` - Fixed an issue where postprocess took excessively long to index large datasets due to a bug in pybids
- `postprocess` - Issue where streams did not properly update postprocessing config fixed


### Deprecations & Removals
- `postprocess` - Removed original postprocessing command
- `postprocess` - Removed original susan command; now a step of postprocess
- `postprocess` - Disabled fmri-process-check report for now, pending rework
- `postprocess` - The stream file "processing_description.json" has been moved to the stream working directory and is now called "run_config.json"

### Development
- `configuration` - Dataclass-based configuration has been applied to all major clpipe commands
- `configuration` - Configuration is now serialized/deserialized with Marshmallow, which allows both JSON and YAML file types to be used
- `postprocess` - Global workflow now constructs image and confounds workflows on its own

## 1.8.1 (Jun 28, 2023)

### Enhancements
- `postproc2` - Added new step ScrubTimepoints, allowing timepoints to be removed from the image and confounds where a set threshold is exceeded for a chosen confound variable.
- `postproc2` - Wildcard statements such as `t_comp_cor*` can now be used in the `Columns` section of `ConfoundsOptions` to select multiple columns at once.
- `postproc2` - Added special case to Temporal Filtering, which will interpolate over any values removed in the ScrubTimepoints step. See the documentation at Postprocessing/postprocess2/Processing Step Options/Temporal Filtering

### Development
- `clpipe` - Contribution guide is now in its own markdown file separate from the setup guide. More details added to guide
- `tests` - New helper added for plotting timeseries data
- `tests` - Longer 100 timepoint sample image added for steps like Temporal Filtering that need more data for effective testing

## 1.8.0 (Apr 05, 2023)

### GLM Setup Command Deprecation
- `glm setup`: command deprecated, to be replaced by postprocess2
- `glm setup`: config file no longer contains GLMSetupOptions. TaskName, ReferenceImage, and ParentClpipeConfig options  previously in GLMSetupOptions have been moved to the top level of the configuration file, as they are still used by Level 1 & 2 setups.
- `glm setup`: Will still run "classic" glm setup pipeline when using a clpipe < 1.8 style glm config file, but prints a warning. Will print deprecation error and exit if using new-style glm setup config file
- `project_setup`: The default TargetDirectory and ConfoundDirectory of the default glm config file now point to `postproc2/default`
- `project_setup`: The default folder `data_GLMPrep` is no longer created
- `project_setup`: Log folders `logs/glm_logs/L1_launch` and `logs/glm_logs/L2_launch` are created instead of `glm_setup_logs`, and these path are auto-populated in the LogDir fields of the default glm config file

### Enhancements
- `preprocess`: `/work` added to the list of UNC bind paths, as `/pine` is being deprecated by Longleaf
- `preprocess`: when templateflow toggle is on, this step now automatically creates a .cache/templateflow folder for you in your home directory if it doesn't already exist
- `glm prepare`: Changed some message exclusive to the `-debug` flag to be viewable without the flag to improve verbosity of the command. Command also now gives a message when completed, won't run if no images are found, and won't run if the EV target folder doesn't exist
- `clpipe`: The `bids_validate` command was moved out of the `bids` sub-command and moved to the top level to make it easier to find/use and more closely resemble the original clpipe command. The `bids` sub-command is still useable, but has been hidden, and will be removed in a future update
- `clpipe`: Similar to above, the `dicom` command has been hidden, and its sub-commands `convert2bids` and `flywheel_sync` have been moved to the top level of the clpipe menu. The dicom command is still accessible, but hidden.
- `clpipe`: The `setup` command has been renamed `project_setup` for consistency with the original command, and to avoid a conflict where a general setup command for clpipe might be necessary (as opposed to setting up a project)
- `clpipe`: The double-dash form `--help` and `--version` options have been removed for consistency with the other commands. The short hand of help, `-h`, is removed for simplicity. The forms `-help` and `-version, -v` remain.
- `project_setup`: Several fields of config and glm_config files that need to be set by user, but appear blank in the starter config files, are now populated like "SET THIS FIELD" to make it clearer that they must be set
- `clpipe`: New documentation page "Overview" added to house top-level cli command info and future location for clpipe overview diagrams

### Bug Fixes
- `clpipe`: Fixed issue where username for clpipe.log file was not obtainable from a desktop node, raising an exception
- `glm report_outliers`: Fixed issue where outputs were doubled
- `project_setup`: Fixed bug where the L2 fsfs dir was not auto-populated in the default glm_config file

### Development
- `setup`: Decoupled creation of files at project_setup from the path setup of user's config file, paving the way to update the configuration system and making it easier to control when directory setup occurs.
- `tests`: Added fixture to allow testing for backwards compatibility with fmriprep < v21 style directory structure
- `CI/CD`: Added a modulefile generation script to support deploying modules automatically
- `CI/CD`: Updated build and deploy scripts to support automatic deployment of modules

## 1.7.3 (Feb 22, 2023)

### Enhancements

- `setup`: the "SourceOptions" block for `dicom flywheel_sync` is now included in the default configuration file
- `setup`: more modality examples added to conversion_config.json starter file (T1w and fmap)
- `setup`: conversion_config.json starter file now includes dcm2niix customization line which sets its search depth to its maximum value, allowing dcm2bids to work with flywheel's DICOM sync directory
- `setup`: the default `.bidsignore` file now includes `scans.json`, a file generated by heudiconv which would cause validation to fail otherwise
- `bids validate`: In `clpipe_config.json`, Moved `BIDSValidatorImage` from `PostprocessingOptions` block to `BIDSValidationOptions` block. The command will still look for the image in its old location if it can't find it in BIDSValidationOptions, maintaining backwards compatibility with < 1.7.3 config files
- `glm prepare`: improved logging messages
- `glm prepare` : changed how file copying works so only file contents are copied, not their permissions, making the command easier to run in a shared environment
- `clpipe`: `-config_file/-c` is now a required argument in most commands to prevent unhelpful error output if no config file given, and to steer clpipe more towards being configuration file driven
- `clpipe`: ignore writing to clpipe.log if the user does not have permission to do so
- `clpipe`: clpipe.log file now includes usernames
- `clpipe`: clpipe.log file is written with group write permission by default

### Bug Fixes

- `setup`: generated glm_config.json file's `[GLMSetupOptions][LogDirectory]` field is now automatically filled out. Previously it was left blank, despite the appropriate log folder being automatically created, and would throw an error in the batch manager if not filled out manually.
- `reports fmriprep`: fixed issue where the main .html report files were not being bundled into the output zip
- `glm prepare`: fixed issue where FileNotFoundErrors were not caught correctly, causing the program to exit earlier than intended


## 1.7.2 (Jan 31, 2023)

### Flywheel Sync

clpipe can now be used to sync DICOM data from Flywheel. Using Flywheel through clpipe allows the user to store their project's remote Flywheel path and download destination in their clpipe configuration file, and to automatically submit Flywheel sync commands to a cluster as batch jobs. clpipe also cleans up an oddly-named, empty temporary directory that is left behind when running Flywheel's sync command.

This feature is accessed with the command `clpipe dicom flywheel_sync`. The clpipe subcommand `clpipe dicom` was added to give this command a "home" and to house future dicom-specific commands.

```
clpipe dicom flywheel_sync -c /path/to/your/clpipe_config.json -submit
```

### GLM
- combined `l1_prepare_fsf` and `l2_prepare_fsf` into the `clpipe glm prepare` command to match how the launch command works:
```
> clpipe glm prepare
Usage: clpipe glm prepare [OPTIONS] LEVEL MODEL

  Propagate an .fsf file template for L1 or L2 GLM analysis.

  LEVEL is the level of anlaysis, L1 or L2

  MODEL must be a a corresponding L1 or L2 model from your GLM configuration
  file.

Options:
  -glm_config_file FILE  The path to your clpipe configuration file.
                         [required]
  -debug                 Flag to enable detailed error messages and traceback.
  -help, -h, --help      Show this message and exit.
```
- `l1_prepare_fsf` no longer leaves an underscore at the end of the .fsf file names or the feat output directories
- L1 and L2 config files now support LogDirectory options for specifying where to send the output of the launch command. The output folder is used by default if no LogDirectory is specified.
- Improved error handling for `clpipe glm prepare` command

### clpipe bids convert
- Command has been moved from `clpipe bids` to the new `clpipe dicom`, which better reflects the BIDS conversion operation (a command acting on DICOM data to convert it to BIDS format). It has also been renamed from from `convert` back to its original name, `convert2bids`, to improve the clarity of this command's name.

Usage now looks like this:

`clpipe dicom convert2bids -c path/to/my/clpipe_config.json 256 -submit`

### postproc2

- now supports either fmriprep v20 or v21's directory structure
- no longer deletes "processing_graph.dot" (source of "processing_graph.png" to avoid a race condition issues sometimes causing jobs to fail

### get_reports

Command `get_reports`, used for combining fMRIPrep QC report outputs into a ZIP archive:

- has been added to the main clpipe menu as `clpipe reports fmriprep`
- now prints more log messages
- creates an archive with a shorter directory path
- archive is now named "fMRIPrep_Archive" by default

### Other Updates

- Default version of fMRIPrep referenced in config updated to v21.0.2
- Shorthand commands (e.g. -c for config_file, -s for submit) have been made consistent across all commands under the `clpipe` command
- `clpipe postproc` no longer fails silently when no subjects are found - error is now raised