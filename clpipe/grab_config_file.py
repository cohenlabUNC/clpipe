from .config_json_parser import ClpipeConfigParser, GLMConfigParser
from pathlib import Path
from .config.options import ProjectOptions
import logging
import os

def get_glm_config_file(outputfile=None):
    """This commands generates a default configuration file for further modification."""
 
    config = GLMConfigParser()
    config.config_json_dump(os.path.dirname(outputfile), os.path.basename(outputfile))
    print('GLM Config File at '+ os.path.join(os.path.abspath(os.path.dirname(outputfile)), os.path.basename(outputfile)))
