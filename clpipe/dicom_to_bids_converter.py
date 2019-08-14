import click
from .batch_manager import BatchManager,Job
from .config_json_parser import ConfigParser
import os
from pkg_resources import resource_stream, resource_filename
import parse
import glob
from .error_handler import exception_handler
import sys
import logging

@click.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default = None, help = 'The configuration file for the study, use if you have a custom batch configuration.')
@click.option('-subject', required=True, default=None, help = 'A subject that has all scans of interest present.')
@click.option('-session', default=None, help = 'A session indicator, if sessions are present')
@click.option('-dicom_directory', required = True, help = 'The specially formatted dicom directory string. Please see help pages at https://clpipe.readthedocs.io/en/latest/index.html for more details')
@click.option('-output_file', default = "dicom_info.tsv", help = 'The dicom info output file name.')
@click.option('-submit', is_flag = True, default=False, help = 'Submission job to HPC.')
def dicom_to_nifti_to_bids_converter_setup(subject = None, session = None, dicom_directory=None, output_file=None, config_file = None,  submit=False):
    """This command can be used to compute and extract a dicom information spreadsheet so that a heuristic file can be written. Users should specify a subject with all scans of interest present, and run this command on all sessions of interest. """
    config = ConfigParser()
    config.config_updater()

    heuristic_file = resource_filename(__name__, 'data/setup_heuristic.py')

    if session:
        heudiconv_string = '''module add heudiconv \n heudiconv -d {dicomdirectory} -s {subject} '''\
        ''' -ss {sess} -f {heuristic} -o ./test/ -b --minmeta \n cp ./test/'''\
        '''.heudiconv/{subject}/ses-{sess}/info/dicominfo_ses-{sess}.tsv {outputfile} \n rm -rf ./test/'''
    else:
        heudiconv_string = '''module add heudiconv \n heudiconv -d {dicomdirectory} -s {subject} ''' \
                           ''' -f {heuristic} -o ./test/ -b --minmeta \n cp ./test/''' \
                           '''.heudiconv/{subject}/info/dicominfo.tsv {outputfile} \n rm -rf ./test/'''

    batch_manager = BatchManager(config.config['BatchConfig'], None)
    batch_manager.update_time('1:0:0')
    batch_manager.update_mem_usage('3000')
    if session:
        job1 = Job("heudiconv_setup", heudiconv_string.format(
            dicomdirectory=os.path.abspath(dicom_directory),
            subject=subject,
            sess=session,
            heuristic = heuristic_file,
            outputfile = os.path.abspath(output_file),
        ))
    else:
        job1 = Job("heudiconv_setup", heudiconv_string.format(
            dicomdirectory=os.path.abspath(dicom_directory),
            subject=subject,
            heuristic = heuristic_file,
            outputfile = os.path.abspath(output_file),
        ))

    batch_manager.addjob(job1)
    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-heuristic_file', default = '', help = 'A heuristic file to use')
@click.option('-dicom_directory', default = '',help = 'The specially formatted dicom directory string. Please see help pages at https://clpipe.readthedocs.io/en/latest/index.html for more details')
@click.option('-output_directory', default = '', help = 'Where to output the converted dataset')
@click.option('-log_output_dir', default = '', help = 'Where to put the log files. Defaults to Batch_Output in the current working directory.')
@click.option('-overwrite', is_flag=True, default=False, help = 'Overwrite previous files?')
@click.option('-submit', is_flag=True, default=False, help = 'Submit jobs to HPC')
@click.option('-debug', is_flag=True, default=False, help = 'Debug flag for traceback')
def dicom_to_nifti_to_bids_converter(subjects = None, dicom_directory=None, submit=False, output_directory= None, heuristic_file = None,debug = False, log_output_dir = None, overwrite = False):
    """This command uses heudiconv to convert dicoms into BIDS formatted NiFTI files. Users can specify any number of subjects, or leave subjects blank to convert all subjects. """
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ConfigParser()
    config.config_updater(config_file)
    config.setup_heudiconv(dicom_directory,
                           os.path.abspath(heuristic_file),
                           os.path.abspath(output_directory))

    if not any([config.config['DICOMToBIDSOptions']['DICOMDirectory'],
            config.config['DICOMToBIDSOptions']['OutputDirectory'],
            config.config['DICOMToBIDSOptions']['HeuristicFile']]):
        raise ValueError('DICOM directory, output directory and/or heuristic file are not specified.')

    if not log_output_dir:
        log_output_dir = os.path.abspath(os.path.join('.', 'Batch_Output'))
    else:
        log_output_dir = os.path.abspath(log_output_dir)

    heuristic_file = resource_filename(__name__, 'data/setup_heuristic.py')

    parse_string = config.config['DICOMToBIDSOptions']['DICOMDirectory'].replace('/*', '')
    parse_string = parse_string.replace('*', '')
    if '{session}' in config.config['DICOMToBIDSOptions']['DICOMDirectory']:
        session_toggle = True
        all_dicoms = glob.glob(parse_string.format(
            subject = "*",
            session = "*"
        ))
    else:
        session_toggle = False
        all_dicoms = glob.glob(parse_string.format(
            subject="*"
        ))
    parser = parse.compile(parse_string)

    fileinfo = [parser.parse(x).named for x in all_dicoms if parser.parse(x) is not None]


    if subjects:
        fileinfo = [x for x in fileinfo if x['subject'] in subjects]


    if session_toggle:
        heudiconv_string = '''module add heudiconv \n heudiconv -d {dicomdirectory} -s {subject} '''\
        ''' -ss {sess} -f {heuristic} -o {output_directory} -b --minmeta'''
    else:
        heudiconv_string = '''module add heudiconv \n heudiconv -d {dicomdirectory} -s {subject} ''' \
                           ''' -f {heuristic} -o {output_directory} -b --minmeta'''
    if overwrite:
        heudiconv_string = '''module add heudiconv \n heudiconv -d {dicomdirectory} -s {subject} ''' \
                           ''' -f {heuristic} -o {output_directory} -b --minmeta --overwrite'''
    batch_manager = BatchManager(config.config['BatchConfig'], log_output_dir)
    batch_manager.createsubmissionhead()
    for file in fileinfo:
        subject_id = file['subject']
        subject_id = subject_id.replace('/*', '')
        subject_id = subject_id.replace('*', '')
        if session_toggle:
             session_id = file['session']
             session_id = session_id.replace('/*', '')
             session_id = session_id.replace('*', '')
             job_id = 'convert_sub-' + file['subject'] + '_ses-' + file['session']
             job1 = Job(job_id, heudiconv_string.format(
                dicomdirectory=config.config['DICOMToBIDSOptions']['DICOMDirectory'],
                subject=subject_id,
                sess=session_id,
                heuristic = config.config['DICOMToBIDSOptions']['HeuristicFile'],
                output_directory = config.config['DICOMToBIDSOptions']['OutputDirectory']
            ))
        else:
            job_id = 'convert_sub-' + file['subject']
            job1 = Job(job_id, heudiconv_string.format(
                dicomdirectory=config.config['DICOMToBIDSOptions']['DICOMDirectory'],
                subject=subject_id,
                heuristic=config.config['DICOMToBIDSOptions']['HeuristicFile'],
                output_directory=os.path.abspath(config.config['DICOMToBIDSOptions']['OutputDirectory'])
            ))
        batch_manager.addjob(job1)


    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
        config.config_json_dump(config.config['DICOMToBIDSOptions']['OutputDirectory'], config_file)
    else:
        batch_manager.print_jobs()
