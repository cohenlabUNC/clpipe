from dataclasses import dataclass, field
import marshmallow_dataclass
import json, yaml, os
from pathlib import Path
from pkg_resources import resource_stream
from .bids import Convert2BIDSOptions, BIDSValidatorOptions
from .fmriprep import FMRIPrepOptions
from .beta_series import BetaSeriesOptions
from .postprocessing import PostProcessingOptions
from .roi import ROIExtractionOptions
from .source_options import SourceOptions
from .reho import ReHoExtractionOptions
from .t2star import T2StarExtractionOptions

@dataclass
class PipelineConfig:
    project_title: str = ""
    contributors: str = ""
    project_directory: str = ""
    email_address: str = ""
    source: SourceOptions = SourceOptions()
    convert2bids: Convert2BIDSOptions = Convert2BIDSOptions()
    bids_validation: BIDSValidatorOptions = BIDSValidatorOptions()
    fmriprep: FMRIPrepOptions = FMRIPrepOptions()
    postprocessing: PostProcessingOptions = PostProcessingOptions()
    processing_streams: list = field(default_factory=list)
    batch_config_path: str = ""
    version: str = ""

    def to_dict(self):
        #Generate schema from given dataclasses
        ConfigSchema = marshmallow_dataclass.class_schema(self.__class__)
        return ConfigSchema().dump(self)

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True
    
def load_pipeline_config(json_file = None, yaml_file = None):
    #Generate schema from given dataclasses
    config_schema = marshmallow_dataclass.class_schema(PipelineConfig)

    if(json_file == None and yaml_file == None):
        # Load default config
        with resource_stream(__name__, '../data/defaultConfig.json') as def_config:
                config_dict = json.load(def_config)
    else:
        if(json_file == None and yaml_file):
            with open(yaml_file) as f:
                config_dict = yaml.safe_load(f)
        else:
            with open(json_file) as f:
                config_dict = json.load(f)

    if 'version' not in config_dict:
        config_dict = convert_project_config(config_dict)    
    
    newNames = list(config_dict.keys())
    config_dict = dict(zip(newNames, list(config_dict.values())))
    return config_schema().load(config_dict)

def dump_project_config(config, outputdir, file_name="project_config", yaml_file = False):
    outpath = Path(outputdir) / file_name

    #Generate schema from given dataclasses
    ConfigSchema = marshmallow_dataclass.class_schema(PipelineConfig)
    config_dict = ConfigSchema().dump(config)

    outpath_json = outpath.parent / (outpath.name + '.json')
    
    with open(outpath_json, 'w') as fp:
        json.dump(config_dict, fp, indent="\t")

    if(yaml_file):
        outpath_yaml = outpath.parent / (outpath.name + '.yaml')
        with open(outpath_json, 'r') as json_in:
            conf = json.load(json_in)
        with open(outpath_yaml, 'w') as yaml_out:
            yaml.dump(conf, yaml_out, sort_keys=False)
        os.remove(outpath_json)

        return outpath_yaml
    
    return outpath_json

def convert_project_config(old_config, new_config=None):
    """
    Old Config:
        - Wrong Order - FIXED
        - Extra Fields - FIXED - Needs to be dealt with by user
        - Lack of Fields - FIXED
        - Wrong datatype in value - NOT FIXED
        - Different name for keys - Maybe use fuzzy string matching? Might not be worth it tho
        - Nested Fields - FIXED - Some nested fields are lists of dictionaries. 
            This wont get sorted. Can maybe try coding it
    """
    if not new_config:
        new_config = PipelineConfig().to_dict()
    schema_keys = list(new_config.keys())

    for key in schema_keys:
        if(old_config.get(KEY_MAP[key]) != None):
            if(isinstance(new_config[key], dict)):
                old_config[KEY_MAP[key]] = convert_project_config(old_config[KEY_MAP[key]], new_config[key])
                del old_config[KEY_MAP[key]]
                continue
            else:
                new_config[key] = old_config[KEY_MAP[key]]
                del old_config[KEY_MAP[key]]
                continue
        else:
            #If old config doesnt have key, then just continue because new config will have default value
            continue
    return new_config

