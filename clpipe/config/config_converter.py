import json
import os

"""
Old Config:
    - Wrong Order - FIXED
    - Extra Fields - FIXED - Needs to be dealt with by user
    - Lack of Fields - FIXED
    - Wrong datatype in value - NOT FIXED
    - Different name for keys - Maybe use fuzzy string matching? Might not be worth it tho
    - Nested Fields - FIXED - Some nested fields are lists of dictionaries. This wont get sorted. Can maybe try coding it
"""

def convertConfig(oldConf, newConf):
    schemaKeys = list(newConf.keys())

    for key in schemaKeys:
        if(oldConf.get(key_map[key]) != None):
            if(isinstance(newConf[key], dict)):
                oldConf[key_map[key]] = convertConfig(oldConf[key_map[key]], newConf[key])
                del oldConf[key_map[key]]
                continue
            else:
                newConf[key] = oldConf[key_map[key]]
                del oldConf[key_map[key]]
                continue
        else:
            #If old config doesnt have key, then just continue because new config will have default value
            continue
    return newConf

key_map = {
    "project_title": "ProjectTitle",
    "contributors": "Authors/Contributors",
    "project_directory": "ProjectDirectory",
    "email_address": "EmailAddress",
    "source_options": "SourceOptions",
    "source_url": "SourceURL",
    "dropoff_directory": "DropoffDirectory",
    "temp_directory": "TempDirectory",
    "commandline_opts": "CommandLineOpts",
    "time_usage": "TimeUsage",
    "mem_usage": "MemUsage",
    "core_usage": "CoreUsage",
    "convert2bids_options": "DICOMToBIDSOptions",
    "dicom_directory": "DICOMDirectory",
    "bids_directory": "BIDSDirectory",
    "conversion_config": "ConversionConfig",
    "dicom_format_string": "DICOMFormatString",
    "bids_validation_options": "BIDSValidationOptions",
    "bids_validator_image": "BIDSValidatorImage",
    "log_directory": "LogDirectory",
    "fmriprep_options": "FMRIPrepOptions",
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
    "postprocessing_options": "PostProcessingOptions",
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
    "beta_series_options": "BetaSeriesOptions",
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
    "roi_extract_options": "ROIExtractionOptions",
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