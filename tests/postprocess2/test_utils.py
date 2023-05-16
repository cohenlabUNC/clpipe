from clpipe.postprocutils.utils import nii_to_matrix, matrix_to_nii, scrub_image
import nibabel as nib
import numpy as np


def test_nii_to_matrix(sample_raw_image):
    """Test that a nii file is transformed into a 2D array"""

    test_df, orig_shape, affine = nii_to_matrix(sample_raw_image)

    assert len(test_df.shape) == 2


def test_matrix_to_nii(sample_raw_image):
    """Test to make sure image properties are conserved when transforming
    nii file to df and back.
    """
    # Gather properties from the original image
    nii_img = nib.load(sample_raw_image)
    orig_shape = nii_img.shape
    orig_affine = nii_img.affine

    test_df, orig_shape, affine = nii_to_matrix(sample_raw_image, save_df=True)
    nii = matrix_to_nii(test_df, orig_shape, affine)

    assert nii.shape == orig_shape
    assert np.array_equal(nii.affine, orig_affine)


def test_scrub_image_no_insert_na(
    artifact_dir, sample_raw_image, plot_img, request, helpers
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    scrubbed_path = test_path / "scrubbed.nii.gz"

    scrub_vector = [0, 1, 0, 0, 0, 0, 1, 0, 0, 0]

    scrub_image(
        sample_raw_image, scrub_vector, insert_na=False, export_path=scrubbed_path
    )

    helpers.plot_timeseries(scrubbed_path, sample_raw_image)

    if plot_img:
        helpers.plot_4D_img_slice(scrubbed_path, "scrubbed.png")
