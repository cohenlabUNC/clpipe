===========================
DICOM Sync - NEW
===========================

clpipe now provides an avenue for syncing DICOM data with a remote source through
the `clpipe dicom sync` command.

Currently, only Flywheel is supported as a remote source.

This command uses the same configuration options as DICOM to BIDS conversion,
including for batch configuration options. Options for sync will likely be given their
own configuration block in a future release.

`clpipe dicom sync` does require one additional option, SourceURL, denoting
the remote location of the DICOM data to sync with:

.. code-block :: json
   
	"DICOMToBIDSOptions": {
            "DICOMDirectory": "",
            "SourceURL": "fw://<LAB>/<PROJECT>/",
            "BIDSDirectory": "",
            "ConversionConfig": "",
            "DICOMFormatString": "",
            "TimeUsage": "1:0:0",
            "MemUsage": "5000",
            "CoreUsage": "2",
            "LogDirectory": ""
	},
    

This command creates its own log folder at `<project>/logs/sync_logs`

One quirk of Flywheel's sync command is that it creates a strangely named temporary directory at
the currently working directory, which is empty after the sync is finished. clpipe
removes this folder automatically.

.. click:: clpipe.cli:sync_cli
	:prog: clpipe dicom sync
	:nested: full