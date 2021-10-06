import nibabel as nb
import numpy as np
import os

from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec

from clpipe.postprocutils.utils import apply_filter, calc_filter


class ButterworthFilterInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc='Image to be normalized', mandatory=True)
    out_file = File(exists=False, desc='Output image path', mandatory=True)
    hp = traits.Float(desc='High-pass cutoff value. Set to -1 to disable',
                             mandatory=True)
    lp = traits.Float(desc='Low-pass cutoff value. Set to -1 to disable',
                             mandatory=True)
    tr = traits.Float(desc='Repetition time.', mandatory=True)
    order = traits.Float(desc='Order of the filter', mandatory=True)


class ButterworthFilterOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="Filtered image", mandatory=True)

class ButterworthFilter(BaseInterface):
    input_spec = ButterworthFilterInputSpec
    output_spec = ButterworthFilterOutputSpec

    def _run_interface(self, runtime):
        fname = self.inputs.in_file
        img = nb.load(fname)
        data = np.array(img.get_data())

        filter = calc_filter(self.inputs.hp, self.inputs.lp, self.inputs.tr, self.inputs.order)
        filtered_data = apply_filter(filter, data)

        new_img = nb.Nifti1Image(filtered_data, img.affine, img.header)
        nb.save(new_img, self.inputs.out_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs