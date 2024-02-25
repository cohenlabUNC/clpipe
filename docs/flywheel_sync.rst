===========================
Flywheel Sync
===========================

*****************
Overview
*****************

clpipe now provides an avenue for syncing DICOM data with a remote source through
the ``clpipe flywheel_sync`` command. Flywheel is used by many research institutions
and scan centers to upload the DICOMs collected in each scan session. Researchers can 
then download them, including through the ``clpipe flywheel_sync`` command.

*****************
Setup
*****************

First, the Flywheel CLI must be installed to make use of this command. For UNC-CH users, Flywheel should
be automatically loaded as a module when the clpipe module is loaded. If you need to
install Flywheel, you can find a link to the installer in your profile on the
Flywheel web app.

You will also need to login to Flywheel via the Flywheel CLI to use this command.
Navigate to the Flywheel web app. In the upper right, click on your profile drop down menu, select 'profile'.
Scroll down and copy the command under 'Getting Started With the CLI.' It should look like: ``login <FLYWHEEL URL>::<TOKEN>``. 
Run this command to login.

Using with convert2bids
#################

Flywheel creates a DICOM folder structure that is too deep for the
default depth setting of dcm2niix, which both dcm2bids and heudiconv use to discover
DICOM files in your source directory. However, dcm2niix can be configured to search
deeper with the ``-d`` option:

 
dcm2bids (clpipe default)
*****************

dcm2bids provides a method of passing options through to dcm2niix by adding a
`dcm2niixOptions` item to your conversion conversion_config.json file, like this:

.. code-block :: json

	{
	"dcm2niixOptions": "-b y -ba y -z y -f '%3s_%f_%p_%t' -d 9",
	"descriptions": [
		{
			"dataType": "anat",
			"modalityLabel": "T1w",
			"criteria": {
				"SeriesDescription": "ADNI3_t1_mprag_sag_p2_iso"
			}
		},
		{
			"criteria": {
				"SeriesDescription": "RIDL1"
			},
	...

You must include all options shown, because this argument overwrites the dcm2niixOptions,
as opposed to just appending to them.

The options above add the ``-d 9`` option, setting dcm2niix's search depth to the maximum
value.

For more information on the options dcm2niix offers, please visit `their documentation page <https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage>`_.

heudiconv
*****************

By default, heudiconv sets the search depth of dcm2niix high enough to find 
DICOM files within Flywheel's output structure, so no changes are required if you
use this converter.


Additional Notes
#################

This command creates its own log folder at ``<project>/logs/sync_logs``

One quirk of Flywheel's sync command is that it creates a strangely named temporary directory at
the currently working directory, which is empty after the sync is finished. clpipe
removes this folder automatically.

Note that if you are not using flywheel_sync and are downloading DICOMs directly from 
Flywheel or another platform, you will need to unzip the DICOMs before proceeding to BIDS conversion.

*****************
Configuration
*****************

**Configuration Block**

.. code-block :: json
   
	"SourceOptions": {
		"SourceURL": "fw://<LAB>/<STUDY>/",
		"DropoffDirectory": "/path/to/your/dicom_folder",
		"TempDirectory": "/path/to/a/temp_folder",
		"CommandLineOpts": "-y",
		"TimeUsage": "1:0:0",
		"MemUsage": "10000",
		"CoreUsage": "1"
	},

**Definitions**

.. autoclass:: clpipe.config.options.SourceOptions

*****************
Command
*****************

.. click:: clpipe.cli:flywheel_sync_cli
	:prog: clpipe flywheel_sync
	:nested: full


*****************
Using clpipe flywheel_sync
*****************

When using the flywheel_sync command, be aware that it will sync all the DICOMs in the 
specified Flywheel project rather than a specific participant. It will be able to pick 
up on whether you already have a subject and all their DICOMs in the specified dropoff 
directory you give it; if that's the case, it will skip downloading that subject's 
DICOMs again.

If you would like to run flywheel sync routinely, you can submit a slurm job using 
sbatch that queues it to be run regularly. For example, the script below regularly 
runs flywheel sync every week.

.. code-block :: RST

    #!/bin/bash
    #SBATCH --mem=8G
    #SBATCH --output=/proj/hng/study/clpipe/scripts/pipeline/logs/flywheel_weekly_ingestion_unc/%j_%a.out
    #SBATCH --mail-type=BEGIN,END,FAIL
    #SBATCH --mail-user=example_user@unc.edu
    #SBATCH --time=5:00:00

    module add clpipe

    clpipe flywheel_sync -c /proj/hng/study/clpipe/clpipe_config.json -debug -submit

    sleep 5

    # Queue this script to run again next week
    sbatch --begin=now+1week /proj/hng/study/clpipe/scripts/pipeline/flywheel_weekly_ingestion_unc

To submit the script above as a slurm job, run sbatch flywheel_weekly_ingestion_unc in 
the terminal. Note that flywheel_weekly_ingestion is the name of the script.

Be aware that in the script above, the job will be run each week on the day and time 
that you first submit it. For example, if you submit the job at 2:00pm on Wednesday, 
next week's job will also run at 2:00pm on Wednesday of the following week.

Submitting slurm jobs may be different depending on your research institution, so it 
is recommended that you make sure there are no differences in the script above's slurm 
specifications and the standards for your own institution.
