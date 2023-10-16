import pandas as pd
import json as js
import logging
import sys
from clpipe.config_json_parser import ClpipeConfigParser, file_folder_generator
from clpipe.error_handler import exception_handler
import numpy as np
import os
import click


@click.command()
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="Use a specified configuration file. If used, this command will create a codebook for the participants.tsv contained in the BIDS directory of the project.",
)
@click.option(
    "-file_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Create a .json codebook for the specified tab delimited file.",
)
@click.option(
    "-debug", is_flag=True, help="Flag to enable detailed error messages and traceback"
)
def create_json_codebook(config_file=None, file_path=None, debug=False):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)
    if file_path is not None:
        if config_file is None and not os.path.exists(file_path):
            raise (FileNotFoundError("Did not find specified tabular file."))

        if config_file is not None and os.path.exists(file_path):
            raise (
                FileExistsError(
                    "You specified both a config file and a target tabular file. Please specify only one of these options."
                )
            )
    elif config_file is not None:
        file_path = os.path.join(
            config.config["DICOMToBIDSOptions"]["BIDSDirectory"], "participants.tsv"
        )
        if not os.path.exists(file_path):
            raise (
                FileNotFoundError(
                    "Did not find a participants.tsv file in the BIDS directory."
                )
            )

    data = pd.read_csv(file_path, delimiter=",")

    possible_cat = [np.int64, np.object, np.float64]
    data_dict = {}
    for column in data.columns:
        if data.dtypes[column] in possible_cat:
            if len(data[column].unique()) <= 12:
                levels_dict = dict(
                    zip(
                        sorted(data[column].unique().astype(str)),
                        ["FILL IN"] * len(data[column].unique()),
                    )
                )
                print(levels_dict)

                item_dict = {
                    "LongName": "FILL IN",
                    "Description": "FILL IN",
                    "Levels": levels_dict,
                    "TermURL": "FILL IN",
                }
            else:
                item_dict = {
                    "LongName": "FILL IN",
                    "Description": "FILL IN",
                    "Units": "FILL IN",
                    "TermURL": "FILL IN",
                }
        else:
            item_dict = {
                "LongName": "FILL IN",
                "Description": "FILL IN",
                "Units": "FILL IN",
                "TermURL": "FILL IN",
            }

        if "Levels" in item_dict.keys():
            if "nan" in item_dict["Levels"].keys():
                del item_dict["Levels"]["nan"]
        data_dict[column] = item_dict

    ext = os.path.splitext(file_path)[1]
    output_file = file_path.replace(ext, ".json")
    with open(output_file, "w") as fp:
        js.dump(data_dict, fp, indent="\t")
