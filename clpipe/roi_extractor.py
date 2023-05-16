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
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser, file_folder_generator
import json
from pkg_resources import resource_stream, resource_filename
import glob
import shutil
from .errors import MaskFileNotFoundError

from .utils import get_logger, resolve_fmriprep_dir
from pathlib import Path

STEP_NAME = "roi_extraction"

def fmri_roi_extraction(subjects=None,config_file=None, target_dir=None, target_suffix = None, output_dir=None, task=None, log_output_dir=None,
                        atlas_name = None,
                        custom_atlas = None,
                        custom_label = None,
                        custom_type = None,
                        radius = '5',
                        submit=False, single=False, overlap_ok= False, debug=False, overwrite = False):
    config = ClpipeConfigParser()
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

    logger = get_logger(STEP_NAME, debug=debug, log_dir=Path(config.config["ProjectDirectory"]) / "logs")

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
    logger.debug(atlas_names)
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
        logger.info(f"Starting ROI extraction for suject: {subject}")
        for cur_atlas in atlas_list:
            custom_flag = False
            sphere_flag = False
            if type(cur_atlas) is dict:
                custom_flag = True
                atlas_name = cur_atlas['atlas_name']
                logger.info(f"Using Custom Dict Atlas: {atlas_name}")
                custom_atlas = cur_atlas['atlas_file']
                logger.debug(custom_atlas)
                custom_label = cur_atlas['atlas_labels']
                logger.debug(custom_label)
                custom_type = cur_atlas['atlas_type']
                logger.debug(custom_type)
                if 'sphere' in custom_type:
                    logger.debug("Sphere flag: ON")
                    sphere_flag = True
                    custom_radius = cur_atlas['radius']
                    logger.debug(custom_radius)
            else:
                atlas_name = cur_atlas
            logger.debug(atlas_name)
            if atlas_name in atlas_names:
                logger.debug("Found atlas name in library")
                index = atlas_names.index(atlas_name)
                atlas_filename = atlas_library['Atlases'][index]['atlas_file']
                atlas_labels = atlas_library['Atlases'][index]['atlas_labels']
                atlas_type = atlas_library['Atlases'][index]['atlas_type']
                if 'sphere' in atlas_type:
                    sphere_flag = True
            else:
                logger.debug("Did Not Find Atlas Name in Library")
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
                _fmri_roi_extract_subject(subject, task, atlas_name, atlas_filename, atlas_labels, atlas_type, custom_radius, custom_flag, config, overlap_ok, overwrite, logger)
    if not single:
        if submit:
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())

