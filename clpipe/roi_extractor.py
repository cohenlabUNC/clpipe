import numpy as np
from nilearn.input_data import NiftiSpheresMasker
from nilearn.input_data import NiftiLabelsMasker
from nilearn.input_data import NiftiMapsMasker
import os
import click
import sys
import logging
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
from .error_handler import exception_handler
import json
from pkg_resources import resource_stream, resource_filename
import glob
import shutil

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
@click.option('-atlas_name', help = "What atlas to use. Please refer to documentation, or use the command get_available_atlases to see which are available. When specified for a custom atlas, this is what the output files will be named.")
@click.option('-custom_atlas', help = 'A custom atlas image, in .nii or .nii.gz for label or maps, or a .txt tab delimited set of ROI coordinates if for a sphere atlas. Not needed if specified in config.')
@click.option('-custom_label', help = 'A custom atlas label file. Not needed if specified in config.')
@click.option('-custom_type', help = 'What type of atlas? (label, maps, or spheres). Not needed if specified in config.')
@click.option('-radius', help = "If a sphere atlas, what radius sphere, in mm. Not needed if specified in config.", default = '5')
@click.option('-log_output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files (such as SLURM output files). If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-single', is_flag=True, default=False, help='Flag to directly run command. Used internally.')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def fmri_roi_extraction(subjects=None,config_file=None, target_dir=None, target_suffix = None, output_dir=None, task=None, log_output_dir=None,
                        atlas_name = None,
                        custom_atlas = None,
                        custom_label = None,
                        custom_type = None,
                        radius = '5',
                        submit=False, single=False, debug=False):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = ConfigParser()
    config.config_updater(config_file)


    config.setup_roiextract(target_dir, target_suffix, output_dir)

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
        log_output_dir = os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], "BatchOutput")
        os.makedirs(log_output_dir, exist_ok=True)

    if not single:
        config_string = config.config_json_dump(config.config['ROIExtractionOptions']['OutputDirectory'],
                                os.path.basename(config_file))

    if not subjects:
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['ROIExtractionOptions']['TargetDirectory'])
                   if os.path.isdir(os.path.join(config.config['ROIExtractionOptions']['TargetDirectory'], o)) and 'sub-' in o]
    else:
        sublist = subjects


    if atlas_name is not None:
        atlas_list = [atlas_name]
    else:
        atlas_list = config.config['ROIExtractionOptions']['Atlases']

    atlas_library = json.load(resource_stream(__name__, 'data/atlasLibrary.json'))
    atlas_names = [atlas['atlas_name'] for atlas in atlas_library['Atlases']]
    custom_radius = radius
    submission_string = '''fmri_roi_extraction -config_file={config} -atlas={atlas} -single'''
    submission_string_custom = '''fmri_roi_extraction -config_file={config} -atlas={atlas} -custom_atlas={custom_atlas_file} -custom_label={custom_labels} -custom_type={custom_type} -single'''

    batch_manager = BatchManager(config.config['BatchConfig'], log_output_dir)
    batch_manager.update_mem_usage(config.config['ROIExtractionOptions']['PostProcessingMemoryUsage'])
    batch_manager.update_time(config.config['ROIExtractionOptions']['PostProcessingTimeUsage'])
    batch_manager.update_nthreads(config.config['ROIExtractionOptions']['NThreads'])
    batch_manager.createsubmissionhead()
    for subject in sublist:
        for cur_atlas in atlas_list:
            custom_flag = False
            sphere_flag = True
            if type(cur_atlas) is dict:
                custom_flag = True
                atlas_name = cur_atlas['atlas_name']
                custom_atlas = cur_atlas['atlas_filename']
                custom_label = cur_atlas['atlas_labels']
                custom_type = cur_atlas['atlas_type']
                if custom_type is 'spheres':
                    sphere_flag = True
                    custom_radius = cur_atlas['radius']
            else:
                atlas_name = cur_atlas

            if atlas_name in atlas_names:
                index = atlas_names.index(atlas_name)
                atlas_filename = atlas_library['Atlases'][index]['atlas_file']
                atlas_labels = atlas_library['Atlases'][index]['atlas_labels']
                atlas_type = atlas_library['Atlases'][index]['atlas_type']
                if custom_type is 'spheres':
                    sphere_flag = True
            else:
                if any([not os.path.exists(custom_atlas), not os.path.exists(custom_label), custom_type not in ['label', 'maps', 'spheres']]):
                    raise ValueError('You are attempting to use a custom atlas, but have not specified one or more of the following: \n'
                                     '\t A custom atlas mask file (.nii or .nii.gz)' 
                                     '\t A custom atlas label file (a file with information about the atlas)' 
                                     '\t A custom atlas type (label, maps or spheres)')
                else:
                    atlas_filename = custom_atlas
                    atlas_labels = custom_label
                    atlas_type = custom_type
                    if custom_type is 'spheres':
                        sphere_flag = True
            if custom_flag:
                sub_string_temp = submission_string_custom.format(
                    config = config_string,
                    atlas = atlas_name,
                    custom_atlas = atlas_filename,
                    custom_labels = atlas_labels,
                    custom_type = atlas_type
                )
            else:
                sub_string_temp = submission_string.format(
                    config=config_string,
                    atlas=atlas_name,
                )
            if sphere_flag:
                sub_string_temp = sub_string_temp + ' -radius=' +custom_radius
            if task is not None:
                sub_string_temp = sub_string_temp + ' -task='+task

            sub_string_temp = sub_string_temp + ' ' + subject
            batch_manager.addjob(Job('ROI_extract_' + subject +'_'+atlas_name, sub_string_temp))
            if single:
                logging.info('Running Subject '+ subject + ' Atlas: '+ atlas_name)
                _fmri_roi_extract_subject(subject, task, atlas_name, atlas_filename, atlas_labels, atlas_type, custom_radius, custom_flag, config)
    if not single:
        if submit:
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())

def _fmri_roi_extract_subject(subject, task, atlas_name, atlas_filename, atlas_label, atlas_type,radius, custom_flag, config):
    if not custom_flag:
        atlas_path = resource_filename(__name__, atlas_filename)
    else:
        atlas_path = os.path.abspath(atlas_filename)

    search_string = os.path.abspath(
        os.path.join(config.config['ROIExtractionOptions']['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config['ROIExtractionOptions']['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)
    if task is not None:
        subject_files = [x for x in subject_files if 'task-'+task in x]

    os.makedirs(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name),exist_ok=True)
    shutil.copy2(atlas_label,config.config['ROIExtractionOptions']['OutputDirectory'])

    for file in subject_files:
       ROI_ts = _fmri_roi_extract_image(file, atlas_path, atlas_type, radius)
       file_outname = os.path.splitext(os.path.basename(file))[0]
       if '.nii' in file_outname:
           file_outname = os.path.splitext(file_outname)[0]
       np.savetxt(os.path.join(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name), file_outname + '.csv'), ROI_ts, delimiter=',')


def _fmri_roi_extract_image(data, atlas_path, atlas_type, radius):

    if atlas_type is 'label':
        label_masker = NiftiLabelsMasker(atlas_path)
        timeseries = label_masker.fit_transform(data)
    if atlas_type is 'sphere':
        spheres_masker = NiftiSpheresMasker(atlas_path, float(radius))
        timeseries = spheres_masker.fit_transform(data)
    if atlas_type is 'maps':
        maps_masker = NiftiMapsMasker(atlas_path)
        timeseries = maps_masker.fit_transform(data)


    return timeseries