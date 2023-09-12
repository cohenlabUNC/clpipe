from dataclasses import dataclass, field
from typing import List
import marshmallow_dataclass
from marshmallow import validates, ValidationError
import json, yaml, os
from pathlib import Path
from typing import Union
from .package import VERSION

DEFAULT_CONFIG_FILE_NAME = 'clpipe_config.json'
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

    source_url: str = field(default="fw://", metadata={"required": True})
    """The URL to your source data - for Flywheel this should start with fw: 
    and point to a project. You can use fw ls to browse your fw project space 
    to find the right path."""

   
    dropoff_directory: str = field(default="", metadata={"required": True})
    """A destination for your synced data - usually this will be data_DICOMs"""
    
    temp_directory: str = field(default="", metadata={"required": True})
    """A location for Flywheel to store its temporary files - 
    necessary on shared compute, because Flywheel will use system 
    level tmp space by default, which can cause issues."""
    
    commandline_opts: str = field(default="-y", metadata={"required": True})
    """Any additional options you may need to include - 
    you can browse Flywheel syncs other options with fw sync -help"""

    time_usage: str = field(default="1:0:0", metadata={"required": True})
    mem_usage: str = field(default="10G", metadata={"required": True})
    core_usage: str = field(default="2", metadata={"required": True})

    @validates("source_url")
    def validate_(self, value):
        if not value.startswith("fw://"):
            raise ValidationError("source_url must start with prefix: fw://")


@dataclass
class Convert2BIDSOptions(Option):
    """Options for converting DICOM files to BIDS format."""
    
    dicom_directory: str = field(default="", metadata={"required": True})
    """Path to your source DICOM directory to be converted."""

    bids_directory: str = field(default="", metadata={"required": True})
    """Output directory where your BIDS data will be saved."""

    conversion_config: str = field(default="", metadata={"required": True})
    """The path to your conversion configuration file - either a
    conversion_config.json file for dcm2bids, or heuristic.py for heudiconv."""

    dicom_format_string: str = field(default="", metadata={"required": True})
    """Used to tell clpipe where to find subject and session level folders in you
    DICOM directory."""

    time_usage: str = field(default="1:0:0", metadata={"required": True})
    mem_usage: str = field(default="5000", metadata={"required": True})
    core_usage: str = field(default="2", metadata={"required": True})
    log_directory: str = field(default="", metadata={"required": True})

    @validates("conversion_config")
    def validate_conversion_config(self, value):
        suffix = Path(value).suffix
        if (suffix != ".py") and (suffix != ".json"):
            raise ValidationError("Must be type '.py' or '.json'")

    def populate_project_paths(self, project_directory: os.PathLike, source_data: os.PathLike):
        # create as alt constructor?

        self.dicom_directory = os.path.abspath(source_data)
        self.conversion_config = os.path.join(project_directory, 'conversion_config.json')
        self.bids_directory = os.path.join(project_directory, 'data_BIDS')
        self.log_directory = os.path.join(project_directory, "logs", "DCM2BIDS_logs")


@dataclass
class BIDSValidatorOptions(Option):
    """Options for validating your BIDS directory."""

    bids_validator_image: str = field(default="/proj/hng/singularity_imgs/validator.simg", metadata={"required": True})
    """Path to your BIDS validator image."""
    
    log_directory: str = field(default="", metadata={"required": True})

    def populate_project_paths(self, project_directory: os.PathLike):
        self.log_directory = os.path.join(project_directory, "logs", "bids_validation_logs")


