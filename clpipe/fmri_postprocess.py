import os
import glob
import click
import pandas
from nipy import load_image
from nipy.core.image.image import Image
from nipy import save_image
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
import json
from pkg_resources import resource_stream, resource_filename
import clpipe.postprocutils
import numpy
import logging
import gc
import psutil
import sys
from .error_handler import exception_handler

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help='Which fmriprep directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary. Note, must point to the ``fmriprep`` directory, not its parent directory.')
@click.option('-target_suffix', help= 'Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to "preproc_bold.nii.gz"')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to put the postprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-output_suffix', help = 'What suffix to append to the postprocessed files. If a configuration file is provided with a output suffix, this argument is not necessary.')
@click.option('-task', help = 'Which task to postprocess. If left blank, defaults to all tasks.')
@click.option('-TR', help = 'The TR of the scans. If a config file is not provided, this option is required. If a config file is provided, this information is found from the sidecar jsons.')
@click.option('-log_output_dir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True, help = 'Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess(config_file=None, subjects=None, target_dir=None, target_suffix=None, output_dir=None,
                     output_suffix=None, log_output_dir=None,
                     submit=False, batch=True, task=None, tr=None, debug = False):
    """This command runs an fMRIprep'ed dataset through additional processing, as defined in the configuration file. To run specific subjects, specify their IDs. If no IDs are specified, all subjects are ran."""
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if config_file is None and tr is None:
        raise ValueError('No config file and no specified TR. Please include one.')

    config = ConfigParser()
    config.config_updater(config_file)
    config.setup_postproc(target_dir, target_suffix, output_dir, output_suffix)
    config.validate_config()

    if config_file is None:
        config_file = resource_filename(__name__, "data/defaultConfig.json")

    if log_output_dir is not None:
        if os.path.isdir(log_output_dir):
            log_output_dir = os.path.abspath(log_output_dir)
        else:
            log_output_dir = os.path.abspath(log_output_dir)
            os.makedirs(log_output_dir, exist_ok=True)
    else:
        log_output_dir = os.path.join(config.config['PostProcessingOptions']['OutputDirectory'], "BatchOutput")
        os.makedirs(log_output_dir, exist_ok=True)

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['PostProcessingOptions']['TargetDirectory'])
                   if os.path.isdir(os.path.join(config.config['PostProcessingOptions']['TargetDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    submission_string = '''fmri_postprocess -config_file={config} -target_dir={targetDir} -target_suffix={targetSuffix} ''' \
                        '''-output_dir={outputDir} -output_suffix={outputSuffix} -log_output_dir={logOutputDir} {taskString} {trString} -single {sub}'''
    task_string = ""
    tr_string = ""
    if task is not None:
        task_string = '-task='+task
    if tr is not None:
        tr_string = '-tr='+tr

    if batch:
        config_string = config.config_json_dump(config.config['PostProcessingOptions']['OutputDirectory'], config_file)
        batch_manager = BatchManager(config.config['BatchConfig'], log_output_dir)
        batch_manager.update_mem_usage(config.config['PostProcessingOptions']['PostProcessingMemoryUsage'])
        batch_manager.update_time(config.config['PostProcessingOptions']['PostProcessingTimeUsage'])
        batch_manager.update_nthreads(config.config['PostProcessingOptions']['NThreads'])
        for sub in sublist:
            sub_string_temp = submission_string.format(
                config=config_string,
                targetDir=config.config['PostProcessingOptions']['TargetDirectory'],
                targetSuffix=config.config['PostProcessingOptions']['TargetSuffix'],
                outputDir=config.config['PostProcessingOptions']['OutputDirectory'],
                outputSuffix=config.config['PostProcessingOptions']['OutputSuffix'],
                task = task_string,
                tr = tr_string,
                logOutputDir=log_output_dir,
                sub=sub
            )
            batch_manager.addjob(Job("PostProcessing" + sub, sub_string_temp))
        if submit:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
            config.update_runlog(subjectstring, "PostProcessing")
            config.config_json_dump(config.config['PostProcessingOptions']['OutputDirectory'], config_file)
        else:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())
    else:
        for sub in subjects:
            logging.info('Running Subject ' + sub)
            _fmri_postprocess_subject(config, sub, task)


def _fmri_postprocess_subject(config, subject, task, tr=None):
    search_string = os.path.abspath(
        os.path.join(config.config['PostProcessingOptions']['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config['PostProcessingOptions']['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)
    logging.info('Finding Image Files')
    for image in subject_files:
        if task is None or 'task-' + task in image:
            logging.info('Processing ' + image)
            _fmri_postprocess_image(config, image, tr)


def _fmri_postprocess_image(config, file, tr=None):
    confound_regressors = _find_confounds(config, file)

    logging.info('Looking for: ' + confound_regressors)

    if not os.path.exists(confound_regressors):
        logging.warning('Could not find a confound file for ' + file + ". Moving onto next scan")
        return
    else:
        logging.info('Found confound regressors')
        confounds, fdts = _regression_prep(config, confound_regressors)
        if tr is None:
            image_json_path = _find_json(config, file)
            with open(os.path.abspath(image_json_path), "r") as json_path:
                image_json = json.load(json_path)
            tr = float(image_json['RepetitionTime'])
        logging.info('TR found: ' + str(tr))
        image = load_image(file)
        data = image.get_data()
        orgImageShape = data.shape
        coordMap = image.coordmap
        data = data.reshape((numpy.prod(numpy.shape(data)[:-1]), data.shape[-1]))
        data = numpy.transpose(data)
        row_means = data.mean(axis=0)
        data = (data - data.mean(axis=0))

    regress_toggle = config.config['PostProcessingOptions']['Regress']

    scrub_toggle = False
    if config.config['PostProcessingOptions']['Scrubbing']:
        logging.debug('Scrubbing Toggle Activated')
        scrub_toggle = True
        scrub_ahead = int(config.config['PostProcessingOptions']['ScrubAhead'])
        scrub_behind = int(config.config['PostProcessingOptions']['ScrubBehind'])
        scrub_contig = int(config.config['PostProcessingOptions']['ScrubContig'])
        fd_thres = float(config.config['PostProcessingOptions']['ScrubFDThreshold'])
        scrubTargets = clpipe.postprocutils.utils.scrub_setup(fdts, fd_thres, scrub_behind, scrub_ahead, scrub_contig)

    hp = float(config.config['PostProcessingOptions']['FilteringHighPass'])
    lp = float(config.config['PostProcessingOptions']['FilteringLowPass'])
    filter_toggle = False
    if hp > 0 or lp > 0:
        logging.info('Filtering Toggle Activated')
        filter_toggle = True
        order = int(config.config['PostProcessingOptions']['FilteringOrder'])
        filt = clpipe.postprocutils.utils.calc_filter(hp, lp, tr, order)
        confounds = clpipe.postprocutils.utils.apply_filter(filt, confounds)

    if scrub_toggle and filter_toggle:
        logging.info('Using Spectral Interpolation')
        ofreq = int(config.config['PostProcessingOptions']['OversamplingFreq'])
        hfreq = float(config.config['PostProcessingOptions']['PercentFreqSample'])
        logging.debug('Memory Usage Before Spectral Interpolation:' +str(psutil.virtual_memory().total >> 30) +' GB')
        data = clpipe.postprocutils.spec_interpolate.spec_inter(data, tr, ofreq, scrubTargets, hfreq, binSize=config.config['PostProcessingOptions']["SpectralInterpolationBinSize"])

        gc.collect()
        logging.debug('Memory Usage After Spectral Interpolation GC:' +str(psutil.virtual_memory().total >> 30) +' GB')
    if filter_toggle:
        logging.info('Filtering Data Now')
        data = clpipe.postprocutils.utils.apply_filter(filt, data)

    if regress_toggle:
        logging.info('Regressing Data Now')
        data = clpipe.postprocutils.utils.regress(confounds, data)

    if scrub_toggle:
        logging.info('Scrubbing data now')
        data = clpipe.postprocutils.utils.scrub_image(data, scrubTargets)

    data = (data + row_means)

    data = numpy.transpose(data)
    data = data.reshape(orgImageShape)
    out_image = Image(data, coordMap)

    output_file_path = _build_output_directory_structure(config, file)
    logging.info('Saving post processed data to ' + output_file_path)
    save_image(out_image, output_file_path)

    if scrub_toggle:
        file_name = os.path.basename(file)
        sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
        toOut = numpy.vstack([numpy.arange(1, len(scrubTargets) + 1, 1), numpy.asarray(scrubTargets)]).T
        logging.info('Saving Scrub Targets to ' + os.path.join(os.path.dirname(output_file_path),
                                                               sans_ext + "_scrubTargets.csv"))
        numpy.savetxt(os.path.join(os.path.dirname(output_file_path), sans_ext + "_scrubTargets.csv"), toOut,
                      delimiter=",")


def _regression_prep(config, confound_filepath):
    confounds = pandas.read_table(confound_filepath, dtype="float", na_values="n/a")
    confounds = confounds.fillna(0)
    reg_labels = config.config['PostProcessingOptions']['RegressionParameters']
    regression_type = json.load(resource_stream(__name__, 'data/RegressionOptions.json'))
    target_label = next((item for item in regression_type['RegressionOptions'] if
                         item["Name"] == config.config['PostProcessingOptions']['NuisanceRegression']), False)
    if not target_label:
        raise ValueError
    fd = confounds[reg_labels['FDLabel']]
    confound_labels = []
    confound_labels.extend(reg_labels["MotionParams"])

    if config.config['PostProcessingOptions']['WhiteMatter']:
        confound_labels.extend([reg_labels["WhiteMatter"]])
    if config.config['PostProcessingOptions']['CSF']:
        confound_labels.extend([reg_labels["CSF"]])
    if config.config['PostProcessingOptions']['GlobalSignalRegression']:
        confound_labels.extend([reg_labels["GlobalSignal"]])

    confounds = confounds[confound_labels]

    if target_label['Lagged']:
        confound_temp = confounds.diff()
        confound_temp = confound_temp.fillna(0)
        confounds = pandas.concat([confounds, confound_temp], axis=1, ignore_index=True)

    if target_label['Quadratic']:
        confound_temp = confounds.pow(2)
        confound_temp = confound_temp.fillna(0)
        confounds = pandas.concat([confounds, confound_temp], axis=1, ignore_index=True)

    return confounds, fd


# Rewrite find json function, use task information to be very specific.
def _find_json(config, filepath):
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    components = sans_ext.split('_')

    jsons = glob.glob(os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], '**', '*.json'), recursive=True)

    count_overlap = []
    for json_target in jsons:
        count_overlap.append(sum([json_target.count(x) for x in components]))

    max_value = max(count_overlap)
    target_json = jsons[count_overlap.index(max_value)]
    logging.debug(target_json)
    return target_json


def _find_confounds(config, filepath):
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    root_file = sans_ext[:sans_ext.index('space')]
    return os.path.join(os.path.dirname(filepath), root_file + config.config['PostProcessingOptions']['ConfoundSuffix'])


def _build_output_directory_structure(config, filepath):

    target_directory = filepath[filepath.find('sub-'):]
    target_directory = os.path.dirname(target_directory)
    target_directory = os.path.join(config.config['PostProcessingOptions']['OutputDirectory'], target_directory)
    os.makedirs(target_directory, exist_ok=True)
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]

    file_name = sans_ext + '_' + config.config['PostProcessingOptions']['OutputSuffix']
    logging.debug(file_name)
    return os.path.join(target_directory, file_name)
