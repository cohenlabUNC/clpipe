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
from pkg_resources import resource_stream
import clpipe.postprocutils
import numpy
import logging
import gc
import psutil
logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None)
@click.option('-task')
@click.option('-TR')
@click.option('-targetDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-targetSuffix')
@click.option('-outputDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-outputSuffix')
@click.option('-logOutputDir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-submit/-save', default=False)
@click.option('-batch/-single', default=True)
def fmri_postprocess(configfile=None, subjects=None, targetdir=None, targetsuffix=None, outputdir=None,
                     outputsuffix=None, logoutputdir=None,
                     submit=False, batch=True, task=None, tr=None):
    logging.basicConfig(level=logging.DEBUG)
    if configfile is None and tr is None:
        raise ValueError('No config file and no specified TR. Please include one.')

    config = ConfigParser()
    config.config_updater(configfile)
    config.setup_postproc(targetdir, targetsuffix, outputdir, outputsuffix)
    config.validate_config()

    if logoutputdir is not None:
        if os.path.isdir(logoutputdir):
            logoutputdir = os.path.abspath(logoutputdir)
        else:
            logoutputdir = os.path.abspath(logoutputdir)
            os.makedirs(logoutputdir, exist_ok=True)
    else:
        logoutputdir = os.path.join(config.config['PostProcessingOptions']['OutputDirectory'], "BatchOutput")
        os.makedirs(logoutputdir, exist_ok=True)

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(targetdir)
                   if os.path.isdir(os.path.join(targetdir, o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    submission_string = '''fmri_postprocess -configFile={config} -targetDir={targetDir} -targetSuffix={targetSuffix} ''' \
                        '''-outputDir={outputDir} -outputSuffix={outputSuffix} -logOutputDir={logOutputDir} -single {sub}'''

    if batch:
        batch_manager = BatchManager(config.config['BatchConfig'], logoutputdir)
        batch_manager.update_mem_usage(config.config['PostProcessingOptions']['PostProcessingMemoryUsage'])
        for sub in sublist:
            sub_string_temp = submission_string.format(
                config=os.path.abspath(configfile),
                targetDir=config.config['PostProcessingOptions']['TargetDirectory'],
                targetSuffix=config.config['PostProcessingOptions']['TargetSuffix'],
                outputDir=config.config['PostProcessingOptions']['OutputDirectory'],
                outputSuffix=config.config['PostProcessingOptions']['OutputSuffix'],
                logOutputDir=logoutputdir,
                sub=sub
            )
            batch_manager.addjob(Job("PostProcessing" + sub, sub_string_temp))
        if submit:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
            config.update_runlog(subjectstring, "PostProcessing")
            config.config_json_dump(config.config['PostProcessingOptions']['OutputDirectory'], configfile)
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
        logging.debug()
        data = clpipe.postprocutils.spec_interpolate.spec_inter(data, tr, ofreq, scrubTargets, hfreq, binSize=config.config['PostProcessingOptions']["SpectralInterpolationBinSize"])
        gc.collect()
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
    reg_labels = json.load(resource_stream(__name__, 'data/RegressionOptions.json'))
    target_label = next((item for item in reg_labels['RegressionOptions'] if
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
