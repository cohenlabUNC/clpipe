from dataclasses import dataclass
import marshmallow_dataclass
import json, yaml, os
from pkg_resources import resource_stream
from .bids import Convert2BIDS, BIDSValidator
from .fmriprep import FMRIPrep
from .beta_series import BetaSeries
from .postprocessing import PostProcessing
from .roi import ROIOptions
from .source_options import SourceOptions
from .postprocessing import PostProcessingConfig
from .reho import ReHoExtraction
from .t2star import T2StarExtraction

@dataclass
class ProjectConfig:
    project_title: str
    authors: str
    project_directory: str
    email_address: str
    source: SourceConfig
    convert2bids: Convert2BIDSConfig
    bids_validation: BIDSValidatorConfig
    fmriprep: FMRIPrepConfig
    postprocessing: PostProcessingConfig
    beta_series: BetaSeriesConfig
    processing_streams: list
    roi_extraction: ROIExtractionConfig
    reho_extraction: ReHoExtractionConfig
    t2_star_extraction: T2StarExtractionConfig
    batch_config_path: str

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
