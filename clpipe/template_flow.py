import os
import click
import sys
import logging
from .config_json_parser import ConfigParser
from .error_handler import exception_handler
from templateflow import api

@click.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def templateflow_setup(config_file=None, debug=False):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ConfigParser()
    config.config_updater(config_file)

    templateflow_path = config.config["FMRIPrepOptions"]["TemplateFlowPath"]
    logging.info("Setting TemplateFlow storage path to "+ templateflow_path)
    os.system("export TEMPLATEFLOW_HOME=" + templateflow_path)
    logging.info("Downloading requested templates")
    api.get(config.config['FMRIPrepOptions']["TemplateFlowTemplates"])
