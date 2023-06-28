from dataclasses import dataclass, field

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
