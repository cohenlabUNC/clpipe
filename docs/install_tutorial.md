# Project Setup

## Installation and Folder Setup

First, [install clpipe](https://clpipe.readthedocs.io/en/latest/install.html) using pip and Github

```
pip3 install --upgrade git+https://github.com/cohenlabUNC/clpipe.git
```

Create a new folder for your project

```
mkdir clpipe_tutorial_project
cd clpipe_tutorial_project
```

To run the project setup, you need to have a source data directory prepared. For now, please create an empty one.

```
mkdir data_DICOMs
```

Now you are ready to run the [project_setup](https://clpipe.readthedocs.io/en/latest/project_setup.html) command

## Running project_setup

```
project_setup -project_title clpipe_tutorial_project -project_dir . -source_data data_DICOMs
```

If successful, your folder will now contain the following structure:

```      
.
├── analyses
├── clpipe_config.json
├── conversion_config.json
├── data_BIDS
├── data_DICOMs
├── data_fmriprep
├── data_GLMPrep
├── data_onsets
├── data_postproc
├── data_ROI_ts
├── glm_config.json
├── l1_feat_folders
├── l1_fsfs
├── l2_fsfs
├── l2_gfeat_folders
├── l2_sublist.csv
├── logs
└── scripts
```

clpipe automatically creates many of the directories we will need in the future. For now, let's just familiarize ourselves with the most important file, `clpipe_config.json`, which allows you to configure clpipe's core functionalities. Open `clpipe_config.json` with the editor of your choice.

## Understanding the clpipe_config.json File

There is quite a bit going on in this file, because it controls most of clpipe's processing options. As a `.json` file, this configuration is organized as a collection of key/value pairs, such as:

```
"ProjectTitle": "A Neuroimaging Project"
```

The key here is "ProjectTitle", an attribute corresponding to the project's name, and the value is "A Neuroimaging Project", the name of the project.

Examine the first few lines of the file, which contain metadata about your project:

```
"ProjectTitle": "clpipe_tutorial_project",
"Authors/Contributors": "",
"ProjectDirectory": "<your system's path>/clpipe_tutorial_project",
"EmailAddress": "",
"TempDirectory": "",
```

Notice that the project directory and title have already been filled in by clpipe.

Let's make our first configuration change by setting your name as the author, and providing your email address -

```
"ProjectTitle": "clpipe_tutorial_project",
"Authors/Contributors": "Your Name Here",
"ProjectDirectory": "/nas/longleaf/home/willasc/data/clpipe/clpipe_tutorial_project",
"EmailAddress": "myemail@domain.com",
"TempDirectory": "",
```

Values in a key/value pair are not just limited to text - we can also have a list of more key/value pairs, which allows for hierarchial structures:

```
"top-level-key": {
	"key1":"value",
	"key2":"value",
	"key3":"value"
}
```

The options for clpipe's various processing steps, such as "DICOMToBIDSOptions", follow this structure:

```
"DICOMToBIDSOptions": {
	       

"DICOMToBIDSOptions": {
 "DICOMDirectory": "<your system's path>/clpipe_tutorial_project/data_DICOMs",
 "BIDSDirectory": "<your system's path>/clpipe_tutorial_project/data_BIDS",
 "ConversionConfig": "<your system's path>/clpipe_tutorial_project/conversion_config.json",
 "DICOMFormatString": "",
 "TimeUsage": "1:0:0",
 "MemUsage": "5000",
 "CoreUsage": "2",
 "LogDirectory": "<your system's path>/clpipe_tutorial_project/logs/DCM2BIDS_logs"
 }
}
```

We will go over these processing step options in the following tutorial