from pathlib import Path
import numpy as np
import nibabel as nib

DEFAULT_NUM_BIDS_SUBJECTS = 10
DEFAULT_NUM_DICOM_SUBJECTS = 5
DEFAULT_RANDOM_NII_DIMS = (12, 12, 12, 36)
DICOM_SESSIONS = ['2000', '2010', '2020']

def populate_with_BIDS(project_dir, num_subjects=DEFAULT_NUM_BIDS_SUBJECTS):
    """Populate the given project_dir with BIDS data.
    
    project_dir must be existing clpipe project.
    """

    for sub_num in range(num_subjects):
            subject_folder = project_dir / "data_BIDS" / f"sub-{sub_num}"
            subject_folder.mkdir()

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