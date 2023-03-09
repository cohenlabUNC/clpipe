DEFAULT_NUM_BIDS_SUBJECTS = 10

def populate_with_BIDS(project_dir, num_subjects=DEFAULT_NUM_BIDS_SUBJECTS):
    """Populate the given project_dir with BIDS data.
    
    project_dir must be existing clpipe project.
    """

    for sub_num in range(num_subjects):
            subject_folder = project_dir / "data_BIDS" / f"sub-{sub_num}"
            subject_folder.mkdir()