from dataclasses import dataclass, field
from typing import List
import marshmallow_dataclass
import json, yaml, os
from pathlib import Path
from .package import VERSION

DEFAULT_PROCESSING_STREAM = "default"

class Option:
    """Parent option class for configuring global settings.
    
    Unfortunately, giving this class the @dataclass decorator does not seem to
    pass functionality to child classes, even with super.init()
    """
    class Meta:
        ordered = True
        """Ensures config retains source order when dumped to file."""

    def load_cli_args(self, **kwargs):
        """Override class fields with inputted arguments if they aren't None"""

        for arg_name, arg_value in kwargs.items():
            if arg_value is not None:
                setattr(self, arg_name, arg_value)


@dataclass
class SourceOptions(Option):
    """Options for configuring sources of DICOM data."""

    source_url: str = "fw://"
    """The URL to your source data - for Flywheel this should start with fw: 
    and point to a project. You can use fw ls to browse your fw project space 
    to find the right path."""

   
    dropoff_directory: str = ""
    """A destination for your synced data - usually this will be data_DICOMs"""
    
    temp_directory: str = ""
    """A location for Flywheel to store its temporary files - 
    necessary on shared compute, because Flywheel will use system 
    level tmp space by default, which can cause issues."""
    
    commandline_opts: str = "-y"
    """Any additional options you may need to include - 
    you can browse Flywheel syncs other options with fw sync -help"""

    time_usage: str = "1:0:0"
    mem_usage: str = "10G"
    core_usage: str = "1"


@dataclass
class Convert2BIDSOptions(Option):
    """Options for converting DICOM files to BIDS format."""
    
    dicom_directory: str = ""
    """Path to your source DICOM directory to be converted."""

    bids_directory: str = ""
    """Output directory where your BIDS data will be saved."""

    conversion_config: str = ""
    """The path to your conversion configuration file - either a
    conversion_config.json file for dcm2bids, or heuristic.py for heudiconv."""

    dicom_format_string: str = ""
    """Used to tell clpipe where to find subject and session level folders in you
    DICOM directory."""

    time_usage: str = "1:0:0"
    mem_usage: str = "5000"
    core_usage: str = "2"
    log_directory: str = ""


    def populate_project_paths(self, project_directory: os.PathLike, source_data: os.PathLike):
        self.dicom_directory = os.path.abspath(source_data)
        self.conversion_config = os.path.join(project_directory, 'conversion_config.json')
        self.bids_directory = os.path.join(project_directory, 'data_BIDS')
        self.log_directory = os.path.join(project_directory, "logs", "DCM2BIDS_logs")


@dataclass
class BIDSValidatorOptions(Option):
    """Options for validating your BIDS directory."""

    bids_validator_image: str = "/proj/hng/singularity_imgs/validator.simg"
    """Path to your BIDS validator image."""
    
    log_directory: str = ""

    def populate_project_paths(self, project_directory: os.PathLike):
        self.log_directory = os.path.join(project_directory, "logs", "bids_validation_logs")


@dataclass
class FMRIPrepOptions(Option):
    """Options for configuring fMRIPrep."""

    bids_directory: str = "" 
    """Your BIDs formatted raw data directory."""

    working_directory: str = "SET WORKING DIRECTORY"
    """Storage location for intermediary fMRIPrep files. Takes up a large
    amount of space - Longleaf users should use their /work folder."""

    
    output_directory: str = "" 
    """ Where to save your preprocessed images. """

    fmriprep_path: str = "/proj/hng/singularity_imgs/fmriprep_22.1.1.sif"
    """Path to your fMRIPrep Singularity image."""
    
    freesurfer_license_path: str = "/proj/hng/singularity_imgs/license.txt"
    """Path to your Freesurfer license .txt file."""
    
    use_aroma: bool = False
    """Set True to generate AROMA artifacts. Significantly increases run
    time and memory usage."""
    
    commandline_opts: str = ""
    """Any additional arguments to pass to FMRIprep."""
    
    templateflow_toggle: bool = True
    """Set True to activate to use templateflow, which allows you to
    generate multiple template variantions for the same outputs."""
    
    templateflow_path: str = "/proj/hng/singularity_imgs/template_flow"
    """The path to your templateflow directory."""

    templateflow_templates: list = field(
        default_factory=lambda: [
            "MNI152NLin2009cAsym", 
            "MNI152NLin6Asym", 
            "OASIS30ANTs", 
            "MNIPediatricAsym", 
            "MNIInfant"]
        )
    """Which templates (standard spaces) should clpipe download for use in templateflow?"""

    fmap_roi_cleanup: int = 3
    """How many timepoints should the fmap_cleanup function extract from 
    blip-up/blip-down field maps, set to -1 to disable."""
    
    fmriprep_memory_usage: str = "50G"
    """How much memory in RAM each subject's preprocessing will use."""

    fmriprep_time_usage: str = "16:0:0"
    """How much time on the cluster fMRIPrep is allowed to use."""
    
    n_threads: str = "12"
    """How many threads to use in each job."""

    log_directory: str = ""
    """Path to your logging directory for fMRIPrep outputs.
    Not generally changed from default."""

    docker_toggle: bool = False
    """Set True to use a Docker image."""
    
    docker_fmriprep_version: str = ""
    """Path to your fMRIPrep Docker image."""

    def populate_project_paths(self, project_directory: os.PathLike):
        self.bids_directory = os.path.join(project_directory, "data_BIDS")
        self.output_directory = os.path.join(project_directory, 'data_fmriprep')
        self.log_directory = os.path.join(project_directory, 'logs', 'FMRIprep_logs')


