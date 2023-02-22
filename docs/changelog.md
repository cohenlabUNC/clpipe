# Change Log - NEW

## 1.7.3 (Feb 22, 2023)

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