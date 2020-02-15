import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import logging
import sys
from .error_handler import exception_handler
import nipype.interfaces.fsl as fsl  # fsl
import nipype.pipeline.engine as pe  # pypeline engine
from nipype.interfaces.utility import IdentityInterface
import nibabel as nib
import pandas
import re
import clpipe.postprocutils
import numpy as np

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-drop_tps', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = False,
              help='Drop timepoints csv sheet')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def glm_setup(subjects = None, config_file=None, glm_config_file = None,
                     submit=False, batch=True, debug = None, drop_tps = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    glm_config = GLMConfigParser(glm_config_file)
    task = glm_config.config['GLMSetupOptions']['TaskName']
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
            click.echo(batch_manager.print_jobs())
    else:
        for sub in subjects:

            logging.info('Running Subject ' + sub)
            _glm_prep(glm_config, sub, task, drop_tps)


def _glm_prep(glm_config, subject, task, drop_tps):
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


    search_string = os.path.abspath(
        os.path.join(glm_config.config["GLMSetupOptions"]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + glm_config.config["GLMSetupOptions"]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)

    glm_setup = pe.Workflow(name='glm_setup')
    glm_setup.base_dir = os.path.join(glm_config.config["GLMSetupOptions"]['WorkingDirectory'], "sub-"+subject)
    input_node = pe.Node(IdentityInterface(fields=['in_file', 'out_file', 'mask_file']), name='input')
    strip = pe.Node(fsl.BinaryMaths(operation = 'mul'), name="mask_apply")
    resample = pe.Node(fsl.FLIRT(apply_isoxfm = glm_config.config["GLMSetupOptions"]["ResampleResolution"],
                                    reference = glm_config.config["GLMSetupOptions"]["ReferenceImage"]),
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

    for image in subject_files:
        if task is None or 'task-' + task + '_' in image:
            logging.info('Processing ' + image)
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
                            logging.debug(str([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None]))
                            target_cols.extend([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                        logging.debug("Confound Columns " + str(target_cols))
                        confounds_mat = confounds[target_cols]
                    if len(glm_config.config["GLMSetupOptions"]['ConfoundsQuad']) > 0:
                        cons_re = [re.compile(regex_wildcard(co)) for co in glm_config.config["GLMSetupOptions"]['ConfoundsQuad']]
                        target_cols = []
                        for reg in cons_re:
                            target_cols.extend(
                                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                        logging.debug("Quad Columns " + str(target_cols))
                        confounds_quad_mat = confounds[target_cols]
                        confounds_quad_mat = confounds_quad_mat**2
                        pandas.concat([confounds_mat.reset_index(),confounds_quad_mat.reset_index()],axis=1)
                    if len(glm_config.config["GLMSetupOptions"]['ConfoundsLagged']) > 0:
                        cons_re = [re.compile(regex_wildcard(co)) for co in glm_config.config["GLMSetupOptions"]['ConfoundsLagged']]
                        target_cols = []
                        for reg in cons_re:
                            target_cols.extend(
                                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                        logging.debug("Lagged Columns " + str(target_cols))
                        confounds_lagged_mat = confounds[target_cols]
                        confounds_lagged_mat = confounds_lagged_mat.diff()
                        pandas.concat([confounds_mat.reset_index(),confounds_lagged_mat.reset_index()],axis=1)
                    if len(glm_config.config["GLMSetupOptions"]['ConfoundsQuadLagged']) > 0:
                        cons_re = [re.compile(regex_wildcard(co)) for co in glm_config.config["GLMSetupOptions"]['ConfoundsQuadLagged']]
                        target_cols = []
                        for reg in cons_re:
                            target_cols.extend(
                                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
                        logging.debug("Quadlagged Columns " + str(target_cols))
                        confounds_qlagged_mat = confounds[target_cols]
                        confounds_qlagged_mat = confounds_qlagged_mat.diff()
                        confounds_qlagged_mat = confounds_qlagged_mat**2
                        pandas.concat([confounds_mat.reset_index(),confounds_qlagged_mat.reset_index()],axis=1)
                    if glm_config.config["GLMSetupOptions"]['MotionOutliers']:
                        logging.info("Computing Motion Outliers: ")
                        logging.info("Motion Outlier Variable: "+ glm_config.config["GLMSetupOptions"]['ScrubVar'])
                        logging.info("Threshold: " + str(glm_config.config["GLMSetupOptions"]['Threshold']))
                        logging.info("Ahead: " + str(glm_config.config["GLMSetupOptions"]['ScrubAhead']))
                        logging.info("Behind: " + str(glm_config.config["GLMSetupOptions"]['ScrubBehind']))
                        logging.info("Contiguous: " + str(glm_config.config["GLMSetupOptions"]['ScrubContiguous']))
                        fdts = confounds[glm_config.config["GLMSetupOptions"]['Scrub_Var']]
                        scrub_targets = clpipe.postprocutils.utils.scrub_setup(fdts, glm_config.config["GLMSetupOptions"]['Threshold'], glm_config.config["GLMSetupOptions"]['ScrubBehind'], glm_config.config["GLMSetupOptions"]['ScrubAhead'], glm_config.config["GLMSetupOptions"]['ScrubContiguous'])
                if drop_tps is not None:
                    img_data = nib.load(image)
                    total_tps = img_data.shape[3]
                    tps_drop = None
                    temp = None
                    temp = drop_tps_data[drop_tps_data['file_name'].str.match(os.path.basename(image))]['TR_round']
                    if len(temp) is 1:
                        tps_drop = int(temp)
                        logging.info('Found drop TP info, will remove last ' + str(tps_drop) + ' time points')
                    if tps_drop is not None:
                        total_tps = total_tps - tps_drop
                        if confounds is not None:
                            confounds_mat = confounds_mat.head(total_tps)
                            fdts = fdts.iloc[:(fdts.shape[0]-(tps_drop))]
                        scrub_targets = clpipe.postprocutils.utils.scrub_setup(fdts, glm_config.config["GLMSetupOptions"]['Threshold'],
                                                                               glm_config.config["GLMSetupOptions"]['ScrubBehind'],
                                                                               glm_config.config["GLMSetupOptions"]['ScrubAhead'],
                                                                               glm_config.config["GLMSetupOptions"]['ScrubContiguous'])
                    logging.info("Total timepoints are " + str(total_tps))
                    glm_setup.inputs.drop_tps.t_size = total_tps
                glm_setup.inputs.input.in_file = os.path.abspath(image)
                glm_setup.inputs.input.out_file = _build_output_directory_structure(glm_config, image)
                if confounds is not None:
                    if glm_config.config["GLMSetupOptions"]['MotionOutliers']:
                        mot_outliers = _construct_motion_outliers(scrub_targets)
                        pandas.concat([confounds_mat.reset_index(),confounds_lagged_mat.reset_index()],axis=1)
                        pandas.concat([confounds_mat.reset_index(),mot_outliers.reset_index()],axis=1)
                    confounds_out = os.path.splitext(glm_setup.inputs.input.out_file) + "_confounds.tsv"
                    confounds_mat.to_csv(confounds_out,sep='\t',index=False,header=False)
                    logging.info("Outputting confound file to: " + confounds_out)
                if glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
                    glm_setup.inputs.input.mask_file = _mask_finder_glm(image, glm_config)
                logging.info(glm_setup.inputs)
                glm_setup.run()
            except Exception as err:
                logging.exception(err)

def _build_output_directory_structure(config, filepath):

    target_directory = filepath[filepath.find('sub-'):]
    target_directory = os.path.dirname(target_directory)
    target_directory = os.path.join(config.config["GLMSetupOptions"]['PreppedDataDirectory'], target_directory)
    logging.debug(target_directory)
    os.makedirs(target_directory, exist_ok=True)
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    logging.debug(config.config["GLMSetupOptions"]['PreppedSuffix'])
    file_name = sans_ext + '_' + config.config["GLMSetupOptions"]['PreppedSuffix']
    logging.debug(file_name)
    return os.path.abspath(os.path.join(target_directory, file_name))

def _mask_finder_glm(image, glm_config):

    image_base = os.path.basename(image)
    image_base = image_base.replace(glm_config.config['GLMSetupOptions']['TargetSuffix'],glm_config.config['GLMSetupOptions']['MaskSuffix'])
    logging.debug(image_base)
    target_mask = glob.glob(os.path.join(glm_config.config['GLMSetupOptions']['MaskFolderRoot'],"**" ,image_base), recursive=True)
    logging.debug(target_mask)
    if len(target_mask) == 0:
        logging.info("Mask not found for "+os.path.basename(image))
        return(None)
    else:
        return(os.path.abspath(target_mask[0]))

def _find_confounds(glm_config, filepath):
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    root_file = sans_ext[:sans_ext.index('space')]
    return os.path.join(os.path.dirname(filepath), root_file + glm_config.config["GLMSetupOptions"]['ConfoundSuffix'])

def regex_wildcard(string):
    return '^'+re.sub("\*", ".*", string)+'$'

def _construct_motion_outliers(scrub_targets):
    size = sum(scrub_targets)
    mot_outliers = pandas.DataFrame(np.zeros((len(scrub_targets),size)))
    counter = 0
    for i  in scrub_targets:
        if i == 1:
            mot_outliers.iloc[i, counter] = 1
            counter += 1
    return mot_outliers