@dataclass
class TemporalFiltering(Option):
    """This step removes signals from an image's timeseries based on cutoff thresholds.
    Also applied to confounds."""

    implementation: str = "fslmaths"
    """Available implementations: fslmaths, 3dTProject"""

    filtering_high_pass: float = 0.008
    """Values below this threshold are filtered. Defaults to .08 Hz. Set to -1 to disable."""

    filtering_low_pass: int = -1
    """Values above this threshold are filtered. Disabled by default (-1)."""
    
    filtering_order: int = 2
    """Order of the filter. Defaults to 2."""


@dataclass
class IntensityNormalization(Option):
    """Normalize the intensity of the image data."""

    implementation: str = "10000_GlobalMedian"
    """Currently limited to '10000_GlobalMedian'"""


@dataclass
class SpatialSmoothing(Option):
    """Apply spatial smoothing to the image data."""

    implementation: str = "SUSAN"
    """Currently limited to 'SUSAN'"""
    fwhm: int = 6
    """The size of the smoothing kernel.
    Specifically the full width half max of the Gaussian kernel.
    Scaled in millimeters."""


@dataclass
class AROMARegression(Option):
    """Regress out automatically classified noise artifacts from the image data
    using AROMA. Also applied to confounds."""
    implementation: str = "fsl_regfilt"


@dataclass
class ScrubTimepoints(Option):
    """This step can be used to remove timepoints from the image timeseries
    based on a target variable from that image's confounds file. Timepoints scrubbed
    from an image's timeseries are also removed its respective confound file."""

    insert_na: bool = True
    """Set true to replace scrubbed timepoints with NA. False removes the timepoints completely."""

    scrub_columns: list = field(
        default_factory=lambda: [
            ScrubColumn(target_variable="cosine*", threshold=100.0, scrub_ahead=0, scrub_behind=0, scrub_contiguous=0),
            ScrubColumn(target_variable="framewise_displacement", threshold=0.2, scrub_ahead=0, scrub_behind=0, scrub_contiguous=0)
            ]
        )
    """A list of columns to be scrubbed."""


@dataclass 
class ScrubColumn(Option):
    """A definition for a single column to be scrubbed."""

    target_variable: str = "framewise_displacement"
    """Which confound variable to use as a reference for scrubbing. May use wildcard (*) to select multiple similar columns."""

    threshold: float = 0.9
    """Any timepoint of the target variable exceeding this value will be scrubbed"""

    scrub_ahead: int = 0
    """Set the number of timepoints to scrub ahead of target timepoints"""

    scrub_behind: int = 0
    """Set the number of timepoints to scrub behind target timepoints"""

    scrub_contiguous: int = 0
    """Scrub everything between scrub targets up to this far apart"""


@dataclass
class Resample(Option):
    """Resample your image to a new space."""
    
    reference_image: str = "SET REFERENCE IMAGE"
    """Path to an image against which to resample - often a template"""


@dataclass
class TrimTimepoints(Option):
    """Trim timepoints from the beginning or end of an image.
    Also applied to confounds."""

    from_end: int = 0
    """Number of timepoints to trim from the end of each image."""

    from_beginning: int = 0
    """Number of timepoints to trim from the beginning of each image."""


@dataclass
class ConfoundRegression(Option):
    """Regress out the confound file values from your image. 
    If any other processing steps are relevant to the confounds,
    they will be applied first."""

    implementation: str = "afni_3dTproject"
    """Currently limited to "afni_3dTproject"""


