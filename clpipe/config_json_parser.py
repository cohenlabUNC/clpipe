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

    def setup_project(self, project_title, project_dir, source_data):
        self.config['ProjectTitle'] = project_title
        self.config['ProjectDirectory'] = os.path.abspath(project_dir)
        self.setup_dcm2bids(os.path.abspath(source_data),
                            os.path.join(self.config['ProjectDirectory'], 'conversion_config.json'),
                            os.path.join(self.config['ProjectDirectory'], 'data_BIDS'),
                            None)
        self.setup_fmriprep_directories(os.path.join(self.config['ProjectDirectory'], 'data_BIDS'),
                                        None, os.path.join(self.config['ProjectDirectory'], 'data_fmriprep'))
        self.setup_postproc(os.path.join(self.config['FMRIPrepOptions']['OutputDirectory'], 'fmriprep'),
                            target_suffix= None,
                            output_dir= os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'postproc_default'),
                            output_suffix= 'postproc_1.nii.gz')
        self.setup_postproc(os.path.join(self.config['FMRIPrepOptions']['OutputDirectory'], 'fmriprep'),
                            target_suffix=None,
                            output_dir=os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'betaseries_default'),
                            output_suffix='betaseries_1.nii.gz', beta_series=True)
        self.setup_roiextract(target_dir = os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'postproc_default'),
                              target_suffix= 'postproc.nii.gz',
                              output_dir= os.path.join(self.config['ProjectDirectory'],
                                           'data_ROI_ts', 'postproc_default'),
                              )
        processing_streams = self.get_processing_stream_names()
        print(processing_streams)
        if processing_streams:
            for stream in processing_streams:
                self.update_processing_stream(stream,
                                              output_dir= os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'postproc_'+stream),
                                              output_suffix='postproc_'+stream+".nii.gz")
                self.update_processing_stream(stream,
                                              output_dir= os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'betaseries_'+stream),
                                              output_suffix='betaseries_'+stream+".nii.gz", beta_series=True)



    def setup_fmriprep_directories(self, bidsDir, workingDir, outputDir, log_dir = None):
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
        if log_dir is not None:
            self.config['FMRIPrepOptions']['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['FMRIPrepOptions']['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs', 'FMRIprep_logs')

    def setup_postproc(self, target_dir, target_suffix, output_dir, output_suffix, beta_series = False, log_dir = None):
        target_output = 'PostProcessingOptions'
        log_target = 'postproc_logs'
        if beta_series:
            target_output = 'BetaSeriesOptions'
            log_target = 'betaseries_logs'

        if target_dir is not None:
            self.config[target_output]['TargetDirectory'] = os.path.abspath(target_dir)
        if output_dir is not None:
            self.config[target_output]['OutputDirectory'] = os.path.abspath(output_dir)
            os.makedirs(self.config[target_output]['OutputDirectory'], exist_ok=True)
        if target_suffix is not None:
            self.config[target_output]['TargetSuffix'] = target_suffix
        if output_suffix is not None:
            self.config[target_output]['OutputSuffix'] = output_suffix
        if log_dir is not None:
            self.config[target_output]['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config[target_output]['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs', log_target)
        os.makedirs(self.config[target_output]['LogDirectory'], exist_ok=True)

    def setup_heudiconv(self, dicom_directory, heuristic_file, output_directory):
        if dicom_directory is not None:
            self.config['DicomToBidsOptions']['DICOMDirectory'] = os.path.abspath(dicom_directory)
        if output_directory is not None:
            self.config['DicomToBidsOptions']['OutputDirectory'] = os.path.abspath(output_directory)
            os.makedirs(self.config['DicomToBidsOptions']['OutputDirectory'], exist_ok=True)
        if heuristic_file is not None:
            self.config['DicomToBidsOptions']['HeuristicFile'] = os.path.abspath(heuristic_file)

    def setup_dcm2bids(self, dicom_directory, heuristic_file, output_directory, dicom_format_string, log_dir = None):
        if dicom_directory is not None:
            self.config['DICOMToBIDSOptions']['DICOMDirectory'] = os.path.abspath(dicom_directory)
        if output_directory is not None:
            self.config['DICOMToBIDSOptions']['BIDSDirectory'] = os.path.abspath(output_directory)
            os.makedirs(self.config['DICOMToBIDSOptions']['BIDSDirectory'], exist_ok=True)
        if heuristic_file is not None:
            self.config['DICOMToBIDSOptions']['ConversionConfig'] = os.path.abspath(heuristic_file)
        if dicom_format_string is not None:
            self.config['DICOMToBIDSOptions']['DICOMFormatString'] = dicom_format_string
        if log_dir is not None:
            self.config['DICOMToBIDSOptions']['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['DICOMToBIDSOptions']['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs', 'DCM2BIDS_logs')
        os.makedirs(self.config['DICOMToBIDSOptions']['LogDirectory'], exist_ok=True)

    def setup_roiextract(self, target_dir, target_suffix, output_dir, log_dir = None):
        if target_dir is not None:
            self.config['ROIExtractionOptions']['TargetDirectory'] = os.path.abspath(target_dir)
            if not os.path.isdir(self.config['ROIExtractionOptions']['TargetDirectory']):
                raise ValueError('Target Directory does not exist')
        if output_dir is not None:
            self.config['ROIExtractionOptions']['OutputDirectory'] = os.path.abspath(output_dir)
            os.makedirs(self.config['ROIExtractionOptions']['OutputDirectory'], exist_ok=True)
        if target_suffix is not None:
            self.config['ROIExtractionOptions']['TargetSuffix'] = target_suffix
        if log_dir is not None:
            self.config['ROIExtractionOptions']['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['ROIExtractionOptions']['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs',
                                                                             'ROI_extraction_logs')
        os.makedirs(self.config['ROIExtractionOptions']['LogDirectory'], exist_ok=True)

    def get_processing_stream_names(self):
        try:
            names = [i["ProcessingStream"] for i in self.config['ProcessingStreams']]
        except(KeyError):
            return False
        return names

    def update_processing_stream(self, stream_name, output_dir = None, output_suffix = None, log_dir = None, beta_series = False):
        target_output = 'PostProcessingOptions'
        log_target = stream_name+'_postproc_logs'
        if beta_series:
            target_output = 'BetaSeriesOptions'
            log_target = stream_name+'_betaseries_logs'

        index = [ind  for ind,e in enumerate(self.config['ProcessingStreams']) if e['ProcessingStream'] == stream_name][0]
        if output_dir is not None:
            self.config['ProcessingStreams'][index][target_output]['OutputDir'] = os.path.abspath(output_dir)
            os.makedirs(self.config['ProcessingStreams'][index][target_output]['OutputDir'], exist_ok=True)
        if output_suffix is not None:
            self.config['ProcessingStreams'][index][target_output]['OutputSuffix'] = output_suffix
        if log_dir is not None:
            self.config['ProcessingStreams'][index][target_output]['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['ProcessingStreams'][index][target_output]['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs', log_target)
        os.makedirs(self.config[target_output]['LogDirectory'], exist_ok=True)

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
