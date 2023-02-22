from dataclasses import dataclass
import marshmallow_dataclass
import json, yaml, os
import shutil
from pkg_resources import resource_stream, resource_filename
from .bids import DICOM_to_BIDS, BIDSValidator
from .fmri_prep import FMRIPrep
from .beta_series import BetaSeries
from .post_processing import PostProcessing
from .roi import ROIOptions
from .susan import SusanOptions
from .source_options import SourceOptions
from .post_processing2 import PostProcessing2
from .reho import ReHoExtraction
from .t2star import T2StarExtraction

@dataclass
class Config:
    #Add variable names exactly same as json file
    ProjectTitle: str
    @property
    def ProjectTitle(self):
        return self._ProjectTitle
    @ProjectTitle.setter
    def ProjectTitle(self, value):
        if value is not None:
            self._ProjectTitle = value

    Authors: str
    @property
    def Authors(self):
        return self._Authors
    @Authors.setter
    def Authors(self, value):
        if value is not None:
            self._Authors = value

    ProjectDirectory: str
    @property
    def ProjectDirectory(self):
        return self._ProjectDirectory
    @ProjectDirectory.setter
    def ProjectDirectory(self, value):
        if value is not None:
            self._ProjectDirectory = value

    EmailAddress: str
    @property
    def EmailAddress(self):
        return self._EmailAddress
    @EmailAddress.setter
    def EmailAddress(self, value):
        if value is not None:
            self._EmailAddress = value

    TempDirectory: str
    @property
    def TempDirectory(self):
        return self._TempDirectory
    @TempDirectory.setter
    def TempDirectory(self, value):
        if value is not None:
            self._TempDirectory = value

    SourceOptions: SourceOptions
    @property
    def SourceOptions(self):
        return self._SourceOptions
    @SourceOptions.setter
    def SourceOptions(self, value):
        if value is not None:
            self._SourceOptions = value

    DICOMToBIDSOptions: DICOM_to_BIDS
    @property
    def DICOMToBIDSOptions(self):
        return self._DICOMToBIDSOptions
    @DICOMToBIDSOptions.setter
    def DICOMToBIDSOptions(self, value):
        if value is not None:
            self._DICOMToBIDSOptions = value

    BIDSValidationOptions: BIDSValidator
    @property
    def BIDSValidationOptions(self):
        return self._BIDSValidationOptions
    @BIDSValidationOptions.setter
    def BIDSValidationOptions(self, value):
        if value is not None:
            self._BIDSValidationOptions = value

    FMRIPrepOptions: FMRIPrep
    @property
    def FMRIPrepOptions(self):
        return self._FMRIPrepOptions
    @FMRIPrepOptions.setter
    def FMRIPrepOptions(self, value):
        if value is not None:
            self._FMRIPrepOptions = value

    PostProcessingOptions: PostProcessing
    @property
    def PostProcessingOptions(self):
        return self._PostProcessingOptions
    @PostProcessingOptions.setter
    def PostProcessingOptions(self, value):
        if value is not None:
            self._PostProcessingOptions = value

    PostProcessingOptions2: PostProcessing2
    @property
    def PostProcessingOptions2(self):
        return self._PostProcessingOptions2
    @PostProcessingOptions2.setter
    def PostProcessingOptions2(self, value):
        if value is not None:
            self._PostProcessingOptions2 = value

    BetaSeriesOptions: BetaSeries
    @property
    def BetaSeriesOptions(self):
        return self._BetaSeriesOptions
    @BetaSeriesOptions.setter
    def BetaSeriesOptions(self, value):
        if value is not None:
            self._BetaSeriesOptions = value

    SUSANOptions: SusanOptions
    @property
    def SUSANOptions(self):
        return self._SUSANOptions
    @SUSANOptions.setter
    def SUSANOptions(self, value):
        if value is not None:
            self._SUSANOptions = value

    ProcessingStreams: list
    @property
    def ProcessingStreams(self):
        return self._ProcessingStreams
    @ProcessingStreams.setter
    def ProcessingStreams(self, value):
        if value is not None:
            self._ProcessingStreams = value

    ROIExtractionOptions: ROIOptions
    @property
    def ROIExtractionOptions(self):
        return self._ROIExtractionOptions
    @ROIExtractionOptions.setter
    def ROIExtractionOptions(self, value):
        if value is not None:
            self._ROIExtractionOptions = value

    ReHoExtraction: ReHoExtraction
    @property
    def ReHoExtraction(self):
        return self._ReHoExtraction
    @ReHoExtraction.setter
    def ReHoExtraction(self, value):
        if value is not None:
            self._ReHoExtraction = value

    T2StarExtraction: T2StarExtraction
    @property
    def T2StarExtraction(self):
        return self._T2StarExtraction
    @T2StarExtraction.setter
    def T2StarExtraction(self, value):
        if value is not None:
            self._T2StarExtraction = value

    RunLog: list
    @property
    def RunLog(self):
        return self._RunLog
    @RunLog.setter
    def RunLog(self, value):
        if value is not None:
            self._RunLog = value

    StatusCache: str
    @property
    def StatusCache(self):
        return self._StatusCache
    @StatusCache.setter
    def StatusCache(self, value):
        if value is not None:
            self._StatusCache = value

    BatchConfig: str
    @property
    def BatchConfig(self):
        return self._BatchConfig
    @BatchConfig.setter
    def BatchConfig(self, value):
        if value is not None:
            self._BatchConfig = value

    #Add this class to get a ordered dictionary in the dump method
    class Meta:
        ordered = True

    def setup_project(self, project_title, project_dir, source_data):
        self.ProjectTitle = project_title
        self.ProjectDirectory = os.path.abspath(project_dir)
        self.setup_dcm2bids(os.path.abspath(source_data),
                            os.path.join(self.ProjectDirectory, 'conversion_config.json'),
                            os.path.join(self.ProjectDirectory, 'data_BIDS'),
                            None)
        self.setup_bids_validation(None)
        self.setup_fmriprep_directories(os.path.join(self.ProjectDirectory, 'data_BIDS'),
                                        None, os.path.join(self.ProjectDirectory, 'data_fmriprep'))
        self.setup_postproc(os.path.join(self.FMRIPrepOptions.OutputDirectory, 'fmriprep'),
                            target_suffix= None,
                            output_dir= os.path.join(self.ProjectDirectory, 'data_postproc', 'postproc_default'),
                            output_suffix= 'postproc.nii.gz')
        self.setup_postproc(os.path.join(self.FMRIPrepOptions.OutputDirectory, 'fmriprep'),
                            target_suffix=None,
                            output_dir=os.path.join(self.ProjectDirectory, 'data_postproc', 'betaseries_default'),
                            output_suffix='betaseries.nii.gz', beta_series=True)
        self.setup_roiextract(target_dir = os.path.join(self.ProjectDirectory, 'data_postproc', 'postproc_default'),
                              target_suffix= 'postproc.nii.gz',
                              output_dir= os.path.join(self.ProjectDirectory,
                                           'data_ROI_ts', 'postproc_default'),
                              )
        self.setup_susan(os.path.join(self.ProjectDirectory, 'data_postproc', 'postproc_default'),
                            target_suffix='postproc.nii.gz',
                            output_dir=os.path.join(self.ProjectDirectory, 'data_postproc',
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
        self.setup_glm(self.ProjectDirectory)

    def setup_bids_validation(self, log_dir=None):
        if log_dir is not None:
            self.BIDSValidationOptions.LogDirectory = os.path.abspath(log_dir)
        else:
           self.BIDSValidationOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs', 'bids_validation_logs')
        os.makedirs(self.BIDSValidationOptions.LogDirectory, exist_ok=True)

    def setup_fmriprep_directories(self, bidsDir, workingDir, outputDir, log_dir = None):
        if bidsDir is not None:
            self.FMRIPrepOptions.BIDSDirectory = os.path.abspath(bidsDir)
            if not os.path.isdir(self.FMRIPrepOptions.BIDSDirectory):
                raise ValueError('BIDS Directory does not exist')
        if workingDir is not None:
            self.FMRIPrepOptions.WorkingDirectory = os.path.abspath(workingDir)
            os.makedirs(self.FMRIPrepOptions.WorkingDirectory, exist_ok=True)
        if outputDir is not None:
            self.FMRIPrepOptions.OutputDirectory = os.path.abspath(outputDir)
            os.makedirs(self.FMRIPrepOptions.OutputDirectory, exist_ok=True)
        if log_dir is not None:
            self.FMRIPrepOptions.LogDirectory = os.path.abspath(log_dir)
        else:
            self.FMRIPrepOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs', 'FMRIprep_logs')

    def setup_dcm2bids(self, dicom_directory, heuristic_file, output_directory, dicom_format_string, log_dir = None):
        if dicom_directory is not None:
            self.DICOMToBIDSOptions.DICOMDirectory = os.path.abspath(dicom_directory)
        if output_directory is not None:
            self.DICOMToBIDSOptions.BIDSDirectory = os.path.abspath(output_directory)
            os.makedirs(self.DICOMToBIDSOptions.BIDSDirectory, exist_ok=True)
        if heuristic_file is not None:
            self.DICOMToBIDSOptions.ConversionConfig = os.path.abspath(heuristic_file)
        if dicom_format_string is not None:
            self.DICOMToBIDSOptions.DICOMFormatString = dicom_format_string
        if log_dir is not None:
            self.DICOMToBIDSOptions.LogDirectory = os.path.abspath(log_dir)
        else:
            self.DICOMToBIDSOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs', 'DCM2BIDS_logs')
        os.makedirs(self.DICOMToBIDSOptions.LogDirectory, exist_ok=True)

        # Create a default .bidsignore file
        bids_ignore_path = os.path.join(self.DICOMToBIDSOptions.BIDSDirectory, ".bidsignore")
        if not os.path.exists(bids_ignore_path):
            with open(bids_ignore_path, 'w') as bids_ignore_file:
                # Ignore dcm2bid's auto-generated directory
                bids_ignore_file.write("tmp_dcm2bids")


    def setup_bids_validation(self, log_dir=None):
        if log_dir is not None:
            self.BIDSValidationOptions.LogDirectory = os.path.abspath(log_dir)
        else:
            self.BIDSValidationOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs', 'bids_validation_logs')
        os.makedirs(self.BIDSValidationOptions.LogDirectory, exist_ok=True)

    def setup_fmriprep_directories(self, bidsDir, workingDir, outputDir, log_dir = None):
        if bidsDir is not None:
            self.FMRIPrepOptions.BIDSDirectory = os.path.abspath(bidsDir)
            if not os.path.isdir(self.FMRIPrepOptions.BIDSDirectory):
                raise ValueError('BIDS Directory does not exist')
        if workingDir is not None:
            self.FMRIPrepOptions.WorkingDirectory = os.path.abspath(workingDir)
            os.makedirs(self.FMRIPrepOptions.WorkingDirectory, exist_ok=True)
        if outputDir is not None:
            self.FMRIPrepOptions.OutputDirectory = os.path.abspath(outputDir)
            os.makedirs(self.FMRIPrepOptions.OutputDirectory, exist_ok=True)
        if log_dir is not None:
            self.FMRIPrepOptions.LogDirectory = os.path.abspath(log_dir)
        else:
            self.FMRIPrepOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs', 'FMRIprep_logs')

    def setup_postproc(self, target_dir, target_suffix, output_dir, output_suffix, beta_series = False, log_dir = None):
        if beta_series:
            log_target = 'betaseries_logs'
            if target_dir is not None:
                self.BetaSeriesOptions.TargetDirectory = os.path.abspath(target_dir)
            if output_dir is not None:
                self.BetaSeriesOptions.OutputDirectory = os.path.abspath(output_dir)
                os.makedirs(self.BetaSeriesOptions.OutputDirectory, exist_ok=True)
            if target_suffix is not None:
                self.BetaSeriesOptions.TargetSuffix = target_suffix
            if output_suffix is not None:
                self.BetaSeriesOptions.OutputSuffix = output_suffix
            if log_dir is not None:
                self.BetaSeriesOptions.LogDirectory = os.path.abspath(log_dir)
            else:
                self.BetaSeriesOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs', log_target)
            os.makedirs(self.BetaSeriesOptions.LogDirectory, exist_ok=True)
        else:
            log_target = 'postproc_logs'
            if target_dir is not None:
                self.PostProcessingOptions.TargetDirectory = os.path.abspath(target_dir)
            if output_dir is not None:
                self.PostProcessingOptions.OutputDirectory = os.path.abspath(output_dir)
                os.makedirs(self.PostProcessingOptions.OutputDirectory, exist_ok=True)
            if target_suffix is not None:
                self.PostProcessingOptions.TargetSuffix = target_suffix
            if output_suffix is not None:
                self.PostProcessingOptions.OutputSuffix = output_suffix
            if log_dir is not None:
                self.PostProcessingOptions.LogDirectory = os.path.abspath(log_dir)
            else:
                self.PostProcessingOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs', log_target)
            os.makedirs(self.PostProcessingOptions.LogDirectory, exist_ok=True)

    def setup_heudiconv(self, dicom_directory, heuristic_file, output_directory):
        if dicom_directory is not None:
            self.DICOMToBIDSOptions.DICOMDirectory = os.path.abspath(dicom_directory)
        if output_directory is not None:
            self.DICOMToBIDSOptions.OutputDirectory = os.path.abspath(output_directory)
            os.makedirs(self.DICOMToBIDSOptions.OutputDirectory, exist_ok=True)
        if heuristic_file is not None:
            self.DICOMToBIDSOptions.HeuristicFile = os.path.abspath(heuristic_file)

    def setup_roiextract(self, target_dir, target_suffix, output_dir, log_dir = None):
        if target_dir is not None:
            self.ROIExtractionOptions.TargetDirectory = os.path.abspath(target_dir)
            if not os.path.isdir(self.ROIExtractionOptions.TargetDirectory):
                raise ValueError('Target Directory does not exist')
        if output_dir is not None:
            self.ROIExtractionOptions.OutputDirectory = os.path.abspath(output_dir)
            os.makedirs(self.ROIExtractionOptions.OutputDirectory, exist_ok=True)
        if target_suffix is not None:
            self.ROIExtractionOptions.TargetSuffix = target_suffix
        if log_dir is not None:
            self.ROIExtractionOptions.LogDirectory = os.path.abspath(log_dir)
        else:
            self.ROIExtractionOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs',
                                                                             'ROI_extraction_logs')
        os.makedirs(self.ROIExtractionOptions.LogDirectory, exist_ok=True)

    def setup_susan(self, target_dir, target_suffix, output_dir, output_suffix, log_dir =None):
        if target_dir is not None:
            self.SUSANOptions.TargetDirectory = os.path.abspath(target_dir)
            if not os.path.isdir(self.SUSANOptions.TargetDirectory):
                raise ValueError('Target Directory does not exist')
        if output_dir is not None:
            self.SUSANOptions.OutputDirectory = os.path.abspath(output_dir)
            os.makedirs(self.SUSANOptions.OutputDirectory, exist_ok=True)
        if target_suffix is not None:
            self.SUSANOptions.TargetSuffix = target_suffix
        if output_suffix is not None:
            self.SUSANOptions.OutputSuffix = output_suffix
        if log_dir is not None:
            self.SUSANOptions.LogDirectory = os.path.abspath(log_dir)
        else:
            self.SUSANOptions.LogDirectory = os.path.join(self.ProjectDirectory, 'logs',
                                                                               'SUSAN_logs')
        os.makedirs(self.SUSANOptions.LogDirectory, exist_ok=True)

    def setup_glm(self, project_path):
        glm_config = GLMConfigParser()

        glm_config.config['GLMSetupOptions']['ParentClpipeConfig'] = os.path.join(project_path, "clpipe_config.json")
        glm_config.config['GLMSetupOptions']['TargetDirectory'] = os.path.join(project_path, "data_fmriprep", "fmriprep")
        glm_config.config['GLMSetupOptions']['MaskFolderRoot'] = glm_config.config['GLMSetupOptions']['TargetDirectory']
        glm_config.config['GLMSetupOptions']['PreppedDataDirectory'] =  os.path.join(project_path, "data_GLMPrep")
        os.mkdir(os.path.join(project_path, "data_GLMPrep"))

        glm_config.config['Level1Setups'][0]['TargetDirectory'] = os.path.join(project_path, "data_GLMPrep")
        glm_config.config['Level1Setups'][0]['FSFDir'] = os.path.join(project_path, "l1_fsfs")
        glm_config.config['Level1Setups'][0]['EVDirectory'] = os.path.join(project_path, "data_onsets")
        glm_config.config['Level1Setups'][0]['ConfoundDirectory'] = os.path.join(project_path, "data_GLMPrep")
        os.mkdir(os.path.join(project_path, "l1_fsfs"))
        os.mkdir(os.path.join(project_path, "data_onsets"))
        glm_config.config['Level1Setups'][0]['OutputDir'] = os.path.join(project_path, "l1_feat_folders")

        os.mkdir(os.path.join(project_path, "l1_feat_folders"))
        glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_gfeat_folders")
        glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_fsfs")

        os.mkdir(os.path.join(project_path, "l2_fsfs"))
        os.mkdir(os.path.join(project_path, "l2_gfeat_folders"))

        glm_config.config_json_dump(project_path, "glm_config.json")
        shutil.copy(resource_filename('clpipe', 'data/l2_sublist.csv'), os.path.join(project_path, "l2_sublist.csv"))
        glm_config.config['GLMSetupOptions']['LogDirectory'] = os.path.join(project_path, "logs", "glm_setup_logs")
        os.mkdir(os.path.join(project_path, "logs", "glm_setup_logs"))
    
#Config parser for GLM Config
def config_json_parser(json_path):
    with open(os.path.abspath(json_path), "r") as config_file:
        config = json.load(config_file)
    return config

class GLMConfigParser:
    def __init__(self, glm_config_file = None):
        if glm_config_file is None:
            with resource_stream(__name__, '../data/defaultGLMConfig.json') as def_config:
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
    
def getConfig(json_file = None, yaml_file = None):
    if(json_file == None and yaml_file == None):
        json_file = '/nas/longleaf/home/mbhavith/DEPENd_Lab/clpipe/clpipe/data/defaultConfig.json'

    #Generate schema from given dataclasses
    ConfigSchema = marshmallow_dataclass.class_schema(Config)

    if(json_file == None and yaml_file):
        with open(yaml_file) as f:
            configDict = yaml.safe_load(f)
    else:
        with open(json_file) as f:
            configDict = json.load(f)
    #Change key name to 'Authors'
    newNames = list(configDict.keys())
    newNames[1] = 'Authors'
    configDict = dict(zip(newNames, list(configDict.values())))
    return ConfigSchema().load(configDict)

def dumpConfig(config, outputdir, filepath, yaml_file = False):
    if filepath is None:
            filepath = "defaultConfig.json"
    outpath = os.path.join(os.path.abspath(outputdir), filepath)

    #Generate schema from given dataclasses
    ConfigSchema = marshmallow_dataclass.class_schema(Config)
    configDict = ConfigSchema().dump(config)
    
    with open(outpath, 'w') as fp:
            json.dump(configDict, fp, indent="\t")

    if(yaml_file):
        with open('newConfig.json', 'r') as json_in:
            conf = json.load(json_in)
        with open('newConfig.yaml', 'w') as yaml_out:
            yaml.dump(conf, yaml_out, sort_keys=False)
        os.remove('newConfig.json')
    return(outpath)
