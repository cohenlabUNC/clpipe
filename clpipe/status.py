from pathlib import Path
import pandas as pd
import os
import csv
import datetime
import click

CLICK_FILE_TYPE_EXISTS = click.Path(
    exists=True, dir_okay=False, file_okay=True)

STATUS_HEADER = [
    "subject", "session", "step", "event", "timestamp", "source", "note"
]
STEPS = [
    'ingestion', 'bids-conversion', 'fmriprep-process', 
    'qa', 'clpipe-preprocessing'
]
SUB_ID_TYPE = {'subject': 'string'}
TYPES = {'timestamp': 'datetime64', 'subject': 'string'}
DEFAULT_CACHE_PATH = "./.pipeline/status_log.csv"
DEFAULT_STEP = STEPS[1]
DEFAULT_EVENT = "submitted"
DEFAULT_NOTE = "clpipe generated"
CACHE_FILE_HELP = "Path to your status cache file."


#TODO: Move cli commands back to specific modules to avoid circular import here 
@click.command()
@click.option('-cache_file', type=CLICK_FILE_TYPE_EXISTS,
              help=CACHE_FILE_HELP)
def status(cache_file):
    show_latest_by_step(cache_file)


def _load_records(cache_path: os.PathLike) -> pd.DataFrame:
    
    records: pd.DataFrame = pd.read_csv(cache_path, dtype = SUB_ID_TYPE)
    records = records.astype(TYPES)
    return records


def _get_records_latest(records: pd.DataFrame) -> pd.DataFrame:
    latest_records = records.sort_values(
        'timestamp', ascending=False
    ).groupby(
        ['subject', 'step'], dropna=False, as_index=False
    ).agg({
        'timestamp': 'max',
        'event': 'first',
        'note': 'first'}
    )
    return latest_records


def _get_records_by_step(records: pd.DataFrame, 
                        step=DEFAULT_STEP) -> pd.DataFrame:
    records_by_step = records.loc[
        records['step'] == step
    ]
    return records_by_step


def _get_records_by_event(records: pd.DataFrame,
                          event=DEFAULT_EVENT) -> pd.DataFrame:
    records_by_event = records.loc[
        records['event'] == event
    ]
    return records_by_event


def _get_records_pivot(records: pd.DataFrame):
    latest_events_pivot = records.pivot(
        index="subject", columns="step", values='event')

    return latest_events_pivot


def needs_processing(subjects: list, cache_path: os.PathLike, 
                     step=DEFAULT_STEP):
    try:
        records = _load_records(cache_path)
    except FileNotFoundError:
        return subjects

    latest_records = _get_records_latest(records)
    latest_records_type = _get_records_by_step(latest_records, step=step)
    latest_records_event = _get_records_by_event(
        latest_records_type, event=DEFAULT_EVENT)

    completed = latest_records_event['subject'].tolist()

    needs_processing = [x for x in subjects if x not in completed]
    return needs_processing


def write_record(subject: str, session: str="", 
                 cache_path: os.PathLike=DEFAULT_CACHE_PATH,
                 step=DEFAULT_STEP, event=DEFAULT_EVENT,
                 note=DEFAULT_NOTE):
    timestamp = datetime.datetime.now()
    cache_path = Path(cache_path)

    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True)
        with open(cache_path, "w") as cache_file:
            csv_writer = csv.writer(cache_file)
            csv_writer.writerow(STATUS_HEADER)

    with open(cache_path, "a") as cache_file:
        csv_writer = csv.writer(cache_file)
        csv_writer.writerow(
            [subject, session, step, event, timestamp, "", note]
        )


def get_latest_by_step(cache_path: os.PathLike):
    records = _load_records(cache_path)

    latest_records = _get_records_latest(records)
    latest_records_pivot = _get_records_pivot(latest_records)

    present_steps = [x for x in records['step'].unique() if x in STEPS]

    latest_records_pivot_reordered = latest_records_pivot[present_steps]
    latest_records_pivot_reordered_fillna = \
        latest_records_pivot_reordered.fillna('pending')

    return latest_records_pivot_reordered_fillna


def show_latest_by_step(cache_path: os.PathLike):
    latest_by_step = get_latest_by_step(cache_path)
    click.echo(latest_by_step)