@dataclass
class FMRIPrepOptions(Option):
    """Options for configuring fMRIPrep."""

    bids_directory: str = field(default="", metadata={"required": True}) 
    """Your BIDs formatted raw data directory."""

    working_directory: str = field(default="SET WORKING DIRECTORY", metadata={"required": True})
    """Storage location for intermediary fMRIPrep files. Takes up a large
    amount of space - Longleaf users should use their /work folder."""

    
    output_directory: str = field(default="", metadata={"required": True}) 
    """ Where to save your preprocessed images. """

    fmriprep_path: str = field(default="/proj/hng/singularity_imgs/fmriprep_22.1.1.sif", metadata={"required": True}) 
    """Path to your fMRIPrep Singularity image."""
    
    freesurfer_license_path: str = field(default="/proj/hng/singularity_imgs/license.txt", metadata={"required": True}) 
    """Path to your Freesurfer license .txt file."""
    
    use_aroma: bool = field(default=False, metadata={"required": True}) 
    """Set True to generate AROMA artifacts. Significantly increases run
    time and memory usage."""
    
    commandline_opts: str = field(default="", metadata={"required": True})
    """Any additional arguments to pass to FMRIprep."""
    
    templateflow_toggle: bool = field(default=True, metadata={"required": True})
    """Set True to activate to use templateflow, which allows you to
    generate multiple template variantions for the same outputs."""
    
    templateflow_path: str = field(default="/proj/hng/singularity_imgs/template_flow", metadata={"required": True})
    """The path to your templateflow directory."""

    templateflow_templates: list = field(
        default_factory=lambda: [
            "MNI152NLin2009cAsym", 
            "MNI152NLin6Asym", 
            "OASIS30ANTs", 
            "MNIPediatricAsym", 
            "MNIInfant"], metadata={"required": True}
        )
    """Which templates (standard spaces) should clpipe download for use in templateflow?"""

    fmap_roi_cleanup: int = field(default=3, metadata={"required": False})
    """How many timepoints should the fmap_cleanup function extract from 
    blip-up/blip-down field maps, set to -1 to disable."""
    
    fmriprep_memory_usage: str = field(default="50G", metadata={"required": True})
    """How much memory in RAM each subject's preprocessing will use."""

    fmriprep_time_usage: str = field(default="16:0:0", metadata={"required": True})
    """How much time on the cluster fMRIPrep is allowed to use."""
    
    n_threads: str = field(default="12", metadata={"required": True})
    """How many threads to use in each job."""

    log_directory: str = field(default="", metadata={"required": True})
    """Path to your logging directory for fMRIPrep outputs.
    Not generally changed from default."""

    docker_toggle: bool = field(default=False, metadata={"required": True})
    """Set True to use a Docker image."""
    
    docker_fmriprep_version: str = field(default="", metadata={"required": True})
    """Path to your fMRIPrep Docker image."""

    def populate_project_paths(self, project_directory: os.PathLike):
        self.bids_directory = os.path.join(project_directory, "data_BIDS")
        self.output_directory = os.path.join(project_directory, 'data_fmriprep')
        self.log_directory = os.path.join(project_directory, 'logs', 'FMRIprep_logs')


@dataclass
class TemporalFiltering(Option):
    """This step removes signals from an image's timeseries based on cutoff thresholds.
    Also applied to confounds."""

    implementation: str = field(default="fslmaths", metadata={"required": True})
    """Available implementations: fslmaths, 3dTProject"""

    filtering_high_pass: float = field(default=0.008, metadata={"required": True})
    """Values below this threshold are filtered. Defaults to .08 Hz. Set to -1 to disable."""

    filtering_low_pass: int = field(default=-1, metadata={"required": True})
    """Values above this threshold are filtered. Disabled by default (-1)."""

    filtering_order: int = field(default=2, metadata={"required": True})
    """Order of the filter. Defaults to 2."""

@dataclass
class IntensityNormalization(Option):
    """Normalize the intensity of the image data."""

    implementation: str = field(default="10000_GlobalMedian", metadata={"required": True})
    """Currently limited to '10000_GlobalMedian'"""

@dataclass
class SpatialSmoothing(Option):
    """Apply spatial smoothing to the image data."""

    implementation: str = field(default="SUSAN", metadata={"required": True})
    """Currently limited to 'SUSAN'"""

    fwhm: int = field(default=6, metadata={"required": True})
    """The size of the smoothing kernel.
    Specifically the full width half max of the Gaussian kernel.
    Scaled in millimeters."""

@dataclass
class AROMARegression(Option):
    """Regress out automatically classified noise artifacts from the image data
    using AROMA. Also applied to confounds."""

    implementation: str = field(default="fsl_regfilt", metadata={"required": True})