KEY_MAP = {
    "version": "version",
    "project_title": "ProjectTitle",
    "contributors": "Authors/Contributors",
    "project_directory": "ProjectDirectory",
    "email_address": "EmailAddress",
    "source": "SourceOptions",
    "source_url": "SourceURL",
    "dropoff_directory": "DropoffDirectory",
    "temp_directory": "TempDirectory",
    "commandline_opts": "CommandLineOpts",
    "time_usage": "TimeUsage",
    "mem_usage": "MemUsage",
    "core_usage": "CoreUsage",
    "convert2bids": "DICOMToBIDSOptions",
    "dicom_directory": "DICOMDirectory",
    "bids_directory": "BIDSDirectory",
    "conversion_config": "ConversionConfig",
    "dicom_format_string": "DICOMFormatString",
    "bids_validation": "BIDSValidationOptions",
    "bids_validator_image": "BIDSValidatorImage",
    "log_directory": "LogDirectory",
    "fmriprep": "FMRIPrepOptions",
    "working_directory": "WorkingDirectory",
    "output_directory": "OutputDirectory",
    "fmriprep_path": "FMRIPrepPath",
    "freesurfer_license_path": "FreesurferLicensePath",
    "use_aroma": "UseAROMA",
    "templateflow_toggle": "TemplateFlowToggle",
    "templateflow_path": "TemplateFlowPath",
    "templateflow_templates": "TemplateFlowTemplates",
    "fmap_roi_cleanup": "FMapCleanupROIs",
    "fmriprep_memory_usage": "FMRIPrepMemoryUsage",
    "fmriprep_time_usage": "FMRIPrepTimeUsage",
    "n_threads": "NThreads",
    "docker_toggle": "DockerToggle",
    "docker_fmriprep_version": "DockerFMRIPrepVersion",
    "postprocessing": "PostProcessingOptions",
    "write_process_graph": "WriteProcessGraph",
    "target_directory": "TargetDirectory",
    "target_image_space": "TargetImageSpace",
    "target_tasks": "TargetTasks",
    "target_acquisitions": "TargetAcquisitions",
    "processing_steps": "ProcessingSteps",
    "processing_step_options": "ProcessingStepOptions",
    "temporal_filtering": "TemporalFiltering",
    "implementation": "Implementation",
    "filtering_high_pass": "FilteringHighPass",
    "filtering_low_pass": "FilteringLowPass",
    "filtering_order": "FilteringOrder",
    "intensity_normalization": "IntensityNormalization",
    "spatial_smoothing": "SpatialSmoothing",
    "fwhm": "FWHM",
    "aroma_regression": "AROMARegression",
    "scrub_timepoints": "ScrubTimepoints",
    "resample": "Resample",
    "reference_image": "ReferenceImage",
    "trim_timepoints": "TrimTimepoints",
    "from_end": "FromEnd",
    "from_beginning": "FromBeginning",
    "confound_regression": "ConfoundRegression",
    "confound_options": "ConfoundOptions",
    "columns": "Columns",
    "motion_outliers": "MotionOutliers",
    "include": "Include",
    "scrub_var": "ScrubVar",
    "threshold": "Threshold",
    "scrub_ahead": "ScrubAhead",
    "scrub_behind": "ScrubBehind",
    "scrub_contiguous": "ScrubContiguous",
    "batch_options": "BatchOptions",
    "memory_usage": "MemoryUsage",
    "beta_series": "BetaSeriesOptions",
    "target_suffix": "TargetSuffix",
    "output_suffix": "OutputSuffix",
    "confound_suffix": "ConfoundSuffix",
    "regress": "Regress",
    "nuisance_regression": "NuisanceRegression",
    "white_matter": "WhiteMatter",
    "csf": "CSF",
    "global_signal_regression": "GlobalSignalRegression",
    "task_specific_options": "TaskSpecificOptions",
    "task": "Task",
    "exclude_column_info": "ExcludeColumnInfo",
    "exclude_trial_types": "ExcludeTrialTypes",
    "processing_streams": "ProcessingStreams",
    "processing_stream": "ProcessingStream",
    "roi_extract": "ROIExtractionOptions",
    "atlases": "Atlases",
    "require_mask": "RequireMask",
    "prop_voxels": "PropVoxels",
    "reho_extraction": "ReHoExtraction",
    "exclusion_file": "ExclusionFile",
    "mask_directory": "MaskDirectory",
    "mask_suffix": "MaskSuffix",
    "mask_file_override": "MaskFileOverride",
    "neighborhood": "Neighborhood",
    "t2_star_extraction": "T2StarExtraction",
    "batch_config_path": "BatchConfig"
}