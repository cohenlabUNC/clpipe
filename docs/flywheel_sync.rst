===========================
Flywheel Sync
===========================

clpipe now provides an avenue for syncing DICOM data with a remote source through
the ``clpipe flywheel_sync`` command.

-------------------------------
Setup
-------------------------------

First, the Flywheel CLI must be installed to make use of this command. For UNC-CH users, Flywheel should
be automatically loaded as a module when the clpipe module is loaded. If you need to
install Flywheel, you can find a link to the installer in your profile on the
Flywheel web app.

You will also need to login to Flywheel via the Flywheel CLI to use this command.
Navigate to the Flywheel web app. In the upper right, click on your profile drop down menu, select 'profile'.
Scroll down and copy the command under 'Getting Started With the CLI.' It should look like: ``login <FLYWHEEL URL>::<TOKEN>``. 
Run this command to login.

Finally, ``flywheel_sync`` requires the insertion of a new option block into your clpipe_config.json
file, specifying the Flywheel path you wish to sync from, where these files should go,
and your batch configuration:

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


flywheel_sync Options
----------------

.. autoclass:: clpipe.config.project.SourceOptions

.. click:: clpipe.cli:flywheel_sync_cli
	:prog: clpipe flywheel_sync
	:nested: full

-------------------------------
Using with convert2bids
-------------------------------

Flywheel creates a DICOM folder structure that is too deep for the
default depth setting of dcm2niix, which both dcm2bids and heudiconv use to discover
DICOM files in your source directory. However, dcm2niix can be configured to search
deeper with the ``-d`` option:

 
dcm2bids (clpipe default)
----------------

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

heudiconv
----------------

By default, heudiconv sets the search depth of dcm2niix high enough to find 
DICOM files within Flywheel's output structure, so no changes are required if you
use this converter.


-------------------------------
Additional Notes
-------------------------------

This command creates its own log folder at ``<project>/logs/sync_logs``

One quirk of Flywheel's sync command is that it creates a strangely named temporary directory at
the currently working directory, which is empty after the sync is finished. clpipe
removes this folder automatically.