@dataclass
class ScrubTimepoints(Option):
    """This step can be used to remove timepoints from the image timeseries
    based on a target variable from that image's confounds file. Timepoints scrubbed
    from an image's timeseries are also removed its respective confound file."""

    insert_na: bool = field(default=True, metadata={"required": True})
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
    
    target_variable: str = field(default="framewise_displacement", metadata={"required": True})
    """Which confound variable to use as a reference for scrubbing. May use wildcard (*) to select multiple similar columns."""

    threshold: float = field(default=0.9, metadata={"required": True})
    """Any timepoint of the target variable exceeding this value will be scrubbed"""

    scrub_ahead: int = field(default=0, metadata={"required": True})
    """Set the number of timepoints to scrub ahead of target timepoints"""

    scrub_behind: int = field(default=0, metadata={"required": True})
    """Set the number of timepoints to scrub behind target timepoints"""

    scrub_contiguous: int = field(default=0, metadata={"required": True})
    """Scrub everything between scrub targets up to this far apart"""


@dataclass
class Resample(Option):
    """Resample your image to a new space."""
    
    reference_image: str = field(default="SET REFERENCE IMAGE", metadata={"required": True})
    """Path to an image against which to resample - often a template"""

@dataclass
class TrimTimepoints(Option):
    """Trim timepoints from the beginning or end of an image.
    Also applied to confounds."""

    from_end: int = field(default=0, metadata={"required": True})
    """Number of timepoints to trim from the end of each image."""

    from_beginning: int = field(default=0, metadata={"required": True})
    """Number of timepoints to trim from the beginning of each image."""

@dataclass
class ConfoundRegression(Option):
    """Regress out the confound file values from your image. 
    If any other processing steps are relevant to the confounds,
    they will be applied first."""

    implementation: str = field(default="afni_3dTproject", metadata={"required": True})
    """Currently limited to "afni_3dTproject"""


@dataclass
class ProcessingStepOptions(Option):
    """The default processing options for each step."""

    temporal_filtering: TemporalFiltering = field(default_factory=TemporalFiltering, metadata={"required": True})
    intensity_normalization: IntensityNormalization = field(default_factory=IntensityNormalization, metadata={"required": True})
    spatial_smoothing: SpatialSmoothing = field(default_factory=SpatialSmoothing, metadata={"required": True})
    aroma_regression: AROMARegression = field(default_factory=AROMARegression, metadata={"required": True})
    scrub_timepoints: ScrubTimepoints = field(default_factory=ScrubTimepoints, metadata={"required": True})
    resample: Resample = field(default_factory=Resample, metadata={"required": True})
    trim_timepoints: TrimTimepoints = field(default_factory=TrimTimepoints, metadata={"required": True})

@dataclass
class MotionOutliers(Option):
    """These options control the construction of spike regressor columns based on 
    a particular confound column (usually framewise_displacement)
    and a threshold. For each timepoint of the chosen variable that exceeds
    the threshold, a new column of all 0s and a single '1' at that timepoint is
    added to the end of the confounds file to serve as a spike regressor for GLM analysis."""

    include: bool = field(default=False, metadata={"required": True})
    """Set 'true' to add motion outlier spike regressors to each confound file."""

    scrub_var: str = field(default="framewise_displacement", metadata={"required": True})
    """Which variable in the confounds file should be used to calculate motion outliers."""

    threshold: float = field(default=0.9, metadata={"required": True})
    """Threshold at which to flag a timepoint as a motion outlier."""

    scrub_ahead: int = field(default=0, metadata={"required": True})
    """How many time points ahead of a flagged time point should be flagged also."""

    scrub_behind: int = field(default=0, metadata={"required": True})
    """If a timepoint is scrubbed, how many points before to remove."""

    scrub_contiguous: int = field(default=0, metadata={"required": True})
    """How many good contiguous timepoints need to exist."""

@dataclass
class ConfoundOptions(Option):
    """The default options to apply to the confounds files."""

    columns: list = field(
        default_factory=lambda: [
            "csf", "csf_derivative1", 
			"white_matter", "white_matter_derivative1"],
        metadata={"required": True}
        )
    """A list containing a subset of confound file columns to use
    from each image's confound file. You may use the wildcard '*' operator
    to select groups of columns, such as 'csf*'"""

    motion_outliers: MotionOutliers = field(default_factory=MotionOutliers, metadata={"required": True})
    """Options specific to motion outliers."""

