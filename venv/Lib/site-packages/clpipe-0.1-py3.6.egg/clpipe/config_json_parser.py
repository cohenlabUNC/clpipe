import json
import datetime
from pkg_resources import resource_stream
from jsonschema import validate
import os

class ConfigParser:

    def __init__(self):
        self.setup_default_config()
        self.configSchema = json.load(resource_stream(__name__,'data/configSchema.json'))


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
            json.dump(self.config, fp)

    def setup_default_config(self):
        self.config = json.load(resource_stream(__name__,'data/defaultConfig.json'))

    def validate_config(self):
        validate(self.config, self.configSchema)

    def setup_directories(self, bidsDir, workingDir, outputDir):
        self.config['BIDSDirectory'] = bidsDir
        self.config['WorkingDirectory'] = workingDir
        self.config['OutputDirectory'] = outputDir

    def update_runlog(self, subjects, whatran):
        newLog = {'DateRan': datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"),
                  'Subjects': subjects,
                  'WhatRan': whatran}
        self.config['RunLog'].append(newLog)