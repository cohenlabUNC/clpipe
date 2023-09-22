from typing import List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParallelConfig:
    """Configuration for ParallelManager."""

    output_directory: str = field(
        default=".", metadata={"description": "Output directory for batch jobs."}
    )
    debug: bool = field(default=False, metadata={"description": "Enable debug mode."})
    mem_use: str = field(
        default=None, metadata={"description": "Memory usage configuration."}
    )
    time: str = field(default=None, metadata={"description": "Time configuration."})
    threads: int = field(default=None, metadata={"description": "Number of threads."})
    email: str = field(
        default=None, metadata={"description": "Email address for job notifications."}
    )
    submission_head: 
