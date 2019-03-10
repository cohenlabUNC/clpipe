import datetime
import getpass
import json
import os
import collections
from jsonschema import validate
from pkg_resources import resource_stream


def config_json_parser(json_path):
    with open(os.path.abspath(json_path), "r") as config_file:
        config = json.load(config_file)

    return config


class ConfigParser:

    def __init__(self):
        with resource_stream(__name__, 'data/defaultConfig.json') as def_config:
            self.config = json.load(def_config)
        self.setup_default_config()
        with resource_stream(__name__, 'data/configSchema.json') as def_schema:
            self.configSchema = json.load(def_schema)

    def config_updater(self, new_config):
        if new_config is None:
            None
        else:
            new_config = config_json_parser(new_config)
            self.config = update(self.config, new_config)

    def config_json_dump(self, outputdir, filepath):
        if filepath is None:
            filepath = "defaultConfig.json"
        outpath = os.path.join(os.path.abspath(outputdir), filepath)
        with open(outpath, 'w') as fp:
            json.dump(self.config, fp, indent="\t")
        return(outpath)

    def setup_default_config(self):
        pass

    def validate_config(self):
        validate(self.config, self.configSchema)

    def setup_fmriprep_directories(self, bidsDir, workingDir, outputDir):
        if bidsDir is not None:
            self.config['FMRIPrepOptions']['BIDSDirectory'] = os.path.abspath(bidsDir)
            if not os.path.isdir(self.config['FMRIPrepOptions']['BIDSDirectory']):
                raise ValueError('BIDS Directory does not exist')
        if workingDir is not None:
            self.config['FMRIPrepOptions']['WorkingDirectory'] = os.path.abspath(workingDir)
            os.makedirs(self.config['FMRIPrepOptions']['WorkingDirectory'], exist_ok=True)
        if outputDir is not None:
            self.config['FMRIPrepOptions']['OutputDirectory'] = os.path.abspath(outputDir)
            os.makedirs(self.config['FMRIPrepOptions']['OutputDirectory'], exist_ok=True)

    def setup_postproc(self, target_dir, target_suffix, output_dir, output_suffix):
        if target_dir is not None:
            self.config['PostProcessingOptions']['TargetDirectory'] = os.path.abspath(target_dir)
            if not os.path.isdir(self.config['PostProcessingOptions']['TargetDirectory']):
                raise ValueError('Target Directory does not exist')
        if output_dir is not None:
            self.config['PostProcessingOptions']['OutputDirectory'] = os.path.abspath(output_dir)
            os.makedirs(self.config['PostProcessingOptions']['OutputDirectory'], exist_ok=True)
        if target_suffix is not None:
            self.config['PostProcessingOptions']['TargetSuffix'] = target_suffix
        if output_suffix is not None:
            self.config['PostProcessingOptions']['OutputSuffix'] = output_suffix

    def setup_heudiconv(self, dicom_directory, heuristic_file, output_directory):
        if dicom_directory is not None:
            self.config['DicomToBidsOptions']['DICOMDirectory'] = os.path.abspath(dicom_directory)
        if output_directory is not None:
            self.config['DicomToBidsOptions']['OutputDirectory'] = os.path.abspath(output_directory)
            os.makedirs(self.config['DicomToBidsOptions']['OutputDirectory'], exist_ok=True)
        if heuristic_file is not None:
            self.config['DicomToBidsOptions']['HeuristicFile'] = os.path.abspath(heuristic_file)

    def setup_roiextract(self, target_dir, target_suffix, output_dir):
        if target_dir is not None:
            self.config['ROIExtractionOptions']['TargetDirectory'] = os.path.abspath(target_dir)
            if not os.path.isdir(self.config['ROIExtractionOptions']['TargetDirectory']):
                raise ValueError('Target Directory does not exist')
        if output_dir is not None:
            self.config['ROIExtractionOptions']['OutputDirectory'] = os.path.abspath(output_dir)
            os.makedirs(self.config['ROIExtractionOptions']['OutputDirectory'], exist_ok=True)
        if target_suffix is not None:
            self.config['ROIExtractionOptions']['TargetSuffix'] = target_suffix


    def update_runlog(self, subjects, whatran):
        newLog = {'DateRan': datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"),
                  'Subjects': subjects,
                  'WhatRan': whatran,
                  "WhoRan": getpass.getuser()}
        self.config['RunLog'].append(newLog)


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
