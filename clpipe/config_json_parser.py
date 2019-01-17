import datetime
import getpass
import json
import os

from jsonschema import validate
from pkg_resources import resource_stream


class ConfigParser:

    def __init__(self, new_config=None):
        self.setup_default_config()
        self.configSchema = json.load(resource_stream(__name__,'data/configSchema.json'))

        if new_config is not None:
            self.config_updater(new_config)

    def config_json_parser(self,json_path):
        with open(json_path, "r") as config_file:
            config = json.load(config_file)

        return config

    def config_updater(self, newConfig):

        if newConfig is None:
            None
        else:
            self.config = {**self.config, **newConfig}
            self.config['DateRan'] = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
            self.validate_config()

    def config_json_dump(self, outputdir, filepath):
        if filepath is None:
            filepath = "defaultConfig.json"
        outpath = os.path.join(os.path.abspath(outputdir), filepath)
        with open(outpath, 'w') as fp:
            json.dump(self.config, fp, indent="\t")

    def setup_default_config(self):
        self.config = json.load(resource_stream(__name__,'data/defaultConfig.json'))

    def validate_config(self):
        validate(self.config, self.configSchema)

    def setup_directories(self, bidsDir, workingDir, outputDir):
        if bidsDir is not None:
            self.config['BIDSDirectory'] = os.path.abspath(bidsDir)
            if not os.path.isdir(self.config['BIDSDirectory']):
                raise ValueError('BIDS Directory does not exist')
        if workingDir is not None:
            self.config['WorkingDirectory'] = os.path.abspath(workingDir)
            os.makedirs(self.config['WorkingDirectory'],exist_ok=True)
        if outputDir is not None:
            self.config['OutputDirectory'] = os.path.abspath(outputDir)
            os.makedirs(self.config['OutputDirectory'], exist_ok=True)

    def update_runlog(self, subjects, whatran):
        newLog = {'DateRan': datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"),
                  'Subjects': subjects,
                  'WhatRan': whatran,
                  "WhoRan": getpass.getuser()}
        self.config['RunLog'].append(newLog)