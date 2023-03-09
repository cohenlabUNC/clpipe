import os
import glob

from clpipe.utils import add_file_handler, get_logger
from .batch_manager import BatchManager, Job
from .postprocutils.utils import scrub_setup
from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import sys
import site
path1 = sys.path
path1.insert(0, site.USER_SITE)
sys.path = path1
sys.path = path1[1:]
import nipype.interfaces.fsl as fsl  # fsl
import nipype.pipeline.engine as pe  # pypeline engine
from nipype.interfaces.utility import IdentityInterface
import nibabel as nib
import pandas
import re
import numpy as np

STEP_NAME = "glm_setup"
DEPRECATION_MSG = "glm setup's processing functions are now deprecated should be performed with postproc2."


def glm_setup(subjects = None, config_file=None, glm_config_file = None,
                     submit=False, batch=True, debug = False, drop_tps = None):
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    logger = get_logger(STEP_NAME, debug=debug, log_dir=os.path.join(config.config["ProjectDirectory"], "logs"))

    glm_config = GLMConfigParser(glm_config_file)

    try:
        # This working indicates the user has a glm_config file from < v1.7.4
        # In this case, carry on as normal but warn the user of deprecation
        task = glm_config.config['GLMSetupOptions']['TaskName']
        logger.warn(DEPRECATION_MSG)
    except KeyError:
        # No 'GLMSetupOptions' means the user has a glm_config file from >= v1.7.4
        # Exit this step with a deprecation error
        logger.error(DEPRECATION_MSG)
        sys.exit(1)
    
    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(glm_config.config['GLMSetupOptions']['TargetDirectory'])
                   if os.path.isdir(os.path.join(glm_config.config['GLMSetupOptions']['TargetDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    submission_string = '''glm_setup -config_file={config} -glm_config_file={glm_config} -single {debug} {sub} '''
    if debug:
        debug_string = '-debug'
    else:
        debug_string = ''
    if batch:
        batch_manager = BatchManager(config.config['BatchConfig'], glm_config.config['GLMSetupOptions']['LogDirectory'])
        batch_manager.update_mem_usage(glm_config.config['GLMSetupOptions']['MemoryUsage'])
        batch_manager.update_time(glm_config.config['GLMSetupOptions']['TimeUsage'])
        batch_manager.update_nthreads(glm_config.config['GLMSetupOptions']['NThreads'])
        batch_manager.update_email(config.config["EmailAddress"])
        for sub in sublist:
            sub_string_temp = submission_string.format(
                config=os.path.abspath(config_file),
                glm_config=os.path.abspath(glm_config_file),
                sub=sub,
                debug = debug_string
            )

            batch_manager.addjob(Job("GLM_Setup" + sub, sub_string_temp))
        if submit:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.print_jobs()
    else:
        for sub in sublist:
            logger.info('Running Subject ' + sub)
            _glm_prep(glm_config, sub, task, drop_tps, logger)


def _glm_prep(glm_config, subject, task, drop_tps, logger):
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


    search_string = os.path.abspath(
        os.path.join(glm_config.config["GLMSetupOptions"]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + glm_config.config["GLMSetupOptions"]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)

    if not subject_files:
        raise ValueError(f"No subject found matching: {subject}")

    glm_setup = pe.Workflow(name='glm_setup')
    glm_setup.base_dir = os.path.join(glm_config.config["GLMSetupOptions"]['WorkingDirectory'], "sub-"+subject)
    input_node = pe.Node(IdentityInterface(fields=['in_file', 'out_file', 'mask_file']), name='input')
    strip = pe.Node(fsl.BinaryMaths(operation = 'mul'), name="mask_apply")
    resample = pe.Node(fsl.FLIRT(apply_xfm = True,
                                 reference = glm_config.config["GLMSetupOptions"]["ReferenceImage"],
                                 uses_qform = True),
                                 name="resample")
    glm_setup.connect(input_node, 'out_file', resample, 'out_file')
    if drop_tps is not None:
        drop_tps_data = pandas.read_csv(drop_tps)
        drop = pe.Node(fsl.ExtractROI(), name = "drop_tps")
        drop.inputs.t_min = 0
        glm_setup.connect(input_node, "in_file", drop, "in_file")


    if glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
        if drop_tps is None:
           glm_setup.connect([(input_node, strip, [('in_file', 'in_file'),
                                         ('mask_file', 'operand_file')])])
        else:
            glm_setup.connect(drop, "roi_file", strip, "in_file")
            glm_setup.connect(input_node, "mask_file", strip, "operand_file")

    if glm_config.config["GLMSetupOptions"]["SUSANSmoothing"]:
        sus = pe.Node(fsl.SUSAN(), name="susan_smoothing")
        sus.inputs.brightness_threshold = glm_config.config["GLMSetupOptions"]['SUSANOptions']['BrightnessThreshold']
        sus.inputs.fwhm = glm_config.config["GLMSetupOptions"]['SUSANOptions']['FWHM']

        if glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
            glm_setup.connect(strip, 'out_file', sus, 'in_file')
        elif drop_tps is not None:
            glm_setup.connect(drop, 'roi_file', sus, 'in_file')
        else:
            glm_setup.connect(input_node, 'in_file', sus, 'in_file')

    if glm_config.config["GLMSetupOptions"]["SUSANSmoothing"]:
        glm_setup.connect(sus, 'smoothed_file', resample, 'in_file')
    elif glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
        glm_setup.connect(strip, 'out_file', resample, 'in_file')
    elif drop_tps is not None:
        glm_setup.connect(drop, 'roi_file', resample, 'in_file')
    else:
        glm_setup.connect(input_node, 'in_file', resample, 'in_file')

    if drop_tps is not None:
        drop_tps_data = pandas.read_csv(drop_tps)

    images_to_process = []

    for image in subject_files:
        if task is None or 'task-' + task + '_' in image:
            images_to_process.append(image)

    if len(images_to_process) == 0:
        raise ValueError(f"No task found matching: task-{task} for subject {subject}")

    for image in images_to_process:
        logger.info('Processing ' + image)
        confounds = None
        try:
            if glm_config.config["GLMSetupOptions"]['PrepareConfounds']:
                confound_file = _find_confounds(glm_config, image)
                if not os.path.exists(confound_file):
                    raise ValueError("Cannot find confound file: "+ confound_file)
                confounds = pandas.read_table(confound_file, dtype="float", na_values="n/a")
                if len(glm_config.config["GLMSetupOptions"]['Confounds']) > 0:
                    cons_re = [re.compile(regex_wildcard(co)) for co in glm_config.config["GLMSetupOptions"]['Confounds']]
                    target_cols = []
                    for reg in cons_re:
                        logger.debug(str([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None]))
                        target_cols.extend([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                    logger.debug("Confound Columns " + str(target_cols))
                    confounds_mat = confounds[target_cols]
                if len(glm_config.config["GLMSetupOptions"]['ConfoundsQuad']) > 0:
                    cons_re = [re.compile(regex_wildcard(co)) for co in glm_config.config["GLMSetupOptions"]['ConfoundsQuad']]
                    target_cols = []
                    for reg in cons_re:
                        target_cols.extend(
                            [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                    logger.debug("Quad Columns " + str(target_cols))
                    confounds_quad_mat = confounds[target_cols]
                    confounds_quad_mat.rename(columns =lambda x: x+"_quad", inplace = True)
                    confounds_quad_mat = confounds_quad_mat**2
                    confounds_mat = pandas.concat([confounds_mat,confounds_quad_mat],axis=1, ignore_index=True)
                    logger.debug(str(confounds_mat.shape))
                if len(glm_config.config["GLMSetupOptions"]['ConfoundsDerive']) > 0:
                    cons_re = [re.compile(regex_wildcard(co)) for co in glm_config.config["GLMSetupOptions"]['ConfoundsDerive']]
                    target_cols = []
                    for reg in cons_re:
                        target_cols.extend(
                            [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                    logger.debug("Lagged Columns " + str(target_cols))
                    confounds_lagged_mat = confounds[target_cols]
                    confounds_lagged_mat.rename(columns =lambda x: x+"_lagged", inplace = True)
                    confounds_lagged_mat = confounds_lagged_mat.diff()
                    confounds_mat = pandas.concat([confounds_mat,confounds_lagged_mat],axis=1, ignore_index=True)
                    logger.debug(str(confounds_mat.shape))
                    logger.debug(str(confounds_mat.head(5)))
                if len(glm_config.config["GLMSetupOptions"]['ConfoundsQuadDerive']) > 0:
                    cons_re = [re.compile(regex_wildcard(co)) for co in glm_config.config["GLMSetupOptions"]['ConfoundsQuadDerive']]
                    target_cols = []
                    for reg in cons_re:
                        target_cols.extend(
                            [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                    logger.debug("Quadlagged Columns " + str(target_cols))
                    confounds_qlagged_mat = confounds[target_cols]
                    confounds_qlagged_mat = confounds_qlagged_mat.diff()
                    confounds_qlagged_mat = confounds_qlagged_mat**2
                    confounds_qlagged_mat.rename(columns =lambda x: x+"_qlagged", inplace = True)
                    confounds_mat = pandas.concat([confounds_mat,confounds_qlagged_mat],axis=1,ignore_index=True)
                    logger.debug(str(confounds_mat.shape))
                if glm_config.config["GLMSetupOptions"]['MotionOutliers']:
                    logger.info("Computing Motion Outliers: ")
                    logger.info("Motion Outlier Variable: "+ glm_config.config["GLMSetupOptions"]['ScrubVar'])
                    logger.info("Threshold: " + str(glm_config.config["GLMSetupOptions"]['Threshold']))
                    logger.info("Ahead: " + str(glm_config.config["GLMSetupOptions"]['ScrubAhead']))
                    logger.info("Behind: " + str(glm_config.config["GLMSetupOptions"]['ScrubBehind']))
                    logger.info("Contiguous: " + str(glm_config.config["GLMSetupOptions"]['ScrubContiguous']))
                    fdts = confounds[glm_config.config["GLMSetupOptions"]['ScrubVar']]
                    logger.debug(str(fdts))
                    scrub_targets = scrub_setup(fdts, glm_config.config["GLMSetupOptions"]['Threshold'], glm_config.config["GLMSetupOptions"]['ScrubBehind'], glm_config.config["GLMSetupOptions"]['ScrubAhead'], glm_config.config["GLMSetupOptions"]['ScrubContiguous'])
                    logger.debug(str(scrub_targets))
            if drop_tps is not None:
                img_data = nib.load(image)
                total_tps = img_data.shape[3]
                tps_drop = None
                temp = None
                temp = drop_tps_data[drop_tps_data['file_name'].str.match(os.path.basename(image))]['TR_round']
                if len(temp) is 1:
                    tps_drop = int(temp)
                    logger.info('Found drop TP info, will remove last ' + str(tps_drop) + ' time points')
                if tps_drop is not None:
                    total_tps = total_tps - tps_drop
                    if confounds is not None:
                        confounds_mat = confounds_mat.head(total_tps)
                        fdts = fdts.iloc[:(fdts.shape[0]-(tps_drop))]
                    scrub_targets = scrub_setup(fdts,
                                                glm_config.config["GLMSetupOptions"]['Threshold'],
                                                glm_config.config["GLMSetupOptions"]['ScrubBehind'],
                                                glm_config.config["GLMSetupOptions"]['ScrubAhead'],
                                                glm_config.config["GLMSetupOptions"]['ScrubContiguous'])
                logger.info("Total timepoints are " + str(total_tps))
                glm_setup.inputs.drop_tps.t_size = total_tps
            glm_setup.inputs.input.in_file = os.path.abspath(image)
            glm_setup.inputs.input.out_file = _build_output_directory_structure(glm_config, image, logger)
            if confounds is not None:
                if glm_config.config["GLMSetupOptions"]['MotionOutliers']:
                    mot_outliers = _construct_motion_outliers(scrub_targets)
                    confounds_mat = pandas.concat([confounds_mat,mot_outliers],axis=1, ignore_index=True)
                    logger.debug(str(confounds_mat.shape))
                if glm_config.config["GLMSetupOptions"]["DummyScans"] is not 0:
                    confounds_mat = confounds_mat.iloc[glm_config.config["GLMSetupOptions"]["DummyScans"]:]
                confounds_out = glm_setup.inputs.input.out_file.replace(glm_config.config["GLMSetupOptions"]["OutputSuffix"],"confounds.tsv")
                logger.debug(str(confounds_mat.columns))
                confounds_mat.fillna(0, inplace = True)
                confounds_mat.to_csv(confounds_out,sep='\t',index=False,header=False)
                logger.info("Outputting confound file to: " + confounds_out)
            if glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
                glm_setup.inputs.input.mask_file = _mask_finder_glm(image, glm_config, logger)
            logger.debug(glm_setup.inputs)
            glm_setup.run()
        except Exception as err:
            logger.exception(err)

def _build_output_directory_structure(config, filepath, logger):

    target_directory = filepath[filepath.find('sub-'):]
    target_directory = os.path.dirname(target_directory)
    target_directory = os.path.join(config.config["GLMSetupOptions"]['OutputDirectory'], target_directory)
    logger.debug(target_directory)
    os.makedirs(target_directory, exist_ok=True)
    file_name = os.path.basename(filepath)
    file_name = file_name.replace(config.config["GLMSetupOptions"]['TargetSuffix'],config.config["GLMSetupOptions"]['OutputSuffix'])
    logger.debug(file_name)
    return os.path.abspath(os.path.join(target_directory, file_name))

def _mask_finder_glm(image, glm_config, logger):

    image_base = os.path.basename(image)
    image_base = image_base.replace(glm_config.config['GLMSetupOptions']['TargetSuffix'],glm_config.config['GLMSetupOptions']['MaskSuffix'])
    logger.debug(image_base)
    target_mask = glob.glob(os.path.join(glm_config.config['GLMSetupOptions']['MaskFolderRoot'],"**" ,image_base), recursive=True)
    logger.debug(target_mask)
    if len(target_mask) == 0:
        logger.info("Mask not found for "+os.path.basename(image))
        return(None)
    else:
        return(os.path.abspath(target_mask[0]))

def _find_confounds(glm_config, filepath):
    file_name = os.path.basename(filepath)
    file_name = file_name.replace(glm_config.config['GLMSetupOptions']['TargetSuffix'],glm_config.config['GLMSetupOptions']['ConfoundSuffix'])
    return os.path.join(os.path.dirname(filepath), file_name)

def regex_wildcard(string):
    return '^'+re.sub("\*", ".*", string)+'$'

def _construct_motion_outliers(scrub_targets):
    size = sum(scrub_targets)
    mot_outliers = pandas.DataFrame(np.zeros((len(scrub_targets),size)))
    counter = 0
    for ind, i  in enumerate(scrub_targets):
        if i == 1:
            mot_outliers.iloc[ind, counter] = 1
            counter += 1
    return mot_outliers
