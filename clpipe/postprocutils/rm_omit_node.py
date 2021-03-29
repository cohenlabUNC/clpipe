from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

import nibabel as nb
import numpy as np
import os

class NANOmitInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc='File with NAN volumes to be removed', mandatory=True)
    


class NANOmitOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="File with NAN volumes removed.")


class NANOmit(BaseInterface):
    input_spec = NANOmitInputSpec
    output_spec = NANOmitOutputSpec

    def _run_interface(self, runtime):
        fname = self.inputs.in_file

        img = nb.load(fname)
        img_dat = img.get_fdata()

        nan_vec = np.sum(np.isnan(img_dat), axis=(0, 1, 2))
        it = np.nditer(nan_vec, flags=['f_index'])
        good_inds = [it.index for x in it if x == 0]
        img_trimdat = img_dat[:,:,:,good_inds]
        rm_file = nb.Nifti1Image(img_trimdat, img.affine, nb.Nifti1Header())
        _, base, _ = split_filename(fname)
        nb.save(rm_file, base + '_naomit.nii.gz')

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        fname = self.inputs.in_file
        _, base, _ = split_filename(fname)
        outputs["out_file"] = os.path.abspath(base + '_naomit.nii.gz')
        return outputs