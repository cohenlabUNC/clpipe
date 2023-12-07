# Reports how many columns in a given confounds file are outliers.

import logging
import pandas as pd
from pathlib import Path
from multiprocessing import Pool


def get_image_confounds(confounds_file):
    confound_file_stem = Path(confounds_file).stem

    logger = logging.getLogger(confound_file_stem)
    logger.info(f"Counting outliers in file: {str(confounds_file)}")

    header_opt = None

    # Quick and dirty way to check for header
    with open(confounds_file) as f:
        firstLine = f.readline()
        firstChar = firstLine.split("\t")[0]
        try:
            float(firstChar)
        except ValueError:
            header_opt = "infer"

    # Read in the data with pandas
    confounds = pd.read_csv(confounds_file, sep="\t", header=header_opt)

    # Count the number of non-zero values in each column
    # Output a vector of non-zero count for each column
    count_non_zero_df = confounds.astype(bool).sum(axis=0)

    # Consider any column with only one non-zero value to be an outlier column
    # Output the total number of outlier columns as a scalar
    try:
        total_outlier_volumes = count_non_zero_df.value_counts()[1]
    except KeyError:
        total_outlier_volumes = 0
    # Fetch the number of rows
    total_volumes = confounds.shape[0]

    # Calculate the ratio and percentage of outliers
    outlier_ratio = total_outlier_volumes / total_volumes
    percent_outliers = outlier_ratio * 100

    # Show the results
    result_string = "Found {} outlier volumes out of {} total volumes. Percent outlier volumes: {:2.2%}".format(
        total_outlier_volumes, total_volumes, outlier_ratio
    )
    logger.info(result_string)

    # Create result dataframe
    result_df = pd.DataFrame(
        data={
            "confound_file": confound_file_stem,
            "total_outliers": [total_outlier_volumes],
            "total_volumes": [total_volumes],
            "percent_outliers": [round(percent_outliers, 2)],
        }
    )

    return result_df


def get_study_outliers(confounds_dir, output_file, confounds_suffix="confounds.tsv"):
    logger = logging.getLogger("ConfoundsDir")
    logger.level = logging.INFO

    to_process = []
    match_pattern = f"sub-*/**/*{confounds_suffix}"

    confounds_files = list(Path(confounds_dir).glob(match_pattern))
    if len(confounds_files) == 0:
        raise ValueError(
            f"No confounds files found matching pattern: {match_pattern}. Try setting the --confounds_suffix option to match your confounds file name."
        )

    for confounds_file in confounds_files:
        logger.debug(f"Found confounds file: {confounds_file}")
        to_process.append(confounds_file)

    logger.info(f"Calculating outlier counts for {len(confounds_files)} images")

    with Pool(processes=20) as pool:
        result = pd.concat(pool.map(get_image_confounds, to_process))
        result.set_index("confound_file", inplace=True)
        print(result)
        result.to_csv(output_file, sep="\t")
