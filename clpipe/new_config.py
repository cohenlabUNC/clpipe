from dataclasses import dataclass
import marshmallow_dataclass
import json, os

"""
Variable 2 of the top level JSON is supposed to be 'Authors/Contributors'. The '/' is an issue
and does not allow the deserialization to happen. This can either be manually changed during
serialization and deserialization.
Currently, I edited the JSON file to make it 'Authors' and it works fine.
This can be done by changing the key name to 'Authors' before loading data from dictionary
and then changing the key name back to 'Authors/Contributors' before sumping into JSON
"""

@dataclass
class DICOM_to_BIDS:
    #Add variable names exactly same as json file
    DICOMDirectory: str
    BIDSDirectory: str
    ConversionConfig: str
    DICOMFormatString: str
    TimeUsage: str #Can be diff data type?
    MemUsage: str #Can be diff data type?
    CoreUsage: str #Can be diff data type?
    LogDirectory: str

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class FMRIPrep:
    """
    Configuration options for fmriprep.
    """
    #Add variable names exactly same as json file
    BIDSDirectory: str #: The target BIDS directory
    WorkingDirectory: str 
    """A directory to store intermediary
    processing files - recommend a temporary location, as
    this folder can grow very large!"""
    OutputDirectory: str #: Output location of your fmriprepped images.
    FMRIPrepPath: str
    FreesurferLicensePath: str
    CommandLineOpts: str
    TemplateFlowToggle: bool
    TemplateFlowPath: str
    TemplateFlowTemplates: list
    FMapCleanupROIs: int
    FMRIPrepMemoryUsage: str
    FMRIPrepTimeUsage: str
    NThreads: str
    LogDirectory: str
    DockerToggle: bool
    DockerFMRIPrepVersion: str
    UseAROMA: bool

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class Config:
    """clpipe's top-level configuration options.
    """    
    #Add variable names exactly same as json file
    
    Authors: str #: The maintainers of your clpipe project.
    ProjectDirectory: str #: The root directory of your clpipe project.
    EmailAddress: str #: Email address to be submitted to slurm.
    TempDirectory: str
    DICOMToBIDSOptions: DICOM_to_BIDS
    FMRIPrepOptions: FMRIPrep
    ProjectTitle: str = "A Neuroimaging Project" #: The title of your clpipe project.

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True
    