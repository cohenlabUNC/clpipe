import os
import glob
import click
from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import logging
import sys
from .error_handler import exception_handler
import pkg_resources
pkg_resources.require("numpy==1.18.5")
pkg_resources.require("scipy==1.2.2")
import numpy
import pandas
import numpy as np

@click.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def fsl_onset_extract(config_file=None, glm_config_file = None, debug = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    glm_config = GLMConfigParser(glm_config_file)

    search_string = os.path.abspath(
        os.path.join(config.config["FMRIPrepOptions"]['BIDSDirectory'], "**",
                     "*" +"task-"+ glm_config.config["GLMSetupOptions"]['TaskName']+"*"+ glm_config.config["Level1Onsets"]['EventFileSuffix']))

    files = glob.glob(search_string, recursive=True)

    target_trials = glm_config.config["Level1Onsets"]['TrialTypeToExtract']

    for file in files:
        data = pandas.read_table(file)
        logging.info("Processing " + os.path.basename(file))
        for trial_type in target_trials:
            temp = data.loc[data[glm_config.config["Level1Onsets"]["TrialTypeVariable"]] == trial_type]

            onsets = temp['onset']/glm_config.config["Level1Onsets"]["TimeConversionFactor"]
            duration = temp['duration']/glm_config.config["Level1Onsets"]["TimeConversionFactor"]
            p_response  = numpy.repeat(np.array([1]), len(onsets))
            if glm_config.config["Level1Onsets"]["ParametricResponseVariable"] != "":
                p_response = temp[glm_config.config["Level1Onsets"]["ParametricResponseVariable"]]

            to_file = np.array([onsets, duration, p_response])
            file_name = os.path.basename(file).replace(glm_config.config["Level1Onsets"]['EventFileSuffix'], trial_type + ".txt")
            output = os.path.join(glm_config.config["Level1Onsets"]['EVDirectory'], file_name)
            logging.debug(output)
            numpy.savetxt(output, np.transpose(to_file), "%8.4f")

