===========================
Flywheel Sync - NEW
===========================

clpipe now provides an avenue for syncing DICOM data with a remote source through
the `clpipe dicom flywheel_sync` command.

-------------------------------
Setup
-------------------------------

First, the Flywheel CLI must be installed to make use of this command. For UNC-CH users, Flywheel should
be automatically loaded as a module when the clpipe module is loaded. If you need to
install Flywheel, you can find a link to the installer in your profile on the
Flywheel web app.

You will also need to login to Flywheel via the Flywheel CLI to use this command.
Navigate to the Flywheel web app. In the upper right, click on your profile drop down menu, select 'profile'.
Scroll down and copy the command under 'Getting Started With the CLI.' It should look like: 'login <FLYWHEEL URL>::<TOKEN>'. 
Run this command to login.

Finally, `flywheel_sync` requires the insertion of a new option block into your clpipe_config.json
file, specifying the Flywheel path you wish to sync from, where these files should go,
and your batch configuration:

.. code-block :: json
   
	"SourceOptions": {
		"SourceURL": "fw://<LAB>/<STUDY>/",
		"DropoffDirectory": "/path/to/your/dicom_folder",
		"TempDirectory": "/path/to/a/temp_folder",
		"CommandLineOpts": "",
		"TimeUsage": "1:0:0",
		"MemUsage": "10000",
		"CoreUsage": "1"
	},


flywheel_sync Options
----------------

* ``SourceOptions:`` Options regarding remote data sources.

    * ``SourceURL:`` The URL to your source data - for Flywheel this should start with `fw:` and point to a project. You can use `fw ls` to browse your fw project space to find the right path.
    * ``DropoffDirectory:`` A destination for your synced data - usually this will be `data_DICOMs`
    * ``TempDirectory`` A location for Flywheel to store its temporary files - necessary on shared compute, because Flywheel will use system level tmp space by default, which can cause issues.
    * ``CommandLineOpts:`` Any additional options you may need to include - you can browse Flywheel sync's other options with `fw sync --help`


.. click:: clpipe.cli:flywheel_sync_cli
	:prog: clpipe dicom flywheel_sync
	:nested: full

-------------------------------
Using with convert2bids
-------------------------------

Unfortunately, Flywheel creates a DICOM folder structure that is too deep for the
default depth setting of dcm2niix, which both dcm2bids and heudiconv use to discover
DICOM files in your source directory.

To fix this issue, you must pass through the argument `-d 9` to dcm2niix, which
sets the default search depth to the maximum.

 
dcm2bids (clpipe default)
----------------

You can set the depth flag with dcm2bids by copying the `dcm2niixOptions`
key to your conversion_config.json file, like this:

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

heudiconv
----------------

By default, heudiconv searches deeply enough to find DICOM files within Flywheel's
output structure.


-------------------------------
Additional Notes
-------------------------------

This command creates its own log folder at `<project>/logs/sync_logs`

One quirk of Flywheel's sync command is that it creates a strangely named temporary directory at
the currently working directory, which is empty after the sync is finished. clpipe
removes this folder automatically.