from pathlib import Path
import numpy as np
import nibabel as nib
import shutil
import json

from clpipe.config_json_parser import GLMConfigParser

DEFAULT_NUM_BIDS_SUBJECTS = 10
DEFAULT_NUM_DICOM_SUBJECTS = 5
DEFAULT_NUM_FMRIPREP_SUBJECTS = 8
DEFAULT_RANDOM_NII_DIMS = (12, 12, 12, 36)
DICOM_SESSIONS = ['2000', '2010', '2020']

def populate_with_BIDS(project_dir, sample_raw_image, num_subjects=DEFAULT_NUM_BIDS_SUBJECTS):
    """Populate the given project_dir with BIDS data.
    
    project_dir must be existing clpipe project.
    """
    bold_suffix = "bold.nii.gz"

    for sub_num in range(num_subjects):
        subject_folder = project_dir / "data_BIDS" / f"sub-{sub_num}"
        subject_folder.mkdir()
        subject_folder = project_dir / "data_BIDS" / f"sub-{sub_num}" / "func"
        subject_folder.mkdir()
        task_info = f"task-rest"
        shutil.copy(sample_raw_image, subject_folder / f"sub-{sub_num}_{task_info}_{bold_suffix}")

def populate_with_DICOM(project_dir: Path, num_subjects=DEFAULT_NUM_DICOM_SUBJECTS):
    """For the given clpipe project dir, populate the data_DICOMs folder. 
    
    project_dir must be an existing clpipe project
    """
    dicom_dir = project_dir / "data_DICOMs"

    sub = dicom_dir / "sub"
    session_sub = dicom_dir / "session_sub"
    session_sub_flat = dicom_dir / "session_sub_flat"
    sub_session = dicom_dir / "sub_session"
    sub_session_flat = dicom_dir / "sub_session_flat"

    for sub_num in range(num_subjects):
        sub_folder = sub / str(sub_num)
        sub_folder.mkdir(parents=True, exist_ok=True)

        for session in DICOM_SESSIONS:
            sub_session_folder = sub_session / str(sub_num) / session
            sub_session_folder.mkdir(parents=True, exist_ok=True)

            sub_session_folder_flat = sub_session_flat / Path(str(sub_num) + "_" + session)
            sub_session_folder_flat.mkdir(parents=True, exist_ok=True)

            session_sub_folder = session_sub / session / str(sub_num)
            session_sub_folder.mkdir(parents=True, exist_ok=True)

            session_sub_folder_flat = session_sub_flat / Path(session + "_" + str(sub_num))
            session_sub_folder_flat.mkdir(parents=True, exist_ok=True)

def populate_with_fmriprep(project_dir: Path, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
    sample_fmriprep_dataset_description, num_subjects=DEFAULT_NUM_FMRIPREP_SUBJECTS, legacy = False):
    tasks = ["rest", "gonogo", "nback_run-1", "nback_run-2"]

    image_space = "space-MNI152NLin2009cAsym"
    bold_suffix = "desc-preproc_bold.nii.gz"
    mask_suffix = "desc-brain_mask.nii.gz"
    sidecar_suffix = "desc-preproc_bold.json"
    confounds_suffix = "desc-confounds_timeseries.tsv"
    melodic_mixing_suffix = "desc-MELODIC_mixing.tsv"
    aroma_noise_ics_suffix = "AROMAnoiseICs.csv"

    if(legacy):
        fmriprep_dir = project_dir / "data_fmriprep" / "fmriprep"
    else:
        fmriprep_dir = project_dir / "data_fmriprep"
    fmriprep_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(sample_fmriprep_dataset_description, fmriprep_dir)

    for sub_num in range(num_subjects):
        subject_folder = fmriprep_dir / f"sub-{sub_num}" / "func"
        subject_folder.mkdir(parents=True)
        
        for task in tasks:
            task_info = f"task-{task}"
            
            shutil.copy(sample_raw_image, subject_folder / f"sub-{sub_num}_{task_info}_{image_space}_{bold_suffix}")
            shutil.copy(sample_raw_image_mask, subject_folder / f"sub-{sub_num}_{task_info}_{image_space}_{mask_suffix}")

            shutil.copy(sample_confounds_timeseries, subject_folder / f"sub-{sub_num}_{task_info}_{confounds_suffix}")
            shutil.copy(sample_melodic_mixing, subject_folder / f"sub-{sub_num}_{task_info}_{melodic_mixing_suffix}")
            shutil.copy(sample_aroma_noise_ics, subject_folder / f"sub-{sub_num}_{task_info}_{aroma_noise_ics_suffix}")

            if task == "rest":
                tr = .6
            else:
                tr = .9
            sidecar_json = {"RepetitionTime": tr, "TaskName": task}
            with open(subject_folder / f"sub-{sub_num}_{task_info}_{image_space}_{sidecar_suffix}", "w") as sidecar_file:
                json.dump(sidecar_json, sidecar_file)

