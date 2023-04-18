import os
import glob
import numpy
import pandas
import numpy as np

from .config_json_parser import ClpipeConfigParser, GLMConfigParser
from .utils import get_logger

STEP_NAME = "fsl_onset_extract"

def fsl_onset_extract(config_file=None, glm_config_file = None, debug = None):
    

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    glm_config = GLMConfigParser(glm_config_file)

    project_dir = config.config["ProjectDirectory"]
    logger = get_logger(STEP_NAME, debug=debug, f_name=os.path.join(project_dir, "logs"))

    search_string = os.path.abspath(
        os.path.join(config.config["FMRIPrepOptions"]['BIDSDirectory'], "**",
                     "*" +"task-"+ glm_config.config["GLMSetupOptions"]['TaskName']+"*"+ glm_config.config["Level1Onsets"]['EventFileSuffix']))

    files = glob.glob(search_string, recursive=True)

    target_trials = glm_config.config["Level1Onsets"]['TrialTypeToExtract']

    for file in files:
        data = pandas.read_table(file)
        logger.info("Processing " + os.path.basename(file))
        for trial_type in target_trials:
            temp = data.loc[data[glm_config.config["Level1Onsets"]["TrialTypeVariable"]] == trial_type]
            if len(temp) == 0:
                logger.warning("Trial Type: "+ trial_type + ", has no entries. If this is unexpected, check your GLM config file for misspellings/incorrect entries in the ['Level1Onsets']['TrialTypeToExtract']")
            else:
                onsets = temp['onset']/glm_config.config["Level1Onsets"]["TimeConversionFactor"]
                duration = temp['duration']/glm_config.config["Level1Onsets"]["TimeConversionFactor"]
                p_response  = numpy.repeat(np.array([1]), len(onsets))
                if glm_config.config["Level1Onsets"]["ParametricResponseVariable"] != "":
                    p_response = temp[glm_config.config["Level1Onsets"]["ParametricResponseVariable"]]

                to_file = np.array([onsets, duration, p_response])
                file_name = os.path.basename(file).replace(glm_config.config["Level1Onsets"]['EventFileSuffix'], trial_type + ".txt")
                output = os.path.join(glm_config.config["Level1Onsets"]['EVDirectory'], file_name)
                logger.debug(output)
                numpy.savetxt(output, np.transpose(to_file), "%8.4f")

