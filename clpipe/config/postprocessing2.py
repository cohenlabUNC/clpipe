from dataclasses import dataclass

DEFAULT_PROCESSING_STREAM = "default"


@dataclass
class TemporalFiltering:
    implementation: str
    filtering_high_pass: float
    filtering_low_pass: int
    filtering_order: int

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class IntensityNormalization:
    implementation: str

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class SpatialSmoothing:
    implementation: str
    fwhm: int

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class AROMARegression:
    implementation: str

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

@dataclass
class ScrubTimepoints:
    target_variable: str
    threshold: float
    scrub_ahead: int
    scrub_behind: int
    scrub_contiguous: int
    insert_na: bool


@dataclass
class Resample:
    reference_image: str

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class TrimTimepoints:
    from_end: int
    from_beginning: int
    
    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class ConfoundRegression:
    implementation: str

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class ProcessingStepOptions:
    temporal_filtering: TemporalFiltering
    intensity_normalization: IntensityNormalization
    spatial_smoothing: SpatialSmoothing
    aroma_regression: AROMARegression
    scrub_timepoints: ScrubTimepoints
    resample: Resample
    trim_timepoints: TrimTimepoints
    confound_regression: ConfoundRegression

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class MotionOutliers:
    include: bool
    scrub_var: str
    threshold: float
    scrub_ahead: int
    scrub_behind: int
    scrub_contiguous: int

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class ConfoundOptions:
    columns: list
    motion_outliers: MotionOutliers

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class BatchOptions:
    memory_usage: str
    timeUsage: str
    n_threads: str

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True


@dataclass
class PostProcessingConfig:
    working_directory: str
    write_process_graph: bool
    target_directory: str
    target_image_space: str
    target_tasks: list
    target_acquisitions: list
    output_directory: str
    processing_steps: list
    processing_step_options: ProcessingStepOptions
    confound_options: ConfoundOptions
    batch_options: BatchOptions

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True