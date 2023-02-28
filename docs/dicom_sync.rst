===========================
Flywheel Sync
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
		"DropoffDirectory": "path/to/your/dicom_folder",
		"TimeUsage": "1:0:0",
		"MemUsage": "10000",
		"CoreUsage": "1"
	},


.. click:: clpipe.cli:flywheel_sync_cli
	:prog: clpipe dicom flywheel_sync
	:nested: full

-------------------------------
Additional Notes
-------------------------------

This command creates its own log folder at `<project>/logs/sync_logs`

One quirk of Flywheel's sync command is that it creates a strangely named temporary directory at
the currently working directory, which is empty after the sync is finished. clpipe
removes this folder automatically.