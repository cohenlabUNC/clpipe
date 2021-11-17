import nibabel as nb
import numpy as np
import os

from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename
import nipype.pipeline.engine as pe
from nipype.interfaces.utility import IdentityInterface
from nipype.interfaces.base.traits_extension import isdefined

from clpipe.postprocutils.utils import apply_filter, calc_filter

def build_input_node():
    return pe.Node(IdentityInterface(fields=['in_file', 'out_file'], mandatory_inputs=False), name="inputnode")

def build_output_node():
    return pe.Node(IdentityInterface(fields=['out_file'], mandatory_inputs=True), name="outputnode")

class ButterworthFilterInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc='Image to be normalized', mandatory=False)
    hp = traits.Float(desc='High-pass cutoff value. Set to -1 to disable',
                             mandatory=True)
    lp = traits.Float(desc='Low-pass cutoff value. Set to -1 to disable',
                             mandatory=True)
    tr = traits.Float(desc='Repetition time.', mandatory=True)
    order = traits.Float(desc='Order of the filter', mandatory=True)
    out_file = File(mandatory=False)


class ButterworthFilterOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Filtered image")

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
        
        if not isdefined(self.inputs.out_file):
            _, base, _ = split_filename(fname)
            self.new_file = base + '_filtered.nii'
        else:
            self.new_file = self.inputs.out_file

        nb.save(new_img, self.new_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = os.path.abspath(self.new_file)

        return outputs