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
import nipy.modalities.fmri.hrf
from scipy import signal

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help='Which fmriprep directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary. Note, must point to the ``fmriprep`` directory, not its parent directory.')
@click.option('-target_suffix', help= 'Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to "preproc_bold.nii.gz"')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to put the postprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-output_suffix', help = 'What suffix to append to the postprocessed files. If a configuration file is provided with a output suffix, this argument is not necessary.')
@click.option('-task', help = 'Which task to postprocess. If left blank, defaults to all tasks.')
@click.option('-TR', help = 'The TR of the scans. If a config file is not provided, this option is required. If a config file is provided, this information is found from the sidecar jsons.')
@click.option('-processing_stream', help = 'Optional processing stream selector.')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-beta_series', is_flag = True, default = False, help = "Flag to activate beta-series correlation correlation. ADVANCED METHOD, refer to the documentation.")
@click.option('-drop_tps', type=click.Path(dir_okay=True, file_okay=True))
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True, help = 'Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess(config_file=None, subjects=None, target_dir=None, target_suffix=None, output_dir=None,
                     output_suffix=None, log_dir=None,
                     submit=False, batch=True, task=None, tr=None, processing_stream = None, debug = False, beta_series = False,                       drop_tps = None):
    """This command runs an fMRIprep'ed dataset through additional processing, as defined in the configuration file. To run specific subjects, specify their IDs. If no IDs are specified, all subjects are ran."""
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    if config_file is None and tr is None:
        raise ValueError('No config file and no specified TR. Please include one.')

    config = ConfigParser()
    config.config_updater(config_file)
    config.setup_postproc(target_dir, target_suffix, output_dir, output_suffix, beta_series,
                          log_dir)
    config.validate_config()
    if beta_series:
          output_type = 'BetaSeriesOptions'
    else:
          output_type = 'PostProcessingOptions'
    if config_file is None:
        config_file = resource_filename(__name__, "data/defaultConfig.json")

    alt_proc_toggle = False
    if processing_stream is not None:

        processing_stream_config = config.config['ProcessingStreams']
        processing_stream_config = [i for i in processing_stream_config if i['ProcessingStream'] == processing_stream]
        if len(processing_stream_config) == 0:
            raise KeyError('The processing stream you specified was not found.')
        alt_proc_toggle = True

    if alt_proc_toggle:
        if beta_series:
            config.update_processing_stream(processing_stream, processing_stream_config[0]['BetaSeriesOptions']['OutputDirectory'],
                                           processing_stream_config[0]['BetaSeriesOptions']['OutputSuffix'],
                                           processing_stream_config[0]['BetaSeriesOptions']['LogDirectory'])
            config.config['BetaSeriesOptions'].update(processing_stream_config[0]['BetaSeriesOptions'])
        else:
            config.config['PostProcessingOptions'].update(processing_stream_config[0]['PostProcessingOptions'])
            config.update_processing_stream(processing_stream, processing_stream_config[0]['PostProcessingOptions']['OutputDirectory'],
                                           processing_stream_config[0]['PostProcessingOptions']['OutputSuffix'],
                                           processing_stream_config[0]['PostProcessingOptions']['LogDirectory'])




    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config[output_type]['TargetDirectory'])
                   if os.path.isdir(os.path.join(config.config[output_type]['TargetDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    submission_string = '''fmri_postprocess -config_file={config} -target_dir={targetDir} -target_suffix={targetSuffix} ''' \
                        '''-output_dir={outputDir} -output_suffix={outputSuffix} {procstream} -log_dir={logOutputDir} {drop_tps} {taskString} {trString} {beta_series} -single {sub}'''
    drop_tps_string = ""
    task_string = ""
    tr_string = ""
    beta_series_string = ""
    if drop_tps is not None:
        drop_tps_string  = '-drop_tps ' + drop_tps
    if task is not None:
        task_string = '-task='+task
    if tr is not None:
        tr_string = '-tr='+tr
    if beta_series:
        beta_series_string = '-beta_series'
    if processing_stream is not None:
        procstream = "-processing_stream=" + processing_stream
    else:
        procstream = ""
    if batch:
        config_string = config.config_json_dump(config.config[output_type]['OutputDirectory'], os.path.basename(config_file))
        batch_manager = BatchManager(config.config['BatchConfig'], config.config[output_type]['LogDirectory'])
        batch_manager.update_mem_usage(config.config['PostProcessingOptions']['PostProcessingMemoryUsage'])
        batch_manager.update_time(config.config['PostProcessingOptions']['PostProcessingTimeUsage'])
        batch_manager.update_nthreads(config.config['PostProcessingOptions']['NThreads'])
        batch_manager.update_email(config.config["EmailAddress"])
        for sub in sublist:
            sub_string_temp = submission_string.format(
                config=config_string,
                targetDir=config.config[output_type]['TargetDirectory'],
                targetSuffix=config.config[output_type]['TargetSuffix'],
                outputDir=config.config[output_type]['OutputDirectory'],
                outputSuffix=config.config[output_type]['OutputSuffix'],
                procstream = procstream,
                taskString = task_string,
                trString = tr_string,
                logOutputDir=config.config[output_type]['LogDirectory'],
                beta_series = beta_series_string,
                drop_tps = drop_tps_string,
                sub=sub
            )
            if debug:
              sub_string_temp = sub_string_temp + " -debug"

            batch_manager.addjob(Job("PostProcessing" + sub, sub_string_temp))
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
            logging.debug(beta_series)
            logging.info('Running Subject ' + sub)
            _fmri_postprocess_subject(config, sub, task, tr, beta_series, drop_tps)


def _fmri_postprocess_subject(config, subject, task, tr=None, beta_series = False, drop_tps = None):
    if beta_series:
          output_type = 'BetaSeriesOptions'
    else:
          output_type = 'PostProcessingOptions'
    search_string = os.path.abspath(
        os.path.join(config.config[output_type]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config[output_type]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)

    drop_tps = pandas.read_csv(drop_tps)

    logging.info('Finding Image Files')
    for image in subject_files:
        if task is None or 'task-' + task in image:
            logging.info('Processing ' + image)
            try:
                temp = drop_tps[drop_tps['file_name'].str.match(os.path.basename(image))]['TR_round']
                if len(temp) is not 0:
                        tps_drop = int(temp)
                        logging.info('Found drop TP info, will remove last ' + str(tps_drop) + ' time points')
                else:
                        tps_drop = None
                _fmri_postprocess_image(config, image, task,  tr, beta_series, tps_drop)
            except Exception as err:
                logging.exception(err)


def _fmri_postprocess_image(config, file, task = None, tr=None, beta_series = False, drop_tps = None):
    confound_regressors = _find_confounds(config, file)
    output_file_path = _build_output_directory_structure(config, file, beta_series)

    if os.path.exists(output_file_path):
      logging.info("Output File Exists! Skipping.")
      return 0

    logging.info('Looking for: ' + confound_regressors)

    if not os.path.exists(confound_regressors):
        logging.warning('Could not find a confound file for ' + file + ". Moving onto next scan")
        return
    else:
        logging.info('Found confound regressors')
        confounds, fdts = _regression_prep(config, confound_regressors)
        if drop_tps is not None:
            confounds = confounds.iloc[:(confounds.shape[0]-drop_tps)]
            fdts = fdts.iloc[:(fdts.shape[0]-drop_tps)]
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
        if drop_tps is not None:
            data = data[0:(data.shape[0]-drop_tps), :]
            orgImageShape = list(orgImageShape)
            orgImageShape[3] = data.shape[0]
            orgImageShape = tuple(orgImageShape)
        row_means = data.mean(axis=0)
        data = (data - data.mean(axis=0))
    if not beta_series:
        regress_toggle = config.config['PostProcessingOptions']['Regress']

        scrub_toggle = False
        if config.config['PostProcessingOptions']['Scrubbing']:
            logging.debug('Scrubbing Toggle Activated')
            scrub_toggle = True
            scrub_ahead = int(config.config['PostProcessingOptions']['ScrubAhead'])
            scrub_behind = int(config.config['PostProcessingOptions']['ScrubBehind'])
            scrub_contig = int(config.config['PostProcessingOptions']['ScrubContig'])
            fd_thres = float(config.config['PostProcessingOptions']['ScrubFDThreshold'])
            orig_fdts = fdts
            if config.config['PostProcessingOptions']['RespNotchFilter']:
                fdts = _notch_filter_fd(config,  confound_regressors, tr, drop_tps)

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
            logging.info('Scrubbing data Now')
            data = clpipe.postprocutils.utils.scrub_image(data, scrubTargets)

        data = (data + row_means)

        data = numpy.transpose(data)
        data = data.reshape(orgImageShape)
        data32 = numpy.float32(data)
        out_image = Image(data32, coordMap)

        output_file_path = _build_output_directory_structure(config, file)
        logging.info('Saving post processed data to ' + output_file_path)
        save_image(out_image, output_file_path)

        if scrub_toggle:
            file_name = os.path.basename(file)
            sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
            toOut = numpy.column_stack([numpy.arange(1, len(scrubTargets) + 1, 1), numpy.asarray(scrubTargets), fdts, orig_fdts])
            logging.info('Saving Scrub Targets to ' + os.path.join(os.path.dirname(output_file_path),
                                                                   sans_ext + "_scrubTargets.csv"))
            numpy.savetxt(os.path.join(os.path.dirname(output_file_path), sans_ext + "_scrubTargets.csv"), toOut,
                          delimiter=",")
    else:
        beta_series_options = config.config['BetaSeriesOptions']['TaskSpecificOptions']

        avail_tasks = [x['Task'] for x in beta_series_options]
        logging.debug(avail_tasks)
        img_task = _find_image_task(file)
        logging.debug(img_task)
        if img_task not in avail_tasks:
            logging.info('Did not find beta series specification for the task ' +img_task+ ' for image ' +file )
            return
        else:
            beta_series_options = beta_series_options[avail_tasks.index(img_task)]


        hp = float(config.config['BetaSeriesOptions']['FilteringHighPass'])
        lp = float(config.config['BetaSeriesOptions']['FilteringLowPass'])

        events_file = _find_events(config, file)
        logging.debug(events_file)
        if os.path.exists(events_file):
            confounds, fdts = _regression_prep(config, confound_regressors, beta_series)
            ntp = len(confounds)
            if tr is None:
                image_json_path = _find_json(config, file)
                with open(os.path.abspath(image_json_path), "r") as json_path:
                    image_json = json.load(json_path)
                tr = float(image_json['RepetitionTime'])
            filter_toggle = False
            filt = None
            if hp > 0 or lp > 0:
                logging.info('Filtering Toggle Activated')
                filter_toggle = True
                order = int(config.config['BetaSeriesOptions']['FilteringOrder'])
                filt = clpipe.postprocutils.utils.calc_filter(hp, lp, tr, order)
                confounds = clpipe.postprocutils.utils.apply_filter(filt, confounds)
            filt_ev_array, valid_events = _ev_mat_prep(events_file, filt, tr, ntp, beta_series_options)

            image = load_image(file)
            data = image.get_data()
            orgImageShape = data.shape
            coordMap = image.coordmap
            data = data.reshape((numpy.prod(numpy.shape(data)[:-1]), data.shape[-1]))
            data = numpy.transpose(data)
            data = (data - data.mean(axis=0))
            logging.debug(filt_ev_array)
            beta_image_2d = _beta_series_calc(data, filt_ev_array, confounds)
            beta_series_dims = orgImageShape[:-1]
            beta_series_dims =  beta_series_dims + (len(valid_events),)
            beta_3d = beta_image_2d.transpose().reshape(beta_series_dims)
            beta_image = Image(beta_3d, coordMap)
            output_file_path = _build_output_directory_structure(config, file, beta_series)
            events_output = os.path.splitext(os.path.splitext(output_file_path)[0])[0] + "_usedevents.tsv"
            save_image(beta_image, output_file_path)
            valid_events.to_csv(events_output, sep = ' ')
        else:
            logging.info("Did not find an events file for " + file)
            return

def _find_image_task(filename):
    comps = filename.split("_")
    task_comp = [x for x in comps if 'task-' in x][0]
    task_name = task_comp.split('-')[1]
    return task_name


def _ev_mat_prep(event_file, filt, TR, ntp, config_block):
    events = pandas.read_table(event_file)
    #Change back to 'trial_type' once testing is complete
    trial_types = events.loc[:,'trial_type'].tolist()
    logging.debug(trial_types)
    logging.debug(config_block['ExcludeTrialTypes'])
    valid_trials = [ind for ind, x in enumerate(trial_types) if x not in [config_block['ExcludeTrialTypes']]]
    valid_events = events.iloc[valid_trials,:]

    timeCourse = numpy.arange(0, 32 + TR / 16.0, (TR / 16.0))
    time_up = numpy.arange(0, TR * ntp, TR / 16.0)
    n_up = len(time_up)
    hrf = nipy.modalities.fmri.hrf.spm_hrf_compat(timeCourse)
    indexSample = numpy.arange(0, TR * ntp / (TR / 16.0), TR / (TR / 16.0))
    indexSample = indexSample.astype("int")
    eventArray = numpy.zeros((ntp, len(valid_trials)))
    for index, row in valid_events.iterrows():
        ev_loop = numpy.zeros(n_up)
        index1 = numpy.logical_and((time_up >= row["onset"]), (time_up <= row["onset"] + row["duration"]))
        ev_loop[index1] = 1
        ev_loop = numpy.convolve(ev_loop, hrf)
        ev_loop = ev_loop[:-(len(hrf) - 1)]
        ev_loop = ev_loop[indexSample]
        eventArray[:, index] = ev_loop
    if filt is not None:
        filt_event_array = clpipe.postprocutils.utils.apply_filter(filt, eventArray)
    else:
        filt_event_array = eventArray
    return filt_event_array, valid_events


def _beta_series_calc(data, filt_ev_mat, filt_confound_mat):
    beta_maker = numpy.zeros(filt_ev_mat.shape)
    logging.debug(beta_maker.shape)
    for index in range(filt_ev_mat.shape[1]):
        logging.debug(filt_ev_mat[:,index].shape)
        logging.debug(filt_confound_mat.shape)
        logging.debug((numpy.sum(filt_ev_mat,1) - filt_ev_mat[:,index]).shape)
        temp_mat = numpy.concatenate([numpy.expand_dims(filt_ev_mat[:,index],1), numpy.expand_dims(numpy.sum(filt_ev_mat,1) - filt_ev_mat[:,index],1), filt_confound_mat],1)
        temp_beta = numpy.linalg.pinv(temp_mat)
        logging.debug(temp_beta.shape)
        beta_maker[:, index] = temp_beta[0,:]

    betas = numpy.matmul(beta_maker.transpose(), data)
    return betas


def _regression_prep(config, confound_filepath, beta_series_toggle = False):
    confounds = pandas.read_table(confound_filepath, dtype="float", na_values="n/a")
    confounds = confounds.fillna(0)
    reg_labels = config.config['PostProcessingOptions']['RegressionParameters']
    stream_toggle = 'PostProcessingOptions'
    if beta_series_toggle:
        stream_toggle = 'BetaSeriesOptions'
        logging.info("Using beta series regression options.")
        logging.debug(stream_toggle)
    regression_type = json.load(resource_stream(__name__, 'data/RegressionOptions.json'))
    target_label = next((item for item in regression_type['RegressionOptions'] if
                         item["Name"] == config.config[stream_toggle]['NuisanceRegression']), False)
    if not target_label:
        raise ValueError
    fd = confounds[reg_labels['FDLabel']]
    confound_labels = []
    confound_labels.extend(reg_labels["MotionParams"])

    if config.config[stream_toggle]['WhiteMatter']:
        confound_labels.extend([reg_labels["WhiteMatter"]])
    if config.config[stream_toggle]['CSF']:
        confound_labels.extend([reg_labels["CSF"]])
    if config.config[stream_toggle]['GlobalSignalRegression']:
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


def _find_events(config, filepath):
    session_toggle = False
    if 'ses-' in filepath:
        session_toggle = True


    file_name = os.path.basename(filepath)
    file_name = os.path.splitext(os.path.splitext(file_name)[0])[0]
    file_components = file_name.split("_")

    file_components = [x for x in file_components if 'desc-' not in x]
    file_components = [x for x in file_components if 'space-' not in x]
    file_components = [x for x in file_components if 'bold' not in x]
    sub_comp = [x for x in file_components if 'sub-' in x]
    ses_comp = [x for x in file_components if 'ses-' in x]


    event_name = '_'.join(file_components)+"_events.tsv"
    if session_toggle:
        event_path = os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], sub_comp[0], ses_comp[0], 'func', event_name)
    else:
        event_path = os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], sub_comp[0], 'func',
                                  event_name)
    return event_path

def _build_output_directory_structure(config, filepath, beta_series_toggle = False):
    output_type = 'PostProcessingOptions'
    if beta_series_toggle:
        output_type = 'BetaSeriesOptions'
        logging.debug(output_type)

    target_directory = filepath[filepath.find('sub-'):]
    target_directory = os.path.dirname(target_directory)
    target_directory = os.path.join(config.config[output_type]['OutputDirectory'], target_directory)
    logging.debug(target_directory)
    os.makedirs(target_directory, exist_ok=True)
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    logging.debug(config.config[output_type]['OutputSuffix'])
    file_name = sans_ext + '_' + config.config[output_type]['OutputSuffix']
    logging.debug(file_name)
    return os.path.join(target_directory, file_name)


def _notch_filter_fd(config, confounds_filepath, tr, drop_tps = None):
    confounds = pandas.read_table(confounds_filepath, dtype="float", na_values="n/a")
    confounds = confounds.fillna(0)
    if drop_tps is not None:
        confounds = confounds.iloc[:(confounds.shape[0]-drop_tps)]
    reg_labels = config.config['PostProcessingOptions']['RegressionParameters']
    confounds = numpy.array(confounds[reg_labels["MotionParams"]])
    band = config.config['PostProcessingOptions']['RespNotchFilterBand']
    filt_fd = clpipe.postprocutils.utils.notch_filter(confounds, band, tr)
    return filt_fd
