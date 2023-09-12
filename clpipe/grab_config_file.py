from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import logging
import os

def get_config_file(outputfile=None):
    """This commands generates a default configuration file for further modification."""

    logging.basicConfig(level=logging.INFO)
    config = ClpipeConfigParser()
    config.config_json_dump(os.path.dirname(outputfile), os.path.basename(outputfile))
    print('Config File at '+ os.path.join(os.path.abspath(os.path.dirname(outputfile)), os.path.basename(outputfile)))

def get_glm_config_file(outputfile=None):
    """This commands generates a default configuration file for further modification."""
 
    config = GLMConfigParser()
    config.config_json_dump(os.path.dirname(outputfile), os.path.basename(outputfile))
    print('GLM Config File at '+ os.path.join(os.path.abspath(os.path.dirname(outputfile)), os.path.basename(outputfile)))