def _fmri_roi_extract_subject(subject, task, atlas_name, atlas_filename, atlas_label, atlas_type,radius, custom_flag, config, overlap_ok, overwrite, logger):
    logger.info('Running Subject '+ subject + ' Atlas: '+ atlas_name + ' Atlas Type: ' + atlas_type)
    
    if not custom_flag:
        atlas_path = resource_filename(__name__, atlas_filename)
        atlas_labelpath = resource_filename(__name__, atlas_label)
    else:
        atlas_path = os.path.abspath(atlas_filename)
        atlas_labelpath = os.path.abspath(atlas_label)
    logger.debug(f"Using atlas path: {atlas_path}")

    search_string = os.path.abspath(
        os.path.join(config.config['ROIExtractionOptions']['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config['ROIExtractionOptions']['TargetSuffix']))
    logger.debug(search_string)
    subject_files = glob.glob(search_string, recursive=True)
    if task is not None:
        logger.info(f"Checking for task {task} for subjects: {subject_files}")
        subject_files = [x for x in subject_files if 'task-'+task in x]
    logger.info(f"Processing subjects: {subject_files}")

    os.makedirs(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name),exist_ok=True)
    shutil.copy2(atlas_labelpath,config.config['ROIExtractionOptions']['OutputDirectory'])

    for file in subject_files:
        logger.info(f"Processing image: {Path(file).stem}")
        file_outname = os.path.splitext(os.path.basename(file))[0]
        if '.nii' in file_outname:
            file_outname = os.path.splitext(file_outname)[0]

        if os.path.exists(os.path.join(
            config.config['ROIExtractionOptions']['OutputDirectory'],
            atlas_name + '/' + file_outname + "_atlas-" + atlas_name + '.csv'
        )) and not overwrite:
            logger.info("File Exists! Skipping. Use -overwrite to reprocess.")
            continue

        found_mask = False
        fallback = False
        try:
            mask_file = _mask_finder(file, config, logger)
            found_mask = True
        except MaskFileNotFoundError:
            if config.config['ROIExtractionOptions']['RequireMask']:
                logger.warning("Skipping this scan due to missing brain mask.")
                continue
            else:
                logger.warning(
                    "Unable to find a mask for this image. Extracting ROIs without using brain mask."
                )
        else:
            try:
                logger.info("Starting masked ROI extraction...")
                # Attempt to run ROI extraction with mask
                ROI_ts = _fmri_roi_extract_image(
                    file, atlas_path, atlas_type, radius, overlap_ok, logger, mask = mask_file
                )
            except ValueError as ve:
                # Fallback for if any ROIs are outside of the mask region
                logger.warning(
                    ve.__str__() + ". Extracting ROIs without using brain mask."
                )
                fallback = True
        
        if not found_mask or fallback:
            logger.info("Starting non-masked ROI extraction...")
            ROI_ts = _fmri_roi_extract_image(
                file, atlas_path, atlas_type, radius, overlap_ok, logger
        )

        if fallback:
            temp_mask = concat_imgs([mask_file,mask_file])
            mask_ROIs = _fmri_roi_extract_image(temp_mask, atlas_path, atlas_type, radius, overlap_ok, logger)
            mask_ROIs = np.nan_to_num(mask_ROIs)
            logger.debug(mask_ROIs[0])
            to_remove = [ind for ind,prop in np.ndenumerate(mask_ROIs[0]) if prop < config.config['ROIExtractionOptions']['PropVoxels']]
            logger.debug(to_remove)
            ROI_ts[:, to_remove] = np.nan

            # Save ROI masked threshold timeseries
            np.savetxt(os.path.join(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name),
                file_outname + "_atlas-" + atlas_name + '_voxel_prop.csv'), mask_ROIs[0], delimiter=',')
        
        # Save the ROI timeseries
        np.savetxt(os.path.join(os.path.join(config.config['ROIExtractionOptions']['OutputDirectory'], atlas_name),
            file_outname + "_atlas-" + atlas_name + '.csv'), ROI_ts, delimiter=',')
        
        logger.info("Extraction completed.")


def _fmri_roi_extract_image(data,  atlas_path, atlas_type, radius, overlap_ok,logger,mask = None):
    if 'label' in atlas_type:
        logger.debug('Labels Extract')
        label_masker = NiftiLabelsMasker(atlas_path, mask_img=mask)
        timeseries = label_masker.fit_transform(data)
    if 'sphere' in atlas_type:
        atlas_path = np.loadtxt(atlas_path)
        logger.debug('Sphere Extract')
        spheres_masker = NiftiSpheresMasker(atlas_path, float(radius),mask_img=mask, allow_overlap = overlap_ok)
        timeseries = spheres_masker.fit_transform(data)
    if 'maps' in atlas_type:
        logger.debug('Maps Extract')
        maps_masker = NiftiMapsMasker(atlas_path,mask_img=mask, allow_overlap = overlap_ok)
        timeseries = maps_masker.fit_transform(data)
    timeseries[timeseries == 0.0] = np.nan

    return timeseries


def get_available_atlases():

    with resource_stream(__name__, 'data/atlasLibrary.json') as at_lib:
        atlas_library = json.load(at_lib)

    for atlas in atlas_library['Atlases']:

        print('Atlas Label: ' + atlas['atlas_name'])
        print('Atlas Type: ' + atlas['atlas_type'])
        print('Atlas Citation: ' + atlas['atlas_citation'])
        print('')

def _mask_finder(data, config, logger):
    """Search for a mask in the fmriprep output directory matching
    the name of the image targeted for roi_extraction"""

    file_struct = file_folder_generator(os.path.basename(data), "func", target_suffix=config.config['ROIExtractionOptions']['TargetSuffix'])
    logger.debug(f"Mask file structure: {file_struct}")

    fmriprep_dir = resolve_fmriprep_dir(config.config['FMRIPrepOptions']['OutputDirectory'])
    logger.debug(f"Searching for masks in: {fmriprep_dir}")

    target_mask = os.path.join(fmriprep_dir, os.path.join(file_struct[-1])+'_desc-brain_mask.nii.gz')
    if not os.path.exists(target_mask):
        logger.warn(f"No .nii.gz mask file found, searching for unzipped variant...")
        target_mask_unzipped =os.path.join(fmriprep_dir, os.path.join(file_struct[-1])+'_desc-brain_mask.nii')
        if not os.path.exists(target_mask_unzipped):
            raise MaskFileNotFoundError(f"No mask found on path: {target_mask}")
    logger.debug(f"Found matching mask: {target_mask}")
    return(target_mask)