@dataclass
class BatchOptions(Option):
    """The batch settings for postprocessing."""

    memory_usage: str = field(default="20G", metadata={"required": True})
    """How much memory to allocate per job."""

    time_usage: str = field(default="2:0:0", metadata={"required": True})
    """How much time to allocate per job."""

    n_threads: str = field(default="1", metadata={"required": True})
    """How many threads to allocate per job."""

@dataclass
class PostProcessingOptions(Option):
    """Options for additional processing after fMRIPrep's preprocessing."""

    stream_name: str = field(default="default", metadata={"required": True})
    """Name of the processing stream to use. 'default' uses no stream."""

    working_directory: str = field(default="SET WORKING DIRECTORY", metadata={"required": True})
    """Directory for caching intermediary processing files."""

    write_process_graph: bool = field(default=True, metadata={"required": True})
    """Set 'true' to write a processing graph alongside your output."""

    target_directory: str = field(default="", metadata={"required": True})
    """Which directory to process - leave empty to use your config's fMRIPrep output
    directory."""

    target_image_space: str = field(default="MNI152NLin2009cAsym", metadata={"required": True})
    """Which space to use from your fmriprep output.
    This is the value that follows "space-" in the image file names."""

    target_tasks: list = field(default_factory=list, metadata={"required": True})
    """Which tasks to use from your fmriprep output. 
    This is the value that follows "task-" in the image file names.
    Leave blank to target all tasks."""

    target_acquisitions: list = field(default_factory=list, metadata={"required": True})
    """Which acquisitions to use from your fmriprep output. 
    This is the value that follows "acq-" in the image file names.
    Leave blank to target all acquisitions."""

    output_directory: str = field(default="data_postprocess", metadata={"required": True})
    """Path to save your postprocessing data. Defaults to data_postproc."""
    
    processing_steps: list = field(
        default_factory=lambda: [
            "SpatialSmoothing",
            "TemporalFiltering",
            "IntensityNormalization",
            "ApplyMask"],
        metadata={"required": True}
    )
    """Your list of processing steps to use, in order."""

    processing_step_options: ProcessingStepOptions = field(default_factory=ProcessingStepOptions, metadata={"required": True})
    """Configuration for each processing step."""

    confound_options: ConfoundOptions = field(default_factory=ConfoundOptions, metadata={"required": True})
    """Options related to the outputted confounds file."""

    batch_options: BatchOptions = field(default_factory=BatchOptions, metadata={"required": True})
    """Options for cluster resource usage."""

    log_directory: str = field(default="", metadata={"required": True})
    """Log output location. Not normally changed from default."""

    def populate_project_paths(self, project_directory: os.PathLike):
        self.target_directory = os.path.join(project_directory, "data_fmriprep")
        self.output_directory = os.path.join(project_directory, 'data_postprocess')
        self.log_directory = os.path.join(project_directory, 'logs', 'postprocess_logs')

    
    def get_stream_working_dir(self, processing_stream:str):
        """Get the working directory relative to the processing stream."""
        return os.path.join(self.working_directory, processing_stream)

    def get_stream_output_dir(self, processing_stream:str):
        """Get the output directory relative to the processing stream."""
        return os.path.join(self.output_directory, processing_stream)

    def get_stream_log_dir(self, processing_stream:str):
        """Get the log directory relative to the processing stream."""
        return os.path.join(self.log_directory, processing_stream)

    def get_pybids_db_path(self, processing_stream: str, index_name: str):
        """Get the path to the pybids index relative to the stream working dir."""
        return os.path.join(self.get_stream_working_dir(processing_stream), index_name)


@dataclass
class PostProcessingRunConfiguration(Option):
    """Stores the configuration for a postprocessing run.
    
    Holds a copy of postprocessing options internally for reference. Values of this
    class hold variants of these values with the appropriate stream paths, as well
    as any other necessary values not in the options.
    """
    processing_step_options: ProcessingStepOptions = field(default_factory=PostProcessingOptions)
    
    stream_working_dir: str = ""
    
    stream_log_dir: str = ""
    
    stream_output_dir: str = ""
    
    pybids_db_path: str = ""
    