def populate_with_postproc2(project_dir: Path, sample_raw_image, sample_confounds_timeseries,
                            num_subjects=DEFAULT_NUM_FMRIPREP_SUBJECTS):
    tasks = ["rest", "gonogo", "nback_run-1", "nback_run-2"]

    image_space = "space-MNI152NLin2009cAsym"
    bold_suffix = "desc-postproc_bold.nii.gz"
    confounds_suffix = "desc-confounds_timeseries.tsv"

    postproc2_dir = project_dir / "data_postproc2" / "default"
    postproc2_dir.mkdir(parents=True, exist_ok=True)

    for sub_num in range(num_subjects):
        subject_folder = postproc2_dir / f"sub-{sub_num}" / "func"
        subject_folder.mkdir(parents=True)

        for task in tasks:
            task_info = f"task-{task}"

            shutil.copy(sample_raw_image, subject_folder / f"sub-{sub_num}_{task_info}_{image_space}_{bold_suffix}")
            shutil.copy(sample_confounds_timeseries, subject_folder / f"sub-{sub_num}_{task_info}_{confounds_suffix}")


def generate_random_nii(dims: tuple=DEFAULT_RANDOM_NII_DIMS, low: int=0, high: int=1000) -> nib.Nifti1Image:
    """Creates a simple nii image with the given dimensions.

    Args:
        dims (tuple): A 3d or 4d tuple representing dimensions of the nii.
        low (int): The floor generated voxel intensity.
        high (int): The ceiling generated voxel intensity.

    Returns:
        nib.Nifti1Image: A random nii image.
    """
    size = 1
    for x in dims:
        size *= x

    affine = np.diag([1 for x in dims])

    array_data = np.random.randint(low, high=high, size=size, dtype=np.int16).reshape(dims)
    image = nib.Nifti1Image(array_data, affine)

    return image

def generate_random_nii_mask(dims: tuple=DEFAULT_RANDOM_NII_DIMS) -> nib.Nifti1Image:
    mask_base = np.ones(dims, dtype=np.int16)
    
    # Zero the edges of our mask
    mask_base[0] = 0
    mask_base[-1] = 0
    for x in mask_base:
        x[0] = 0
        x[-1] = 0
        for y in x:
            y[0] = 0
            y[-1] = 0

    affine = np.diag([1 for x in dims])
    image = nib.Nifti1Image(mask_base, affine)

    return image

def old_GLMConfigParser_init(self, glm_config_file=None):
    """Monkeypatch function for running GLMConfigParser init according to <= v1.7.3"""
    import json
    from pkg_resources import resource_stream
    from clpipe.config_json_parser import config_json_parser

    if glm_config_file is None:
        with resource_stream(__name__, '/data/old_GLMConfig.json') as def_config:
            self.config = json.load(def_config)
    else:
        self.config = config_json_parser(glm_config_file)

def old_setup_glm(self, project_path):
    """Monkeypatch function for running glm setup according to <= v1.7.3"""
    import os
    
    glm_config = GLMConfigParser()

    glm_config.config['GLMSetupOptions']['ParentClpipeConfig'] = os.path.join(project_path, "clpipe_config.json")
    glm_config.config['GLMSetupOptions']['TargetDirectory'] = os.path.join(project_path, "data_fmriprep", "fmriprep")
    glm_config.config['GLMSetupOptions']['MaskFolderRoot'] = glm_config.config['GLMSetupOptions']['TargetDirectory']
    glm_config.config['GLMSetupOptions']['PreppedDataDirectory'] =  os.path.join(project_path, "data_GLMPrep")

    glm_config.config['Level1Setups'][0]['TargetDirectory'] = os.path.join(project_path, "data_GLMPrep")
    glm_config.config['Level1Setups'][0]['FSFDir'] = os.path.join(project_path, "l1_fsfs")
    glm_config.config['Level1Setups'][0]['EVDirectory'] = os.path.join(project_path, "data_onsets")
    glm_config.config['Level1Setups'][0]['ConfoundDirectory'] = os.path.join(project_path, "data_GLMPrep")
    glm_config.config['Level1Setups'][0]['OutputDir'] = os.path.join(project_path, "l1_feat_folders")

    glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_gfeat_folders")
    glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_fsfs")

    glm_config.config['GLMSetupOptions']['LogDirectory'] = os.path.join(project_path, "logs", "glm_setup_logs")

    glm_config.config_json_dump(project_path, "glm_config.json")