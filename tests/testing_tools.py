import tempfile
import os
from pathlib import Path

from click.testing import CliRunner
from clpipe.project_setup import project_setup

NUM_SUBJECTS = 8
PROJECT_TITLE = "test_project"

def setup_test_directory(temporary=True, show=True, num_subjects=NUM_SUBJECTS, project_title=PROJECT_TITLE):
    """
    Sets up a test directory for running against clpipe.

    Args:
        temporary (bool, optional): True uses a temporary location. False sets up a directory
            under TestFiles/[PROJECT_TITLE], which is not idempotent and will fail if a given project
            already exists. Defaults to True.
        show (bool, optional): Prints the generated filesystem. Defaults to True.
        num_subjects (int, optional): Number of subjects to place in data_BIDS. Defaults to NUM_SUBJECTS.
        project_title (str, optional): Name of test directory folder and clpipe project. Defaults to PROJECT_TITLE.

    Raises:
        Exception: Any errors from clpipe project_setup command are raised

    Returns:
        Path: path to the test filesystem
    """

    # Determine the location of the test directory depending on whether it should
    # be temporary or not.
    base_dir = None
    if temporary:
        tmpfile = tempfile.TemporaryDirectory()
        base_dir = Path(tmpfile.name)
    else:
        base_dir = Path("TestFiles")
    base_dir = base_dir / f"{project_title}"

    # clpipe will set this up, but needs a data_DICOMs dir ahead of time, so
    # we will set it up in advance
    raw_data = base_dir / "data_DICOMs"
    raw_data.mkdir(parents=True, exist_ok=True)

    # Use the clpipe CLI to setup project
    runner = CliRunner()
    result = runner.invoke(
        project_setup, 
        [
            '-project_title', project_title, 
            '-project_dir', str(base_dir),
            '-source_data', str(raw_data), 
        ]
    )

    # Raise any exceptions from the CLI
    if result.exit_code != 0:
        raise Exception(result.exception)

    # Populate the BIDS directory
    for sub_num in range(num_subjects):
        subject_folder = base_dir / "data_BIDS" / f"sub-{sub_num}"
        subject_folder.mkdir(parents=True, exist_ok=True)

    if show:
        print(f"[{project_title}]")
        for clpipe_file in os.scandir(base_dir):
            print(f"--- {clpipe_file.name}")
            if clpipe_file.name == 'data_BIDS':
                for bids_file in os.scandir(base_dir / clpipe_file.name):
                    print(f"----- {bids_file.name}")
    
    return base_dir


if __name__ == "__main__":
    setup_test_directory()