@dataclass
class ProcessingStepOptions(Option):
    """The default processing options for each step."""

    temporal_filtering: TemporalFiltering = TemporalFiltering()
    intensity_normalization: IntensityNormalization = IntensityNormalization()
    spatial_smoothing: SpatialSmoothing = SpatialSmoothing()
    aroma_regression: AROMARegression = AROMARegression()
    scrub_timepoints: ScrubTimepoints = ScrubTimepoints()
    resample: Resample = Resample()
    trim_timepoints: TrimTimepoints = TrimTimepoints()
    confound_regression: ConfoundRegression = ConfoundRegression()


@dataclass
class MotionOutliers(Option):
    """These options control the construction of spike regressor columns based on 
    a particular confound column (usually framewise_displacement)
    and a threshold. For each timepoint of the chosen variable that exceeds
    the threshold, a new column of all 0s and a single '1' at that timepoint is
    added to the end of the confounds file to serve as a spike regressor for GLM analysis."""

    include: bool = False
    """Set 'true' to add motion outlier spike regressors to each confound file."""

    scrub_var: str = "framewise_displacement"
    """Which variable in the confounds file should be used to calculate motion outliers."""

    threshold: float = 0.9
    """Threshold at which to flag a timepoint as a motion outlier."""

    scrub_ahead: int = 0
    """How many time points ahead of a flagged time point should be flagged also."""

    scrub_behind: int = 0
    """If a timepoint is scrubbed, how many points before to remove."""

    scrub_contiguous: int = 0
    """How many good contiguous timepoints need to exist."""


@dataclass
class ConfoundOptions(Option):
    """The default options to apply to the confounds files."""

    columns: list = field(
        default_factory=lambda: [
            "csf", "csf_derivative1", 
			"white_matter", "white_matter_derivative1"]
        )
    """A list containing a subset of confound file columns to use
    from each image's confound file. You may use the wildcard '*' operator
    to select groups of columns, such as 'csf*'"""

    motion_outliers: MotionOutliers = MotionOutliers()
    """Options specific to motion outliers."""


@dataclass
class BatchOptions(Option):
    """The batch settings for postprocessing."""

    memory_usage: str = "20G"
    """How much memory to allocate per job."""

    time_usage: str = "2:0:0"
    """How much time to allocate per job."""

    n_threads: str = "1"
    """How many threads to allocate per job."""


@dataclass
class PostProcessingOptions(Option):
    """Options for additional processing after fMRIPrep's preprocessing."""

    working_directory: str = "SET WORKING DIRECTORY"
    """Directory for caching intermediary processing files."""

    write_process_graph: bool = True
    """Set 'true' to write a processing graph alongside your output."""

    target_directory: str = ""
    """Which directory to process - leave empty to use your config's fMRIPrep output
    directory."""

    target_image_space: str = "MNI152NLin2009cAsym"
    """Which space to use from your fmriprep output.
    This is the value that follows "space-" in the image file names."""

    target_tasks: list = field(default_factory=list)
    """Which tasks to use from your fmriprep output. 
    This is the value that follows "task-" in the image file names.
    Leave blank to target all tasks."""

    target_acquisitions: list = field(default_factory=list)
    """Which acquisitions to use from your fmriprep output. 
    This is the value that follows "acq-" in the image file names.
    Leave blank to target all acquisitions."""

    output_directory: str = field(default_factory=list)
    """Path to save your postprocessing data. Defaults to data_postproc."""
    
    processing_steps: list = field(
        default_factory=lambda: [
            "SpatialSmoothing",
			"TemporalFiltering",
			"IntensityNormalization",
			"ApplyMask"]
        )
    """Your list of processing steps to use, in order."""

    processing_step_options: ProcessingStepOptions = ProcessingStepOptions()
    """Configuration for each processing step."""

    confound_options: ConfoundOptions = ConfoundOptions()
    """Options related to the outputted confounds file."""

    batch_options: BatchOptions = BatchOptions()
    """Options for cluster resource usage."""
    

    def populate_project_paths(self, project_directory: os.PathLike):
        pass

    def get_stream_dir(self, processing_stream: os.PathLike):
        """Combine output path and stream name to create stream out directory"""
        return os.path.join(self.output_directory, processing_stream)


@dataclass
class ROIExtractOptions(Option):
    """"""

    target_directory: str = ""
    """Target folder for processing - usually an fMRIPrep output directory."""

    target_suffix: str = "desc-postproc_bold.nii.gz"
    """Narrow down the images to use by specifying the path's suffix. Use 
    'desc-preproc_bold.nii.gz' if targeting the fMRIPrep dir."""

    output_directory: str = ""
    """Location of this command's output. Defaults to data_ROI_ts."""
    
    atlases: list = field(
        default_factory=lambda: ["power"]
        )
    """List of atlases to use. Use 'clpipe roi atlases' to show available atlases."""
    
    require_mask: bool = True
    """Choose whether or not an accompanying mask for each image is required in the 
    target directory."""
    
    prop_voxels: float = 0.5
    """ROIs with less than this proportion of voxels within the mask area are
    set to nan."""

    overlap_ok: bool = False
    """Are overlapping ROIs allowed?"""
    
    memory_usage: str = "20G"
    time_usage: str = "2:0:0"
    n_threads: str = "1"
    log_directory: str = ""

    def populate_project_paths(self, project_directory: os.PathLike):
        self.target_directory = os.path.join(project_directory, "data_postproc")
        self.output_directory = os.path.join(project_directory, 'data_ROI_ts')
        self.log_directory = os.path.join(project_directory, 'logs', 'ROI_extraction_logs')


