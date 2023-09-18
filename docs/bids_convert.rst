========================
DICOM to BIDs Conversion
========================

*****************
Overview
*****************

clpipe's `convert2bids` commands facilitates the conversion of DICOM files into BIDS
format, using either dcm2bids or heudiconv as your underlying converter.

*****************
Configuration
*****************

**Definitions**

.. autoclass:: clpipe.config.options.Convert2BIDSOptions

The DICOM format string
#################

One important thing to note about using the main command is the need for 
a specifically formatted `dicom_dir_format` option. This is to appropriately map your 
dicom directories to subject/sessions. All subject session folders should be named the 
same way. A dicom_dir_format must contain at least {session} and can contain a 
{subject} formatting option.  Two examples of a dicom_dir_format option 
are `{subject}_{session}/`, which corresponds to the following structure:

.. code-block:: console

    dicom_datadata/
        S01_pre/
            scan1/
            scan2/
            scan3
        S01-post/
            scan1/
            scan2/
            scan3/

Alternatively, you can use `{subject}/{session}/`

.. code-block:: console

    data/
        S01/
            pre/
                scan1/
            post/
                scan1/
        S02/
            pre/
                scan1/
            post/
                scan1/


You can include other text in the formatting option, 
so that the program ignores that text. 
For example, `Subject-{subject}/` used on a dataset with `Subject-01` as a 
folder will determine the subject id to be `01` not `Subject-01`. 
Note that in all examples, there is a trailing forward slash.

dcm2bids configuration
#################

`dcm2bids <https://github.com/UNFmontreal/Dcm2Bids>`_ is a JSON-driven tool for converting DICOM files. 
While not as flexible as heudiconv, dcm2bids is easier to learn and has a
conversion configuration that is simpler to setup and 
modify for users less familiar with programming.

This documentation contains a tutorial for setting up a dcm2bids conversion on the
`Tutorials/BIDS Conversion` page. You can also refer to 
`dcm2bids' tutorial <https://unfmontreal.github.io/Dcm2Bids/3.0.1/tutorial/first-steps>`_ 
for futher help.


The Conversion Config File
---------------------

dcm2bids is driven by a JSON configuration file. clpipe helps you out with this by
generating a starter file for you when you use the project_setup command:

.. literalinclude:: ../clpipe/data/defaultConvConfig.json
   :language: json

The starter demonstrates one anatomical and one functional image conversion configuration,
as well one field map, which references the functional image.

The dcm2niix options are included to allow dcm2bids' search depth to be expanded enough
to work with Flywheel's default file structure when syncing. You can ignore it, but
it serves as a useful place to configure any other dcm2niix options you may need
to specify. dcm2niix is the tool used by dcm2bids to perform DICOM to nifti conversion.


dcm2bids_helper
---------------------
To obtain the information from the header, dcm2bids has a handy helper function:

.. code-block:: console

    usage: dcm2bids_helper [-h] -d DICOM_DIR [DICOM_DIR ...] [-o OUTPUT_DIR]

    optional arguments:
        -h, --help            show this help message and exit
        -d DICOM_DIR [DICOM_DIR ...], --dicom_dir DICOM_DIR [DICOM_DIR ...] DICOM files directory
        -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Output BIDS directory, Default: current directory

            Documentation at https://github.com/cbedetti/Dcm2Bids

This command will create convert an entire folder's data, 
create a temporary directory containing all the converted files, 
and, more importantly, the sidecar JSONs. These JSONs contain the information needed 
to update the conversion configuration file.

heudiconv configuration
#################

`heudiconv <https://heudiconv.readthedocs.io/en/latest/usage.html>`_ is another tool for converting
DICOM files to BIDS format. This tool is a bit trickier to use than dcm2bids, because
its configuration is driven by a python file instead of json. However, it allows for
more control over conversion than what dcm2bids can provide, allowing you to handle
datasets with more variation or difficult edge cases.

See one of these various `walkthroughs <https://heudiconv.readthedocs.io/en/latest/tutorials.html>`_
for instructions on setting up and using heudiconv.

clpipe does not currently provide a default heuristic file - run heudiconv on
your dataset with the converter set to "None" to generate a `.heuristic` folder,
and copy a heuristic file from one of the subject folders to the root of your clpipe
directory. clpipe comes with heudionv installed as a Python library,
so you should be able to use the `heudiconv` command directly 
on the command line if you're in the same virtual environment where you installed clpipe.

To use heudiconv, provide a heuristic file as your conversion config file:

.. code-block:: json
	
	"DICOMToBIDSOptions": {
		"DICOMDirectory": "...<clpipe_project>/data_DICOMs",
		"BIDSDirectory": "...<clpipe_project>/clpipe/data_BIDS",
		"ConversionConfig": "...<clpipe_project>/heuristic.py",
		"DICOMFormatString": "{subject}",

And when running convert2bids, include the `-heudiconv` flag:

.. code-block:: console

    clpipe convert2bids -heudiconv -c config_file.json


*****************
Command
*****************

.. click:: clpipe.cli:convert2bids_cli
	:prog: clpipe convert2bids



