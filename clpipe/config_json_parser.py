import datetime
import getpass
import json
import os
import collections
import click
from pkg_resources import resource_stream, resource_filename
import shutil

@click.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True),
              default=None, required = True,
              help='Configuration file to update.')
def update_config_file(config_file=None):
    '''Updates an existing configuration file with any new fields. Does not modify existing fields.'''
    new_config = config_json_parser(config_file)
    temp = config_json_parser(config_file)
    with resource_stream(__name__, 'data/defaultConfig.json') as def_config:
            config_default = json.load(def_config)
    new_config = update(new_config, config_default)
    new_config = update(new_config, temp)
    with open(config_file, 'w') as fp:
        json.dump(new_config, fp, indent="\t")

def config_json_parser(json_path):
    with open(os.path.abspath(json_path), "r") as config_file:
        config = json.load(config_file)

    return config


class ClpipeConfigParser:

    def __init__(self, config_file:os.PathLike=None):
        if not config_file:
            with resource_stream(__name__, 'data/defaultConfig.json') as def_config:
                self.config = json.load(def_config)
            self.setup_default_config()
        else:
            self.config = config_json_parser(config_file)
        #with resource_stream(__name__, 'data/configSchema.json') as def_schema:
         #   self.configSchema = json.load(def_schema)

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
       # validate(self.config, self.configSchema)
        return 1

    def setup_project(self, project_title, project_dir, source_data):
        self.config['ProjectTitle'] = project_title
        self.config['ProjectDirectory'] = os.path.abspath(project_dir)
        self.setup_dcm2bids(os.path.abspath(source_data),
                            os.path.join(self.config['ProjectDirectory'], 'conversion_config.json'),
                            os.path.join(self.config['ProjectDirectory'], 'data_BIDS'),
                            None)
        self.setup_bids_validation(None)
        self.setup_fmriprep_directories(os.path.join(self.config['ProjectDirectory'], 'data_BIDS'),
                                        None, os.path.join(self.config['ProjectDirectory'], 'data_fmriprep'))
        self.setup_postproc(os.path.join(self.config['FMRIPrepOptions']['OutputDirectory'], 'fmriprep'),
                            target_suffix= None,
                            output_dir= os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'postproc_default'),
                            output_suffix= 'postproc.nii.gz')
        self.setup_postproc(os.path.join(self.config['FMRIPrepOptions']['OutputDirectory'], 'fmriprep'),
                            target_suffix=None,
                            output_dir=os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'betaseries_default'),
                            output_suffix='betaseries.nii.gz', beta_series=True)
        self.setup_roiextract(target_dir = os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'postproc_default'),
                              target_suffix= 'postproc.nii.gz',
                              output_dir= os.path.join(self.config['ProjectDirectory'],
                                           'data_ROI_ts', 'postproc_default'),
                              )
        self.setup_susan(os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'postproc_default'),
                            target_suffix='postproc.nii.gz',
                            output_dir=os.path.join(self.config['ProjectDirectory'], 'data_postproc',
                                                    'postproc_default'),
                            output_suffix='postproc_default.nii.gz')
        # processing_streams = self.get_processing_stream_names()
        # if processing_streams:
        #     for stream in processing_streams:
        #         self.update_processing_stream(stream,
        #                                       output_dir= os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'postproc_'+stream),
        #                                       output_suffix='postproc_'+stream+".nii.gz")
        #         self.update_processing_stream(stream,
        #                                       output_dir= os.path.join(self.config['ProjectDirectory'], 'data_postproc', 'betaseries_'+stream),
        #                                       output_suffix='betaseries_'+stream+".nii.gz", beta_series=True)
        self.setup_glm(self.config['ProjectDirectory'])

    def setup_glm(self, project_path):
        glm_config = GLMConfigParser()

        glm_config.config['ParentClpipeConfig'] = os.path.join(project_path, "clpipe_config.json")
        glm_config.config['TargetDirectory'] = os.path.join(project_path, "data_fmriprep", "fmriprep")
        glm_config.config['LogDirectory'] = os.path.join(project_path, "logs", "glm_setup_logs")

        glm_config.config['Level1Setups'][0]['TargetDirectory'] = os.path.join(project_path, "data_postproc2", "default")
        glm_config.config['Level1Setups'][0]['FSFDir'] = os.path.join(project_path, "l1_fsfs")
        glm_config.config['Level1Setups'][0]['EVDirectory'] = os.path.join(project_path, "data_onsets")
        glm_config.config['Level1Setups'][0]['ConfoundDirectory'] = os.path.join(project_path, "data_postproc2", "default")
        glm_config.config['Level1Setups'][0]['OutputDir'] = os.path.join(project_path, "l1_feat_folders")
        glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_gfeat_folders")
        glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_fsfs")

        glm_config.config_json_dump(project_path, "glm_config.json")
        shutil.copyfile(resource_filename('clpipe', 'data/l2_sublist.csv'), os.path.join(project_path, "l2_sublist.csv"))

    def setup_fmriprep_directories(self, bidsDir, workingDir, outputDir, log_dir = None):
        if bidsDir is not None:
            self.config['FMRIPrepOptions']['BIDSDirectory'] = os.path.abspath(bidsDir)
        if workingDir is not None:
            self.config['FMRIPrepOptions']['WorkingDirectory'] = os.path.abspath(workingDir)
        if outputDir is not None:
            self.config['FMRIPrepOptions']['OutputDirectory'] = os.path.abspath(outputDir)
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
        if target_suffix is not None:
            self.config[target_output]['TargetSuffix'] = target_suffix
        if output_suffix is not None:
            self.config[target_output]['OutputSuffix'] = output_suffix
        if log_dir is not None:
            self.config[target_output]['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config[target_output]['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs', log_target)

    def setup_heudiconv(self, dicom_directory, heuristic_file, output_directory):
        if dicom_directory is not None:
            self.config['DICOMToBIDSOptions']['DICOMDirectory'] = os.path.abspath(dicom_directory)
        if output_directory is not None:
            self.config['DICOMToBIDSOptions']['OutputDirectory'] = os.path.abspath(output_directory)
            os.makedirs(self.config['DICOMToBIDSOptions']['OutputDirectory'], exist_ok=True)
        if heuristic_file is not None:
            self.config['DICOMToBIDSOptions']['HeuristicFile'] = os.path.abspath(heuristic_file)

    def setup_dcm2bids(self, dicom_directory, heuristic_file, output_directory, dicom_format_string, log_dir = None):
        if dicom_directory is not None:
            self.config['DICOMToBIDSOptions']['DICOMDirectory'] = os.path.abspath(dicom_directory)
        if output_directory is not None:
            self.config['DICOMToBIDSOptions']['BIDSDirectory'] = os.path.abspath(output_directory)
        if heuristic_file is not None:
            self.config['DICOMToBIDSOptions']['ConversionConfig'] = os.path.abspath(heuristic_file)
        if dicom_format_string is not None:
            self.config['DICOMToBIDSOptions']['DICOMFormatString'] = dicom_format_string
        if log_dir is not None:
            self.config['DICOMToBIDSOptions']['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['DICOMToBIDSOptions']['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs', 'DCM2BIDS_logs')

    def setup_bids_validation(self, log_dir=None):
        if log_dir is not None:
            self.config['BIDSValidationOptions']['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['BIDSValidationOptions']['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs', 'bids_validation_logs')

    def setup_roiextract(self, target_dir, target_suffix, output_dir, log_dir = None):
        if target_dir is not None:
            self.config['ROIExtractionOptions']['TargetDirectory'] = os.path.abspath(target_dir)
        if output_dir is not None:
            self.config['ROIExtractionOptions']['OutputDirectory'] = os.path.abspath(output_dir)
        if target_suffix is not None:
            self.config['ROIExtractionOptions']['TargetSuffix'] = target_suffix
        if log_dir is not None:
            self.config['ROIExtractionOptions']['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['ROIExtractionOptions']['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs',
                                                                             'ROI_extraction_logs')

    def setup_susan(self, target_dir, target_suffix, output_dir, output_suffix, log_dir =None):
        if target_dir is not None:
            self.config['SUSANOptions']['TargetDirectory'] = os.path.abspath(target_dir)
        if output_dir is not None:
            self.config['SUSANOptions']['OutputDirectory'] = os.path.abspath(output_dir)
        if target_suffix is not None:
            self.config['SUSANOptions']['TargetSuffix'] = target_suffix
        if output_suffix is not None:
            self.config['SUSANOptions']['OutputSuffix'] = output_suffix
        if log_dir is not None:
            self.config['SUSANOptions']['LogDirectory'] = os.path.abspath(log_dir)
        else:
            self.config['SUSANOptions']['LogDirectory'] = os.path.join(self.config['ProjectDirectory'], 'logs',
                                                                               'SUSAN_logs')

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
            self.config['ProcessingStreams'][index][target_output]['OutputDirectory'] = os.path.abspath(output_dir)
            os.makedirs(self.config['ProcessingStreams'][index][target_output]['OutputDirectory'], exist_ok=True)
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

class GLMConfigParser:
    def __init__(self, glm_config_file = None):
        if glm_config_file is None:
            with resource_stream(__name__, 'data/defaultGLMConfig.json') as def_config:
                self.config = json.load(def_config)
        else:
            self.config = config_json_parser(glm_config_file)

    def config_json_dump(self, outputdir, filepath):
        if filepath is None:
            filepath = "defaultGLMConfig.json"
        outpath = os.path.join(os.path.abspath(outputdir), filepath)
        with open(outpath, 'w') as fp:
            json.dump(self.config, fp, indent="\t")
        return(outpath)


def file_folder_generator(basename, modality, target_suffix = None):
    if target_suffix is not None:
        basename = basename.replace(target_suffix, "")

    comps = basename.split("_")
    if comps[-1] is "":
        comps = comps[0:-1]
    sub = comps[0]
    ses = comps[1]
    front_matter = '_'.join(comps[0:-2])
    type = comps[-1]
    if 'ses-' in ses:
        path = os.path.join(sub, ses, modality, front_matter)
        return [sub, ses, modality, front_matter, type, path]
    else:
        ses = ''
        path = os.path.join(sub, modality, front_matter)
        return [sub, ses, modality, front_matter, type, path]

def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
