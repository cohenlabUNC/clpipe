from dataclasses import dataclass

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
