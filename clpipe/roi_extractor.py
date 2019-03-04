import numpy as np
from nilearn.input_data import NiftiSpheresMasker
from nilearn.input_data import NiftiLabelsMasker
from nilearn.input_data import NiftiMapsMasker
from nilearn.input_data import NiftiMasker
import os
import click
import sys
import logging
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
from .error_handler import exception_handler
import json
from pkg_resources import resource_stream, resource_filename

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories. This will extract all ROI sets specified in the configuration file.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which postprocessed directory to process. If a configuration file is provided with a target directory, this argument is not necessary.')
@click.option('-target_suffix', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which target suffix to process. If a configuration file is provided with a target suffix, this argument is not necessary.')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the ROI extracted data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-task', help = 'Which task to process. If none, then all tasks are processed.')
@click.option('-atlas', help = "Which prespecified atlas to use. Please refer to documentation, or use the command get_available_atlases to see which are available. Not needed if specified in config.")
@click.option('-custom_atlas', help = 'A custom atlas image, in .nii or .nii.gz for label or maps, or a .txt tab delimited set of ROI coordinates if for a sphere atlas. Not needed if specified in config.')
@click.option('-custom_label', help = 'A custom atlas label file. Not needed if specified in config.')
@click.option('-custom_type', help = 'What type of atlas? (label, maps, or spheres). Not needed if specified in config.')
@click.option('-radius', help = "If a sphere altas, what radius sphere, in mm. Not needed if specified in config.", default = 5.0)
@click.option('-log_output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files (such as SLURM output files). If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-single', is_flag=True, default=False, help='Flag to directly run command. Used internally.')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def fmri_roi_extraction(subjects=None,config_file=None, target_dir=None, output_dir=None, task=None, log_output_dir=None,
                        atlas = None,
                        custom_atlas = None,
                        custom_label = None,
                        custom_type = None,
                        submit=False, single=False, debug=False):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = ConfigParser()
    config.config_updater(config_file)

    roi_extract_config = config.config['ROIExtractionOptions']



    if not all([config.config['ROIExtractionOptions']['TargetDirectory'], config.config['ROIExtractionOptions']['OutputDirectory'],
                config.config['ROIExtractionOptions']['TargetSuffix']]):
        raise ValueError(
            'Please make sure the BIDS, working and output directories are specified in either the configfile or in the command. At least one is not specified.')
    if log_output_dir is not None:
        if os.path.isdir(log_output_dir):
            log_output_dir = os.path.abspath(log_output_dir)
        else:
            log_output_dir = os.path.abspath(log_output_dir)
            os.makedirs(log_output_dir, exist_ok=True)
    else:
        log_output_dir = os.path.join(config.config['FMRIPrepOptions']['OutputDirectory'], "batchOutput")
        os.makedirs(log_output_dir, exist_ok=True)

    atlas_library = json.load(resource_stream(__name__, 'data/atlasLibrary.json'))
    atlas_names = [atlas['atlas_name'] for atlas in atlas_library['Atlases']]
    if atlas in atlas_names:
        index = atlas_names.index(atlas)
        atlas_filename = atlas_library['Atlases'][index]['atlas_file']
        atlas_labels = atlas_library['Atlases'][index]['atlas_labels']
        atlas_type = atlas_library['Atlases'][index]['atlas_type']
    else:
        if any([not os.path.exists(custom_atlas), not os.path.exists(custom_label), custom_type not in ['label', 'maps', 'spheres']]):
            raise ValueError('You are attempting to use a custom atlas, but have not specified one or more of the following: \n'
                             '\t A custom atlas mask file (.nii or .nii.gz)' 
                             '\t A custom atlas label file (whitespace delimited .txt file)' 
                             '\t A custom atlas type (label, maps or spheres)')
        else:
            atlas_filename = custom_atlas
            atlas_labels = custom_label
            atlas_type = custom_type






def _fmri_roi_extraction(data, atlas_filename=None, atlas_type = None, option=None, brain_mask=None, resampling_target='data', background_label=0,
                   custom_atlas=None, custom_label=None, custom_type=None,
                   radius=5.0, allow_overlap=True, standardize=True,
                   detrend=True, TR=None, smoothing_fwhm=None, high_pass=None, low_pass=None,
                   mask_img=None, sessions=None, sample_mask=None, mask_strategy='epi', target_affine=None):



    if atlas_type is 'label':
        label_masker = NiftiLabelsMasker(resource_filename(__name__,atlas_filename), background_label=background_label, mask_img=brain_mask,
                                         smoothing_fwhm=smoothing_fwhm, standardize=standardize,
                                         detrend=detrend, low_pass=low_pass, high_pass=high_pass, t_r=TR,
                                         resampling_target=resampling_target, verbose=0)
        timeseries = label_masker.fit_transform(data)
    if atlas_type is 'sphere':
        spheres_masker = NiftiSpheresMasker(resource_filename(__name__,atlas_filename), radius=radius, mask_img=brain_mask,
                                            allow_overlap=allow_overlap, smoothing_fwhm=smoothing_fwhm,
                                            standardize=standardize,
                                            detrend=detrend, low_pass=low_pass, high_pass=high_pass, t_r=TR, verbose=0)
        timeseries = spheres_masker.fit_transform(data)
    if atlas_type is 'maps':
        maps_masker = NiftiMapsMasker(resource_filename(__name__,atlas_filename), mask_img=brain_mask, allow_overlap=allow_overlap,
                                      smoothing_fwhm=smoothing_fwhm, standardize=standardize,
                                      detrend=detrend, low_pass=low_pass, high_pass=high_pass, t_r=TR,
                                      resampling_target=resampling_target, verbose=0)
        timeseries = maps_masker.fit_transform(data)


    return timeseries, atlas_filename, atlas_labels