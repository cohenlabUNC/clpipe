import click
from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import logging
import os

@click.command()
@click.option('-outputFile', default = 'AConfigFile.json', help = 'Filepath for the outputted configuration file.')
def get_config_file(outputfile=None):
    """This commands generates a default configuration file for further modification."""
    logging.basicConfig(level=logging.INFO)
    config = ClpipeConfigParser()
    config.config_json_dump(os.path.dirname(outputfile), os.path.basename(outputfile))
    logging.info('Config File at '+ os.path.join(os.path.abspath(os.path.dirname(outputfile)), os.path.basename(outputfile)))


@click.command()
@click.option('-outputFile', default = 'AGLMConfigFile.json', help = 'Filepath for the outputted configuration file.')
def get_glm_config_file(outputfile=None):
    """This commands generates a default configuration file for further modification."""
    logging.basicConfig(level=logging.INFO)
    config = GLMConfigParser()
    config.config_json_dump(os.path.dirname(outputfile), os.path.basename(outputfile))
    logging.info('GLM Config File at '+ os.path.join(os.path.abspath(os.path.dirname(outputfile)), os.path.basename(outputfile)))
