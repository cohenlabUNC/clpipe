import os
import glob
import click
import pandas
import nibabel as nib
import json
import numpy
import gc
import psutil
import re

from pkg_resources import resource_filename

from .postprocutils.utils import (
    get_scrub_vector, calc_filter, apply_filter, regress, scrub_image, notch_filter
)
from .postprocutils.spec_interpolate import spec_inter
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from .errors import SubjectNotFoundError
from .utils import get_logger, add_file_handler

STEP_NAME = "postprocess"

def fmri_postprocess(config_file=None, subjects=None, target_dir=None, target_suffix=None, output_dir=None,
                     output_suffix=None, log_dir=None,
                     submit=False, batch=True, task=None, tr=None, processing_stream = None, debug = False, beta_series = False):
    """This command runs an fMRIprep'ed dataset through additional processing, as defined in the configuration file. To run specific subjects, specify their IDs. If no IDs are specified, all subjects are ran."""

    if config_file is None and tr is None:
        raise ValueError('No config file and no specified TR. Please include one.')

    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_postproc(target_dir, target_suffix, output_dir, output_suffix, beta_series,
                          log_dir)
    config.validate_config()

    add_file_handler(os.path.join(config.config["ProjectDirectory"], "logs"))
    logger = get_logger(STEP_NAME, debug=debug)

    if beta_series:
          raise ValueError("At this time, the beta series functionality is no longer working due to incompatibilities between packages.")
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
                        '''-output_dir={outputDir} -output_suffix={outputSuffix} {procstream} -log_dir={logOutputDir} {taskString} {trString} {beta_series} -single {sub}'''
    task_string = ""
    tr_string = ""
    beta_series_string = ""
    if task is not None:
        task_string = '-task='+task
    if tr is not None:
        tr_string = '-TR='+tr
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
    else:
        for sub in subjects:
            logger.debug(beta_series)
            logger.info('Running Subject ' + sub)
            _fmri_postprocess_subject(config, sub, task, logger, tr, beta_series)


