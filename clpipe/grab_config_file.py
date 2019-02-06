import click
from .config_json_parser import ConfigParser
import logging
import os

@click.command()
@click.option('-outputName', default = 'AConfigFile.json')
def grab_config_file(outputname=None):
    logging.basicConfig(level=logging.INFO)
    config = ConfigParser()
    config.config_json_dump('.', outputname)
    logging.info('Config File at '+ os.path.join(os.path.abspath('.'), outputname))