@dataclass
class ROIExtractOptions(Option):
    """Options for ROI extraction."""

    target_directory: str = field(default="", metadata={"required": True})
    """Target folder for processing - usually an fMRIPrep output directory."""

    target_suffix: str = field(default="desc-postproc_bold.nii.gz", metadata={"required": True})
    """Narrow down the images to use by specifying the path's suffix. Use 
    'desc-preproc_bold.nii.gz' if targeting the fMRIPrep dir."""

    output_directory: str = field(default="data_ROI_ts", metadata={"required": True})
    """Location of this command's output. Defaults to data_ROI_ts."""
    
    atlases: list = field(default_factory=lambda: ["power"], metadata={"required": True})
    """List of atlases to use. Use 'clpipe roi atlases' to show available atlases."""
    
    require_mask: bool = field(default=True, metadata={"required": True})
    """Choose whether or not an accompanying mask for each image is required in the 
    target directory."""
    
    prop_voxels: float = field(default=0.5, metadata={"required": True})
    """ROIs with less than this proportion of voxels within the mask area are
    set to nan."""

    overlap_ok: bool = field(default=False, metadata={"required": True})
    """Are overlapping ROIs allowed?"""

    memory_usage: str = field(default="20G", metadata={"required": True})
    time_usage: str = field(default="2:0:0", metadata={"required": True})
    n_threads: str = field(default="1", metadata={"required": True})
    log_directory: str = field(default="", metadata={"required": True})

    def populate_project_paths(self, project_directory: os.PathLike):
        self.target_directory = os.path.join(project_directory, "data_postproc")
        self.output_directory = os.path.join(project_directory, 'data_ROI_ts')
        self.log_directory = os.path.join(project_directory, 'logs', 'ROI_extraction_logs')


@dataclass
class ProjectOptions(Option):
    """Contains metadata for your project and option blocks for each command."""

    project_title: str = field(default="A Neuroimaging Project", metadata={"required": True})
    """The title of your project."""

    contributors: str = field(default="SET CONTRIBUTORS", metadata={"required": True})
    """Members of the project team."""

    project_directory: str = field(default="", metadata={"required": True})
    """The root directory of your clpipe project."""

    email_address: str = field(default="SET EMAIL ADDRESS", metadata={"required": True})
    """Email address used for delivering batch job updates."""

    source: SourceOptions = field(default_factory=SourceOptions, metadata={"required": True})
    convert2bids: Convert2BIDSOptions = field(default_factory=Convert2BIDSOptions, metadata={"required": True})
    bids_validation: BIDSValidatorOptions = field(default_factory=BIDSValidatorOptions, metadata={"required": True})
    fmriprep: FMRIPrepOptions = field(default_factory=FMRIPrepOptions, metadata={"required": True})
    postprocessing: PostProcessingOptions = field(default_factory=PostProcessingOptions, metadata={"required": True})
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
        ], metadata={"required": True}
    )
    roi_extraction: ROIExtractOptions = field(default_factory=ROIExtractOptions, metadata={"required": True})
    batch_config_path: str = field(default="slurmUNCConfig.json", metadata={"required": True})
    clpipe_version: str = field(default=VERSION, metadata={"required": True})

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
        self.postprocessing.populate_project_paths(project_dir)

        # Try cls with ProjectOptions(project_direct = x, ...), and in children

        
    @classmethod
    def load(cls, options: Union[os.PathLike, 'ProjectOptions']):
        # Return if given ProjectOptions object for testing convenience
        if isinstance(options, cls):
            return options

        #Generate schema from given dataclasses
        config_schema = marshmallow_dataclass.class_schema(cls)

        extension = Path(options).suffix

        with open(options) as f:
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
    
def update_config_file(config_file: os.PathLike, backup: bool = False) -> None:
    config_file = Path(config_file).resolve()

    if backup:
        import shutil
        backup_path = config_file.parent / f"{config_file.stem}_OLD{config_file.suffix}"
        print(f'Backup config file created: {str(backup_path.name)}')
        shutil.copy(config_file, backup_path)

    # TODO: can actually check the version of the config file and check if update needed
    old_options = ProjectOptions.load(config_file)
    old_options.dump(config_file)
    print(f'Config file {config_file.name} updated.')

def get_config_file(output_file="clpipe_config_DEFAULT.json"):
    """This commands generates a default configuration file for further modification."""

    config = ProjectOptions.load()
    config.dump(output_file)
    print('Config file created at '+ output_file)

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
    "scrub_columns": "",
    "stream_name": "",
}