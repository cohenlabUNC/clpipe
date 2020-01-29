import numpy as np
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    from nilearn.input_data import NiftiSpheresMasker
    from nilearn.input_data import NiftiLabelsMasker
    from nilearn.input_data import NiftiMapsMasker
    from nilearn.image import concat_imgs
import os
import click
import sys
import logging
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser, file_folder_generator
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
@click.option('-target_suffix',
              help='Which target suffix to process. If a configuration file is provided with a target suffix, this argument is not necessary.')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the ROI extracted data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-task', help = 'Which task to process. If none, then all tasks are processed.')
@click.option('-atlas_name', help = "What atlas to use. Please refer to documentation, or use the command get_available_atlases to see which are available. When specified for a custom atlas, this is what the output files will be named.")
@click.option('-custom_atlas', help = 'A custom atlas image, in .nii or .nii.gz for label or maps, or a .txt tab delimited set of ROI coordinates if for a sphere atlas. Can not be specified in config.')
@click.option('-custom_label', help = 'A custom atlas label file. Can not be specified in config.')
@click.option('-custom_type', help = 'What type of atlas? (label, maps, or spheres). Can not be specified in config.')
@click.option('-radius', help = "If a sphere atlas, what radius sphere, in mm. Can not be specified in config.", default = '5')
@click.option('-overlap_ok', is_flag=True, default=False, help = "Are overlapping ROIs allowed?")
@click.option('-overwrite', is_flag=True, default=False, help = "Overwrite existing ROI timeseries?")
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
                        submit=False, single=False, overlap_ok= False, debug=False, overwrite = False):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ConfigParser()
    config.config_updater(config_file)
    if config_file is None:
        config_file = 'defaultConfig.json'

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
    else:
        config_string = ""
    if not subjects:
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['ROIExtractionOptions']['TargetDirectory'])
                   if os.path.isdir(os.path.join(config.config['ROIExtractionOptions']['TargetDirectory'], o)) and 'sub-' in o]
    else:
        sublist = subjects


    if atlas_name is not None:
        atlas_list = [atlas_name]
    else:
        atlas_list = config.config['ROIExtractionOptions']['Atlases']

    with resource_stream(__name__, 'data/atlasLibrary.json') as at_lib:
        atlas_library = json.load(at_lib)

    atlas_names = [atlas['atlas_name'] for atlas in atlas_library['Atlases']]
    logging.debug(atlas_names)
    custom_radius = radius
    submission_string = '''fmri_roi_extraction -config_file={config} -atlas_name={atlas} -single'''
    submission_string_custom = '''fmri_roi_extraction -config_file={config} -atlas_name={atlas} -custom_atlas={custom_atlas} -custom_label={custom_labels} -custom_type={custom_type} -single'''

    batch_manager = BatchManager(config.config['BatchConfig'], log_output_dir)
    batch_manager.update_mem_usage(config.config['ROIExtractionOptions']['MemoryUsage'])
    batch_manager.update_time(config.config['ROIExtractionOptions']['TimeUsage'])
    batch_manager.update_nthreads(config.config['ROIExtractionOptions']['NThreads'])
    batch_manager.update_email(config.config["EmailAddress"])
    batch_manager.createsubmissionhead()
    for subject in sublist:
        for cur_atlas in atlas_list:
            custom_flag = False
            sphere_flag = False
            if type(cur_atlas) is dict:
                logging.debug("Custom Dict Atlas")
                custom_flag = True
                atlas_name = cur_atlas['atlas_name']
                logging.debug(atlas_name)
                custom_atlas = cur_atlas['atlas_file']
                logging.debug(custom_atlas)
                custom_label = cur_atlas['atlas_labels']
                logging.debug(custom_label)
                custom_type = cur_atlas['atlas_type']
                logging.debug(custom_type)
                if 'sphere' in custom_type:
                    sphere_flag = True
                    custom_radius = cur_atlas['radius']
                    logging.debug(custom_radius)
            else:
                atlas_name = cur_atlas
            logging.debug(atlas_name)
            if atlas_name in atlas_names:
                logging.debug("Found atlas name in library")
                index = atlas_names.index(atlas_name)
                atlas_filename = atlas_library['Atlases'][index]['atlas_file']
                atlas_labels = atlas_library['Atlases'][index]['atlas_labels']
                atlas_type = atlas_library['Atlases'][index]['atlas_type']
                if 'sphere' in atlas_type:
                    sphere_flag = True
            else:
                logging.debug("Did Not Find Atlas Name in Library")
                custom_flag = True
                if any([not os.path.exists(custom_atlas), not os.path.exists(custom_label), custom_type not in ['label', 'maps', 'sphere']]):
                    raise ValueError('You are attempting to use a custom atlas, but have not specified one or more of the following: \n'
                                     '\t A custom atlas mask file (.nii or .nii.gz)'
                                     '\t A custom atlas label file (a file with information about the atlas)'
                                     '\t A custom atlas type (label, maps or spheres)')
                else:
                    atlas_filename = custom_atlas
                    atlas_labels = custom_label
                    atlas_type = custom_type
                    if 'sphere' in custom_type:
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
            if overlap_ok:
                sub_string_temp = sub_string_temp + ' -overlap_ok'

            sub_string_temp = sub_string_temp + ' ' + subject
            batch_manager.addjob(Job('ROI_extract_' + subject +'_'+atlas_name, sub_string_temp))
            if single:
                logging.info('Running Subject '+ subject + ' Atlas: '+ atlas_name + ' Atlas Type: ' + atlas_type)
                _fmri_roi_extract_subject(subject, task, atlas_name, atlas_filename, atlas_labels, atlas_type, custom_radius, custom_flag, config, overlap_ok, overwrite)
    if not single:
        if submit:
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())