@dataclass
class ProjectOptions(Option):
    """Contains metadata for your project and option blocks for each command."""

    project_title: str = "A Neuroimaging Project"
    """The title of your project."""

    contributors: str = "SET CONTRIBUTORS"
    """Members of the project team."""

    project_directory: str = ""
    """The root directory of your clpipe project."""

    email_address: str = "SET EMAIL ADDRESS"
    """Email address used for delivering batch job updates."""

    source: SourceOptions = SourceOptions()
    convert2bids: Convert2BIDSOptions = Convert2BIDSOptions()
    bids_validation: BIDSValidatorOptions = BIDSValidatorOptions()
    fmriprep: FMRIPrepOptions = FMRIPrepOptions()
    postprocessing: PostProcessingOptions = PostProcessingOptions()
    processing_streams: List[dict] = field(
        default_factory=lambda: [
            {
                "name": "GLM_default",
                "postprocessing_options": {
                    "processing_steps": [
                        "SpatialSmoothing",
                        "AROMARegression",
                        "TemporalFiltering",
                        "IntensityNormalization"
                    ]
                }
			},
            {
                "name": "functional_connectivity_default",
                "postprocessing_options": {
                    "processing_steps": [
                        "TemporalFiltering",
                        "ConfoundRegression"
                    ]
                }
            }
        ]
    )
    roi_extraction: ROIExtractOptions = ROIExtractOptions()
    batch_config_path: str = "slurmUNCConfig.json"
    clpipe_version: str = VERSION

    def get_logs_dir(self) -> str:
        """Get the project's top level log directory."""

        return os.path.join(self.project_directory, "logs")

    def to_dict(self):
        #Generate schema from given dataclasses
        config_schema = marshmallow_dataclass.class_schema(self.__class__)
        return config_schema().dump(self)

    def dump(self, outpath):
        #Generate schema from given dataclasses
        config_schema = marshmallow_dataclass.class_schema(self.__class__)
        config_dict = config_schema().dump(self)

        suffix = Path(outpath).suffix

        with open(outpath, 'w') as fp:
            json.dump(config_dict, fp, indent="\t")

        # .json --> .yaml necessary to get the .yaml to format correctly
        if(suffix) == '.yaml':
            os.rename(outpath, "temp_yaml_to_json")
            with open("temp_yaml_to_json", 'r') as json_in:
                conf = json.load(json_in)
            with open(outpath, 'w') as yaml_out:
                yaml.dump(conf, yaml_out, sort_keys=False)
            os.remove("temp_yaml_to_json")
    

    def populate_project_paths(self, project_dir: os.PathLike, source_data: os.PathLike):
        """Sets all project paths relative to a given project directory.

        Args:
            project_dir (os.PathLike): Root directory of the project.
            source_data (os.PathLike): Directory pointing to the source DICOM data.
        """
        self.project_directory = os.path.abspath(project_dir)

        self.convert2bids.populate_project_paths(project_dir, source_data)
        self.bids_validation.populate_project_paths(project_dir)
        self.fmriprep.populate_project_paths(project_dir)
        self.roi_extraction.populate_project_paths(project_dir)

        
    @classmethod
    def load(cls, file):
        #Generate schema from given dataclasses
        config_schema = marshmallow_dataclass.class_schema(cls)

        extension = Path(file).suffix

        with open(file) as f:
            if extension == '.yaml':
                config_dict = yaml.safe_load(f)
            elif extension == '.json':
                config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported extension: {extension}")

        if 'clpipe_version' not in config_dict:
            config_dict = convert_project_config(config_dict)    
        
        newNames = list(config_dict.keys())
        config_dict = dict(zip(newNames, list(config_dict.values())))
        return config_schema().load(config_dict)
    

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
    "clpipe_version": "clpipe_version",
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
    "roi_extraction": "ROIExtractionOptions",
    "atlases": "Atlases",
    "require_mask": "RequireMask",
    "prop_voxels": "PropVoxels",
    "overlap_ok": "OverlapOk",
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
    "scrub_columns": ""
}