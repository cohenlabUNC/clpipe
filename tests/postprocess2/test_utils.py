from clpipe.postprocutils.utils import nii_to_df, df_to_nii
import nibabel as nib


def test_nii_to_df(sample_raw_image):
    """Test that a nii file is transformed into a 2D array"""

    test_df, affine = nii_to_df(sample_raw_image)

    assert len(test_df.shape) == 2


def test_df_to_nii(sample_raw_image):
    """Test to make sure image properties are conserved when transforming
    nii file to df and back.
    """
    # Gather properties from the original image
    nii_img = nib.load(sample_raw_image)
    orig_shape = nii_img.shape
    orig_affine = nii_img.affine

    test_df, affine = nii_to_df(sample_raw_image, save_df=True)
    nii = df_to_nii(test_df, affine)

    assert nii.shape == orig_shape
    assert nii.affine == orig_affine