def _fmri_roi_extract_subject(subject, task, atlas_name, atlas_filename, atlas_label, atlas_type,radius, custom_flag, config, overlap_ok, overwrite):
    if not custom_flag:
        atlas_path = resource_filename(__name__, atlas_filename)
        atlas_labelpath = resource_filename(__name__, atlas_label)
    else:
        atlas_path = os.path.abspath(atlas_filename)
        atlas_labelpath = os.path.abspath(atlas_label)

    search_string = os.path.abspath(
        os.path.join(config.config['ROIExtractionOptions']['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config['ROIExtractionOptions']['TargetSuffix']))
    logging.debug(search_string)
    subject_files = glob.glob(search_string, recursive=True)
    logging.debug(subject_files)
    if task is not None:
        subject_files = [x for x in subject_files if 'task-'+task in x]

    os.makedirs(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name),exist_ok=True)
    shutil.copy2(atlas_labelpath,config.config['ROIExtractionOptions']['OutputDirectory'])


    for file in subject_files:
       logging.info("Extracting the " + atlas_name + " atlas for " + file)
       mask_file = _mask_finder(file, config)
       if os.path.exists(mask_file):
           logging.info("Found brain mask "+mask_file + ". Using to mask ROI extraction.")
           file_outname = os.path.splitext(os.path.basename(file))[0]
           if '.nii' in file_outname:
               file_outname = os.path.splitext(file_outname)[0]
           if os.path.exists(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'],
                                          atlas_name + '/' + file_outname + "_atlas-" + atlas_name + '.csv')) and not overwrite:
               logging.info("File Exists! Skipping")
           else:
               try:
                  ROI_ts = _fmri_roi_extract_image(file, atlas_path, atlas_type, radius, overlap_ok, mask = mask_file)
               except ValueError as err:
                   logging.warning(err)
                   logging.warning("Extracting ROIs without using brain mask.")
                   ROI_ts = _fmri_roi_extract_image(file, atlas_path, atlas_type, radius, overlap_ok)
               temp_mask = concat_imgs([mask_file,mask_file])
               mask_ROIs = _fmri_roi_extract_image(temp_mask, atlas_path, atlas_type, radius, overlap_ok)
               mask_ROIs = np.nan_to_num(mask_ROIs)
               logging.debug(mask_ROIs[0])
               to_remove = [ind for ind,prop in np.ndenumerate(mask_ROIs[0]) if prop < config.config['ROIExtractionOptions']['PropVoxels']]
               logging.debug(to_remove)

               ROI_ts[:, to_remove] = np.nan
               np.savetxt(
                   os.path.join(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name),
                                file_outname + "_atlas-" + atlas_name + '.csv'), ROI_ts, delimiter=',')
               np.savetxt(
                   os.path.join(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name),
                                file_outname + "_atlas-" + atlas_name + '_voxel_prop.csv'), mask_ROIs[0], delimiter=',')
       else:
           logging.warning("Did not find brain mask: "+mask_file)
           if config.config['ROIExtractionOptions']['RequireMask']:
               logging.warning("Skipping this scan due to missing brain mask.")
           else:
                file_outname = os.path.splitext(os.path.basename(file))[0]
                if '.nii' in file_outname:
                    file_outname = os.path.splitext(file_outname)[0]
                if os.path.exists(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name+'/'+ file_outname +"_atlas-" + atlas_name+ '.csv')) and not overwrite:
                    logging.info("File Exists! Skipping")
                else:
                    ROI_ts = _fmri_roi_extract_image(file, atlas_path, atlas_type, radius, overlap_ok)
                    np.savetxt(os.path.join(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name), file_outname +"_atlas-" + atlas_name+ '.csv'), ROI_ts, delimiter=',')



def _fmri_roi_extract_image(data,  atlas_path, atlas_type, radius, overlap_ok,mask = None):
    if 'label' in atlas_type:
        logging.debug('Labels Extract')
        label_masker = NiftiLabelsMasker(atlas_path, mask_img=mask)
        timeseries = label_masker.fit_transform(data)
    if 'sphere' in atlas_type:
        atlas_path = np.loadtxt(atlas_path)
        logging.debug('Sphere Extract')
        spheres_masker = NiftiSpheresMasker(atlas_path, float(radius),mask_img=mask, allow_overlap = overlap_ok)
        timeseries = spheres_masker.fit_transform(data)
    if 'maps' in atlas_type:
        logging.debug('Maps Extract')
        maps_masker = NiftiMapsMasker(atlas_path,mask_img=mask, allow_overlap = overlap_ok)
        timeseries = maps_masker.fit_transform(data)
    timeseries[timeseries == 0.0] = np.nan

    return timeseries


@click.command()
def get_available_atlases():

    with resource_stream(__name__, 'data/atlasLibrary.json') as at_lib:
        atlas_library = json.load(at_lib)

    for atlas in atlas_library['Atlases']:

        print('Atlas Label: ' + atlas['atlas_name'])
        print('Atlas Type: ' + atlas['atlas_type'])
        print('Atlas Citation: ' + atlas['atlas_citation'])
        print('')

def _mask_finder(data, config):

    file_struct = file_folder_generator(os.path.basename(data), "func", target_suffix=config.config['ROIExtractionOptions']['TargetSuffix'])
    target_mask = os.path.join(config.config['FMRIPrepOptions']['OutputDirectory'], 'fmriprep', os.path.join(file_struct[-1])+'_desc-brain_mask.nii.gz')
    if not os.path.exists(target_mask):
        target_mask =os.path.join(config.config['FMRIPrepOptions']['OutputDirectory'], 'fmriprep', os.path.join(file_struct[-1])+'_desc-brain_mask.nii')
    return(target_mask)

