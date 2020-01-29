import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import logging
import sys
from .error_handler import exception_handler
import nipype.interfaces.io as nio  # Data i/o
import nipype.interfaces.fsl as fsl  # fsl
import nipype.interfaces.utility as util  # utility
import nipype.pipeline.engine as pe  # pypeline engine
from nipype.interfaces.utility import IdentityInterface

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')

@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def glm_setup(subjects = None, config_file=None, glm_config_file = None,
                     submit=False, batch=True, task=None, debug = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    glm_config = GLMConfigParser(glm_config_file)

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['GLMSetupOptions']['TargetDirectory'])
                   if os.path.isdir(os.path.join(config.config['GLMSetupOptions']['TargetDirectory'], o)) and 'sub-' in o]
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
            _glm_prep(glm_config, sub, task)


def _glm_prep(glm_config, subject, task):
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


    search_string = os.path.abspath(
        os.path.join(glm_config.config["GLMSetupOptions"]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + glm_config.config["GLMSetupOptions"]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)

    glm_setup = pe.Workflow(name='glm_setup')
    glm_setup.base_dir = os.path.join(glm_config.config["GLMSetupOptions"]['WorkingDirectory'], "sub-"+subject)
    input_node = pe.Node(IdentityInterface(fields=['in_file', 'out_file', 'mask_file']), name='input')
    sus = pe.Node(fsl.SUSAN(), name="susan_smoothing")
    strip = pe.Node(fsl.ApplyMask(), name="mask_apply")
    resample = pe.Node(fsl.FLIRT(apply_isoxfm = glm_config.config["GLMSetupOptions"]["ResampleResolution"],
                                    reference = glm_config.config["GLMSetupOptions"]["ReferenceImage"]),
                       name="resample")

    glm_setup.connect(input_node, 'out_file', resample, 'out_file')
    if glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
        strip = pe.Node(fsl.ApplyMask(), name="mask_apply")
        glm_setup.connect([(input_node, strip, [('in_file', 'in_file'),
                                         ('mask_file', 'mask_file')])])

    if glm_config.config["GLMSetupOptions"]["SUSANSmoothing"]:
        sus = pe.Node(fsl.SUSAN(), name="susan_smoothing")
        sus.inputs.brightness_threshold = glm_config.config["GLMSetupOptions"]['SUSANOptions']['BrightnessThreshold']
        sus.inputs.fwhm = glm_config.config["GLMSetupOptions"]['SUSANOptions']['FWHM']

        if glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
            glm_setup.connect(strip, 'out_file', sus, 'in_file')
        else:
            glm_setup.connect(input_node, 'in_file', sus, 'in_file')

    if glm_config.config["GLMSetupOptions"]["SUSANSmoothing"]:
        glm_setup.connect(sus, 'smoothed_file', resample, 'in_file')
    elif glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
        glm_setup.connect(strip, 'out_file', resample, 'in_file')
    else:
        glm_setup.connect(input_node, 'in_file', resample, 'in_file')

    for image in subject_files:
        if task is None or 'task-' + task in image:
            logging.info('Processing ' + image)
            try:
                glm_setup.inputs.input.in_file = image

                glm_setup.inputs.input.out_file = _build_output_directory_structure(glm_config, image)
                if glm_config.config["GLMSetupOptions"]["ApplyFMRIPREPMask"]:
                    glm_config.inputs.input.mask_file = _mask_finder_glm(image, glm_config)
                logging.info(glm_config.inputs)

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
    return os.path.join(target_directory, file_name)

def _mask_finder_glm(image, glm_config):

    image_base = os.path.basename(image)
    image_base.replace(glm_config.config['GLMSetupOptions']['TargetSuffix'],glm_config.config['GLMSetupOptions']['MaskSuffix'])
    target_mask = glob.glob(os.path.join(glm_config.config['GLMSetupOptions']['TargetSuffix'],"**" ,image_base), recursive=True)

    if len(target_mask == 0):
        logging.info("Mask not found for "+os.path.basename(image))
        return(None)
    else:
        return(target_mask)
