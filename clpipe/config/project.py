from dataclasses import dataclass
import marshmallow_dataclass
import json, yaml, os
from pkg_resources import resource_stream
from .bids import DICOM_to_BIDS, BIDSValidator
from .fmri_prep import FMRIPrep
from .beta_series import BetaSeries
from .roi import ROIOptions
from .source_options import SourceOptions
from .postprocessing import PostProcessing
from .reho import ReHoExtraction
from .t2star import T2StarExtraction

@dataclass
class ProjectConfig:
    #Add variable names exactly same as json file
    ProjectTitle: str
    @property
    def ProjectTitle(self):
        return self._ProjectTitle
    @ProjectTitle.setter
    def ProjectTitle(self, value):
        if value is not None:
            self._ProjectTitle = value

    Authors: str
    @property
    def Authors(self):
        return self._Authors
    @Authors.setter
    def Authors(self, value):
        if value is not None:
            self._Authors = value

    ProjectDirectory: str
    @property
    def ProjectDirectory(self):
        return self._ProjectDirectory
    @ProjectDirectory.setter
    def ProjectDirectory(self, value):
        if value is not None:
            self._ProjectDirectory = value

    EmailAddress: str
    @property
    def EmailAddress(self):
        return self._EmailAddress
    @EmailAddress.setter
    def EmailAddress(self, value):
        if value is not None:
            self._EmailAddress = value

    TempDirectory: str
    @property
    def TempDirectory(self):
        return self._TempDirectory
    @TempDirectory.setter
    def TempDirectory(self, value):
        if value is not None:
            self._TempDirectory = value

    SourceOptions: SourceOptions
    @property
    def SourceOptions(self):
        return self._SourceOptions
    @SourceOptions.setter
    def SourceOptions(self, value):
        if value is not None:
            self._SourceOptions = value

    DICOMToBIDSOptions: DICOM_to_BIDS
    @property
    def DICOMToBIDSOptions(self):
        return self._DICOMToBIDSOptions
    @DICOMToBIDSOptions.setter
    def DICOMToBIDSOptions(self, value):
        if value is not None:
            self._DICOMToBIDSOptions = value

    BIDSValidationOptions: BIDSValidator
    @property
    def BIDSValidationOptions(self):
        return self._BIDSValidationOptions
    @BIDSValidationOptions.setter
    def BIDSValidationOptions(self, value):
        if value is not None:
            self._BIDSValidationOptions = value

    FMRIPrepOptions: FMRIPrep
    @property
    def FMRIPrepOptions(self):
        return self._FMRIPrepOptions
    @FMRIPrepOptions.setter
    def FMRIPrepOptions(self, value):
        if value is not None:
            self._FMRIPrepOptions = value

    PostProcessingOptions: PostProcessing
    @property
    def PostProcessingOptions(self):
        return self._PostProcessingOptions
    @PostProcessingOptions.setter
    def PostProcessingOptions(self, value):
        if value is not None:
            self._PostProcessingOptions = value

    ProcessingStreams: list
    @property
    def ProcessingStreams(self):
        return self._ProcessingStreams
    @ProcessingStreams.setter
    def ProcessingStreams(self, value):
        if value is not None:
            self._ProcessingStreams = value

    BetaSeriesOptions: BetaSeries
    @property
    def BetaSeriesOptions(self):
        return self._BetaSeriesOptions
    @BetaSeriesOptions.setter
    def BetaSeriesOptions(self, value):
        if value is not None:
            self._BetaSeriesOptions = value

    ROIExtractionOptions: ROIOptions
    @property
    def ROIExtractionOptions(self):
        return self._ROIExtractionOptions
    @ROIExtractionOptions.setter
    def ROIExtractionOptions(self, value):
        if value is not None:
            self._ROIExtractionOptions = value

    ReHoExtraction: ReHoExtraction
    @property
    def ReHoExtraction(self):
        return self._ReHoExtraction
    @ReHoExtraction.setter
    def ReHoExtraction(self, value):
        if value is not None:
            self._ReHoExtraction = value

    T2StarExtraction: T2StarExtraction
    @property
    def T2StarExtraction(self):
        return self._T2StarExtraction
    @T2StarExtraction.setter
    def T2StarExtraction(self, value):
        if value is not None:
            self._T2StarExtraction = value

    RunLog: list
    @property
    def RunLog(self):
        return self._RunLog
    @RunLog.setter
    def RunLog(self, value):
        if value is not None:
            self._RunLog = value

    StatusCache: str
    @property
    def StatusCache(self):
        return self._StatusCache
    @StatusCache.setter
    def StatusCache(self, value):
        if value is not None:
            self._StatusCache = value

    BatchConfig: str
    @property
    def BatchConfig(self):
        return self._BatchConfig
    @BatchConfig.setter
    def BatchConfig(self, value):
        if value is not None:
            self._BatchConfig = value

#Add this class to get a ordered dictionary in the dump method
class Meta:
    ordered = True
    
def getProjectConfig(json_file = None, yaml_file = None):
    #Generate schema from given dataclasses
    ConfigSchema = marshmallow_dataclass.class_schema(ProjectConfig)

    if(json_file == None and yaml_file == None):
        # Load default config
        with resource_stream(__name__, '../data/defaultConfig.json') as def_config:
                configDict = json.load(def_config)
    else:
        if(json_file == None and yaml_file):
            with open(yaml_file) as f:
                configDict = yaml.safe_load(f)
        else:
            with open(json_file) as f:
                configDict = json.load(f)
    
    #Change key name to 'Authors'
    newNames = list(configDict.keys())
    newNames[1] = 'Authors'
    configDict = dict(zip(newNames, list(configDict.values())))
    return ConfigSchema().load(configDict)

def dumpProjectConfig(config, outputdir, filepath, yaml_file = False):
    if filepath is None:
            filepath = "defaultConfig.json"
    outpath = os.path.join(os.path.abspath(outputdir), filepath)

    #Generate schema from given dataclasses
    ConfigSchema = marshmallow_dataclass.class_schema(ProjectConfig)
    configDict = ConfigSchema().dump(config)
    
    with open(outpath, 'w') as fp:
            json.dump(configDict, fp, indent="\t")

    if(yaml_file):
        with open('newConfig.json', 'r') as json_in:
            conf = json.load(json_in)
        with open('newConfig.yaml', 'w') as yaml_out:
            yaml.dump(conf, yaml_out, sort_keys=False)
        os.remove('newConfig.json')
    return(outpath)
