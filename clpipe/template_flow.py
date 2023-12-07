import os
import click
import sys
import logging
from .config_json_parser import ClpipeConfigParser
from .error_handler import exception_handler
from templateflow import api


def templateflow_setup(config_file=None, debug=False):
    _templateflow_setup(config_file, debug)


def _templateflow_setup(config_file=None, debug=False):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    templateflow_path = config.config["FMRIPrepOptions"]["TemplateFlowPath"]
    logging.info("Setting TemplateFlow storage path to " + templateflow_path)
    os.system("export TEMPLATEFLOW_HOME=" + templateflow_path)
    logging.info(
        "Downloading requested templates "
        + " ".join(config.config["FMRIPrepOptions"]["TemplateFlowTemplates"])
    )
    api.get(config.config["FMRIPrepOptions"]["TemplateFlowTemplates"])
