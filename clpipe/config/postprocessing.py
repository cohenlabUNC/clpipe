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
class ScrubTimepoints:
    TargetVariable: str
    Threshold: float
    ScrubAhead: int
    ScrubBehind: int
    ScrubContiguous: int
    InsertNA: bool
    
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
    timeUsage: str = ""
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