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
    #Add variable names exactly same as json file
    BIDSDirectory: str
    WorkingDirectory: str
    OutputDirectory: str
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
    #Add variable names exactly same as json file
    ProjectTitle: str
    Authors: str
    ProjectDirectory: str
    EmailAddress: str
    TempDirectory: str
    DICOMToBIDSOptions: DICOM_to_BIDS
    FMRIPrepOptions: FMRIPrep

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

#Generate schema from given dataclasses
ConfigSchema = marshmallow_dataclass.class_schema(Config)

#Create instance of class with data loaded from json
with open('clpipe_config.json') as f:
    config = ConfigSchema().load(json.load(f))

#Print variables from the different steps
print("TOP LEVEL JSON VARIABLES")
print(config.ProjectTitle)
print(config.ProjectDirectory)
print(config.EmailAddress, '\n')

print("DICOM-TO-BIDS-OPTIONS")
print(config.DICOMToBIDSOptions.DICOMDirectory)
print(config.DICOMToBIDSOptions.ConversionConfig)
print(config.DICOMToBIDSOptions.LogDirectory, '\n')

print("FMRI-PREP_OPTIONS")
print(config.FMRIPrepOptions.OutputDirectory)
print(config.FMRIPrepOptions.TemplateFlowToggle)
print(config.FMRIPrepOptions.FMapCleanupROIs, '\n')

#Edit Variables
config.ProjectTitle = "Config Generation Project"
config.DICOMToBIDSOptions.DICOMDirectory = os.getcwd()
config.FMRIPrepOptions.FMapCleanupROIs = 5

#Serialization
newConfig_json = ConfigSchema().dump(config)
#This process can be edited so the formatting can match the default config format
with open('new-clpipeConfig.json', 'w') as f:
    json.dump(newConfig_json, f)
    