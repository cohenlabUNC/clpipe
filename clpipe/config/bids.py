from dataclasses import dataclass

@dataclass
class BIDSValidatorOptions:
    bids_validator_image: str = ""
    log_directory: str = ""
    
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
