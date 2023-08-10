from dataclasses import dataclass, field
import marshmallow_dataclass
import json, yaml, os
from pathlib import Path
from pkg_resources import resource_stream

@dataclass
class SourceOptions:
    source_url: str = ""
    dropoff_directory: str = ""
    temp_directory: str = ""
    commandline_opts: str = ""
    time_usage: str = ""
    mem_usage: str = ""
    core_usage: str = ""

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class Convert2BIDSOptions:
    #Add variable names exactly same as json file
    dicom_directory: str = ""
    bids_directory: str = ""
    conversion_config: str = ""
    dicom_format_string: str = ""
    time_usage: str = ""
    mem_usage: str = ""
    core_usage: str = ""
    log_directory: str = ""

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class BIDSValidatorOptions:
    bids_validator_image: str = ""
    log_directory: str = ""
    
    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class FMRIPrepOptions:
    #Add variable names exactly same as json file
    bids_directory: str = ""
    working_directory: str = ""
    output_directory: str = ""
    fmriprep_path: str = ""
    freesurfer_license_path: str = ""
    use_aroma: bool = False
    commandline_opts: str = ""
    templateflow_toggle: bool = True
    templateflow_path: str = ""
    templateflow_templates: list = field(default_factory=list)
    fmap_roi_cleanup: int = 3
    fmriprep_memory_usage: str = ""
    fmriprep_time_usage: str = ""
    n_threads: str = ""
    log_directory: str = ""
    docker_toggle: bool = False
    docker_fmriprep_version: str = ""
    
    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

from dataclasses import dataclass, field

DEFAULT_PROCESSING_STREAM = "default"

@dataclass
class TemporalFiltering:
    implementation: str = ""
    filtering_high_pass: float = 0.0
    filtering_low_pass: int = 0
    filtering_order: int = 0

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class IntensityNormalization:
    implementation: str = ""

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class SpatialSmoothing:
    implementation: str = ""
    fwhm: int = 0

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class AROMARegression:
    implementation: str = ""

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class ScrubTimepoints:
    target_variable: str = ""
    threshold: float = 0.0
    scrub_ahead: int = 0
    scrub_behind: int = 0
    scrub_contiguous: int = 0
    insert_na: bool = False


@dataclass
class Resample:
    reference_image: str = ""

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class TrimTimepoints:
    from_end: int = 0
    from_beginning: int = 0
    
    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class ConfoundRegression:
    implementation: str = ""

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class ProcessingStepOptions:
    temporal_filtering: TemporalFiltering = TemporalFiltering()
    intensity_normalization: IntensityNormalization = IntensityNormalization()
    spatial_smoothing: SpatialSmoothing = SpatialSmoothing()
    aroma_regression: AROMARegression = AROMARegression()
    scrub_timepoints: ScrubTimepoints = ScrubTimepoints()
    resample: Resample = Resample()
    trim_timepoints: TrimTimepoints = TrimTimepoints()
    confound_regression: ConfoundRegression = ConfoundRegression()

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class MotionOutliers:
    include: bool = False
    scrub_var: str = "framewise_displacement"
    threshold: float = 0.0
    scrub_ahead: int = 0
    scrub_behind: int = 0
    scrub_contiguous: int = 0

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class ConfoundOptions:
    columns: list = field(default_factory=list)
    motion_outliers: MotionOutliers = MotionOutliers()

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class BatchOptions:
    memory_usage: str = ""
    time_usage: str = ""
    n_threads: str = ""

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class PostProcessingOptions:
    working_directory: str = ""
    write_process_graph: bool = True
    target_directory: str = ""
    target_image_space: str = ""
    target_tasks: list = field(default_factory=list)
    target_acquisitions: list = field(default_factory=list)
    output_directory: str = field(default_factory=list)
    processing_steps: list = field(default_factory=list)
    processing_step_options: ProcessingStepOptions = ProcessingStepOptions()
    confound_options: ConfoundOptions = ConfoundOptions()
    batch_options: BatchOptions = BatchOptions()

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class ProjectOptions:
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
    
def load_project_config(json_file = None, yaml_file = None):
    #Generate schema from given dataclasses
    config_schema = marshmallow_dataclass.class_schema(ProjectOptions)

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
    ConfigSchema = marshmallow_dataclass.class_schema(ProjectOptions)
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
        new_config = ProjectOptions().to_dict()
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
    "batch_config_path": "BatchConfig",
    "target_variable": "TargetVariable",
    "insert_na": "InsertNA",
}