def _fmri_postprocess_subject(config, subject, task, logger, tr=None, beta_series = False):
    if beta_series:
          output_type = 'BetaSeriesOptions'
    else:
          output_type = 'PostProcessingOptions'
    search_string = os.path.abspath(
        os.path.join(config.config[output_type]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config[output_type]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)
    if len(subject_files) == 0:
        raise SubjectNotFoundError(f"No subjects found on search path: {search_string}")
    if config.config['PostProcessingOptions']["DropCSV"] is not "":
        drop_tps = pandas.read_csv(config.config['PostProcessingOptions']["DropCSV"])

    logger.info('Finding Image Files')
    for image in subject_files:
        if task is None or 'task-' + task in image:
            logger.info('Processing ' + image)
            try:
                tps_drop = None
                temp = None
                if config.config['PostProcessingOptions']["DropCSV"] is not "":
                    temp = drop_tps[drop_tps['file_name'].str.match(os.path.basename(image))]['TR_round']
                    if len(temp) is 1:
                        tps_drop = int(temp)
                        logger.info('Found drop TP info, will remove last ' + str(tps_drop) + ' time points')
                else:
                        tps_drop = None
                _fmri_postprocess_image(config, image, logger, task,  tr, beta_series, tps_drop)
            except Exception as err:
                logger.exception(err)


def _fmri_postprocess_image(config, file, logger, task = None, tr=None, beta_series = False, drop_tps = None):
    confound_regressors = _find_confounds(config, file)
    output_file_path = _build_output_directory_structure(config, file, logger, beta_series)

    if os.path.exists(output_file_path):
      logger.info("Output File Exists! Skipping.")
      return 0

    logger.info('Looking for: ' + confound_regressors)

    if not os.path.exists(confound_regressors):
        logger.warning('Could not find a confound file for ' + file + ". Moving onto next scan")
        return
    else:
        logger.info('Found confound regressors')
        confounds, fdts = _regression_prep(config, confound_regressors, logger)
        if drop_tps is not None:
            c_f_t = pandas.DataFrame(confounds)
            c_f_t = c_f_t.iloc[:(c_f_t.shape[0]-(drop_tps))]
            confounds = numpy.asarray(c_f_t)
            logger.info('Removing last ' + str(drop_tps) + ' time points')
            fdts = fdts.iloc[:(fdts.shape[0]-(drop_tps))]
        if tr is None:
            image_json_path = _find_json(config, file, logger)
            with open(os.path.abspath(image_json_path), "r") as json_path:
                image_json = json.load(json_path)
            tr = image_json['RepetitionTime']
        tr = float(tr)
        logger.info('TR found: ' + str(tr))
        image = nib.load(file)
        data = image.get_fdata()
        data = data.astype(numpy.float32)
        orgImageShape = data.shape
        coordMap = image.affine
        data = data.reshape((numpy.prod(numpy.shape(data)[:-1]), data.shape[-1]))
        data = numpy.transpose(data)
        if drop_tps is not None:
            data = data[0:(data.shape[0]-(drop_tps)), :]
            orgImageShape = list(orgImageShape)
            orgImageShape[3] = data.shape[0]
            orgImageShape = tuple(orgImageShape)
        row_means = data.mean(axis=0)
        data = (data - data.mean(axis=0))
    if not beta_series:
        regress_toggle = config.config['PostProcessingOptions']['Regress']

        scrub_toggle = False
        if config.config['PostProcessingOptions']['Scrubbing']:
            logger.debug('Scrubbing Toggle Activated')
            scrub_toggle = True
            scrub_ahead = int(config.config['PostProcessingOptions']['ScrubAhead'])
            scrub_behind = int(config.config['PostProcessingOptions']['ScrubBehind'])
            scrub_contig = int(config.config['PostProcessingOptions']['ScrubContig'])
            fd_thres = float(config.config['PostProcessingOptions']['ScrubFDThreshold'])
            orig_fdts = fdts
            if config.config['PostProcessingOptions']['RespNotchFilter']:
                fdts = _notch_filter_fd(config,  confound_regressors, tr, drop_tps)

            scrubTargets = get_scrub_vector(fdts, fd_thres, scrub_behind, scrub_ahead, scrub_contig)

        hp = float(config.config['PostProcessingOptions']['FilteringHighPass'])
        lp = float(config.config['PostProcessingOptions']['FilteringLowPass'])
        filter_toggle = False
        if hp > 0 or lp > 0:
            logger.info('Filtering Toggle Activated')
            filter_toggle = True
            order = int(config.config['PostProcessingOptions']['FilteringOrder'])
            filt = calc_filter(hp, lp, tr, order)
            confounds = apply_filter(filt, confounds)

        if scrub_toggle and filter_toggle:
            logger.info('Using Spectral Interpolation')
            ofreq = int(config.config['PostProcessingOptions']['OversamplingFreq'])
            hfreq = float(config.config['PostProcessingOptions']['PercentFreqSample'])
            logger.debug('Memory Usage Before Spectral Interpolation:' +str(psutil.virtual_memory().total >> 30) +' GB')
            data = spec_inter(data, tr, ofreq, scrubTargets, hfreq, binSize=config.config['PostProcessingOptions']["SpectralInterpolationBinSize"])

        gc.collect()

        logger.debug('Memory Usage After Spectral Interpolation GC:' +str(psutil.virtual_memory().total >> 30) +' GB')



        if filter_toggle:
            logger.info('Filtering Data Now')
            data = apply_filter(filt, data)
        if regress_toggle:
            logger.info('Regressing Data Now')
            logger.debug(str(confounds.shape))
            logger.debug(str(data.shape))
            data = regress(confounds, data)
        if scrub_toggle:
            logger.info('Scrubbing data Now')
            data = scrub_image(data, scrubTargets)

        data = (data + row_means)

        data = numpy.transpose(data)
        data = data.reshape(orgImageShape)
        data32 = numpy.float32(data)
        out_image = nib.Nifti1Image(data32, coordMap)

        output_file_path = _build_output_directory_structure(config, file, logger)
        logger.info('Saving post processed data to ' + output_file_path)
        nib.save(out_image, output_file_path)

        if scrub_toggle:
            file_name = os.path.basename(file)
            sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
            toOut = numpy.column_stack([numpy.arange(1, len(scrubTargets) + 1, 1), numpy.asarray(scrubTargets), fdts, orig_fdts])
            logger.info('Saving Scrub Targets to ' + os.path.join(os.path.dirname(output_file_path),
                                                                   sans_ext + "_scrubTargets.csv"))
            numpy.savetxt(os.path.join(os.path.dirname(output_file_path), sans_ext + "_scrubTargets.csv"), toOut,
                          delimiter=",")
    else:
        beta_series_options = config.config['BetaSeriesOptions']['TaskSpecificOptions']

        avail_tasks = [x['Task'] for x in beta_series_options]
        logger.debug(avail_tasks)
        img_task = _find_image_task(file)
        logger.debug(img_task)
        if img_task not in avail_tasks:
            logger.info('Did not find beta series specification for the task ' +img_task+ ' for image ' +file )
            return
        else:
            beta_series_options = beta_series_options[avail_tasks.index(img_task)]


        hp = float(config.config['BetaSeriesOptions']['FilteringHighPass'])
        lp = float(config.config['BetaSeriesOptions']['FilteringLowPass'])

        events_file = _find_events(config, file)
        logger.debug(events_file)
        if os.path.exists(events_file):
            confounds, fdts = _regression_prep(config, confound_regressors, beta_series, logger)
            ntp = len(confounds)
            if tr is None:
                image_json_path = _find_json(config, file, logger)
                with open(os.path.abspath(image_json_path), "r") as json_path:
                    image_json = json.load(json_path)
                tr = float(image_json['RepetitionTime'])
            filter_toggle = False
            filt = None
            if hp > 0 or lp > 0:
                logger.info('Filtering Toggle Activated')
                filter_toggle = True
                order = int(config.config['BetaSeriesOptions']['FilteringOrder'])
                filt = calc_filter(hp, lp, tr, order)
                confounds = apply_filter(filt, confounds)
            filt_ev_array, valid_events = _ev_mat_prep(events_file, filt, tr, ntp, beta_series_options, logger)

            image = nib.load(file)
            data = image.get_fdata()
            data = data.astype(numpy.float32)
            orgImageShape = data.shape
            coordMap = image.affine
            data = data.reshape((numpy.prod(numpy.shape(data)[:-1]), data.shape[-1]))
            data = numpy.transpose(data)
            data = (data - data.mean(axis=0))
            logger.debug(filt_ev_array)
            beta_image_2d = _beta_series_calc(data, filt_ev_array, confounds, logger)
            beta_series_dims = orgImageShape[:-1]
            beta_series_dims =  beta_series_dims + (len(valid_events),)
            beta_3d = beta_image_2d.transpose().reshape(beta_series_dims)
            beta_image = nib.Nifti1Image(beta_3d, coordMap)
            output_file_path = _build_output_directory_structure(config, file, logger, beta_series)
            events_output = os.path.splitext(os.path.splitext(output_file_path)[0])[0] + "_usedevents.tsv"
            nib.save(beta_image, output_file_path)
            valid_events.to_csv(events_output, sep = ' ')
        else:
            logger.info("Did not find an events file for " + file)
            return

def _find_image_task(filename):
    comps = filename.split("_")
    task_comp = [x for x in comps if 'task-' in x][0]
    task_name = task_comp.split('-')[1]
    return task_name


def _ev_mat_prep(event_file, filt, TR, ntp, config_block, logger):
    events = pandas.read_table(event_file)
    #Change back to 'trial_type' once testing is complete
    trial_types = events.loc[:,'trial_type'].tolist()
    logger.debug(trial_types)
    logger.debug(config_block['ExcludeTrialTypes'])
    valid_trials = [ind for ind, x in enumerate(trial_types) if x not in [config_block['ExcludeTrialTypes']]]
    valid_events = events.iloc[valid_trials,:]

    timeCourse = numpy.arange(0, 32 + TR / 16.0, (TR / 16.0))
    time_up = numpy.arange(0, TR * ntp, TR / 16.0)
    n_up = len(time_up)
    hrf = 0
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
        filt_event_array = apply_filter(filt, eventArray)
    else:
        filt_event_array = eventArray
    return filt_event_array, valid_events


def _beta_series_calc(data, filt_ev_mat, filt_confound_mat, logger):
    beta_maker = numpy.zeros(filt_ev_mat.shape)
    logger.debug(beta_maker.shape)
    for index in range(filt_ev_mat.shape[1]):
        logger.debug(filt_ev_mat[:,index].shape)
        logger.debug(filt_confound_mat.shape)
        logger.debug((numpy.sum(filt_ev_mat,1) - filt_ev_mat[:,index]).shape)
        temp_mat = numpy.concatenate([numpy.expand_dims(filt_ev_mat[:,index],1), numpy.expand_dims(numpy.sum(filt_ev_mat,1) - filt_ev_mat[:,index],1), filt_confound_mat],1)
        temp_beta = numpy.linalg.pinv(temp_mat)
        logger.debug(temp_beta.shape)
        beta_maker[:, index] = temp_beta[0,:]

    betas = numpy.matmul(beta_maker.transpose(), data)
    return betas


def _regression_prep(config, confound_filepath, logger):
    confounds = pandas.read_table(confound_filepath, dtype="float", na_values="n/a")
    confounds = confounds.fillna(0)
    if len(config.config["PostProcessingOptions"]['Confounds']) > 0:
        cons_re = [re.compile(regex_wildcard(co)) for co in config.config["PostProcessingOptions"]['Confounds']]
        target_cols = []
        for reg in cons_re:
            logger.debug(str([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None]))
            target_cols.extend([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logger.debug("Confound Columns " + str(target_cols))
        confounds_mat = confounds[target_cols]
    if len(config.config["PostProcessingOptions"]['ConfoundsQuad']) > 0:
        cons_re = [re.compile(regex_wildcard(co)) for co in config.config["PostProcessingOptions"]['ConfoundsQuad']]
        target_cols = []
        for reg in cons_re:
            target_cols.extend(
                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logger.debug("Quad Columns " + str(target_cols))
        confounds_quad_mat = confounds[target_cols]
        confounds_quad_mat.rename(columns=lambda x: x + "_quad", inplace=True)
        confounds_quad_mat = confounds_quad_mat ** 2
        confounds_mat = pandas.concat([confounds_mat, confounds_quad_mat], axis=1, ignore_index=True)
        logger.debug(str(confounds_mat.shape))
    if len(config.config["PostProcessingOptions"]['ConfoundsDerive']) > 0:
        cons_re = [re.compile(regex_wildcard(co)) for co in config.config["PostProcessingOptions"]['ConfoundsDerive']]
        target_cols = []
        for reg in cons_re:
            target_cols.extend(
                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logger.debug("Lagged Columns " + str(target_cols))
        confounds_lagged_mat = confounds[target_cols]
        confounds_lagged_mat.rename(columns=lambda x: x + "_lagged", inplace=True)
        confounds_lagged_mat = confounds_lagged_mat.diff()
        confounds_mat = pandas.concat([confounds_mat, confounds_lagged_mat], axis=1, ignore_index=True)
        logger.debug(str(confounds_mat.shape))
        logger.debug(str(confounds_mat.head(5)))
    if len(config.config["PostProcessingOptions"]['ConfoundsQuadDerive']) > 0:
        cons_re = [re.compile(regex_wildcard(co)) for co in
                   config.config["PostProcessingOptions"]['ConfoundsQuadDerive']]
        target_cols = []
        for reg in cons_re:
            target_cols.extend(
                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logger.debug("Quadlagged Columns " + str(target_cols))
        confounds_qlagged_mat = confounds[target_cols]
        confounds_qlagged_mat = confounds_qlagged_mat.diff()
        confounds_qlagged_mat = confounds_qlagged_mat ** 2
        confounds_qlagged_mat.rename(columns=lambda x: x + "_qlagged", inplace=True)
        confounds_mat = pandas.concat([confounds_mat, confounds_qlagged_mat], axis=1, ignore_index=True)
        logger.debug(str(confounds_mat.shape))

    fd = confounds[config.config["PostProcessingOptions"]["ScrubVar"]]
    confounds_mat = confounds_mat.fillna(0)
    confounds_mat = numpy.asarray(confounds_mat)
    return confounds_mat, fd


# Rewrite find json function, use task information to be very specific.
def _find_json(config, filepath, logger):
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    components = sans_ext.split('_')

    jsons = glob.glob(os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], '**', '*.json'), recursive=True)
    logger.debug(jsons)
    task = [task_name for task_name in components if "task-" in task_name][0]
    logger.debug(task)
    top_level_json = [json for json in jsons if task + "_bold.json" in json]

    if len(top_level_json) is not 0:
        target_json = top_level_json[0]

    sub_level_json = [json for json in jsons if "_".join(components[0:2]) + "_bold.json" in json]
    logger.debug("_".join(components[0:2]))
    if len(sub_level_json) is not 0:
        target_json = sub_level_json[0]

    scan_level_json = [json for json in jsons if "_".join(components[0:3]) + "_bold.json" in json]
    
    if len(scan_level_json) is not 0:
        target_json = scan_level_json[0]
    else:
      scan_level_json = [json for json in jsons if "_".join(components[0:4]) + "_bold.json" in json]
      if len(scan_level_json) is not 0:
        target_json = scan_level_json[0]
      else:
        scan_level_json = [json for json in jsons if "_".join(components[0:5]) + "_bold.json" in json]
        if len(scan_level_json) is not 0:
            target_json = scan_level_json[0]
    logger.debug("_".join(components[0:5]))

    logger.debug(target_json)
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

def _build_output_directory_structure(config, filepath, logger, beta_series_toggle = False):
    output_type = 'PostProcessingOptions'
    if beta_series_toggle:
        output_type = 'BetaSeriesOptions'
        logger.debug(output_type)

    target_directory = filepath[filepath.find('sub-'):]
    target_directory = os.path.dirname(target_directory)
    target_directory = os.path.join(config.config[output_type]['OutputDirectory'], target_directory)
    logger.debug(target_directory)
    os.makedirs(target_directory, exist_ok=True)
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    logger.debug(config.config[output_type]['OutputSuffix'])
    file_name = sans_ext + '_' + config.config[output_type]['OutputSuffix']
    logger.debug(file_name)
    return os.path.join(target_directory, file_name)


def _notch_filter_fd(config, confounds_filepath, tr, drop_tps = None):
    confounds = pandas.read_table(confounds_filepath, dtype="float", na_values="n/a")
    confounds = confounds.fillna(0)
    if drop_tps is not None:
        confounds = confounds.iloc[:(confounds.shape[0]-drop_tps)]
    confounds = numpy.array(confounds[config.config["PostProcessingOptions"]["MotionVars"]])
    band = config.config['PostProcessingOptions']['RespNotchFilterBand']
    filt_fd = notch_filter(confounds, band, tr)
    return filt_fd

def regex_wildcard(string):
    return '^'+re.sub("\*", ".*", string)+'$'
