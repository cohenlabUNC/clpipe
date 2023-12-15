import nibabel as nb
import numpy as np
import os

from nipype.interfaces.base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    traits,
    File,
    TraitedSpec,
    CommandLine,
    CommandLineInputSpec,
)
from nipype.utils.filemanip import split_filename
import nipype.pipeline.engine as pe
from nipype.interfaces.utility import IdentityInterface
from nipype.interfaces.base.traits_extension import isdefined

from clpipe.postprocutils.utils import apply_filter, calc_filter


def build_input_node():
    return pe.Node(
        IdentityInterface(fields=["in_file", "out_file"], mandatory_inputs=False),
        name="inputnode",
    )


def build_output_node():
    return pe.Node(
        IdentityInterface(fields=["out_file"], mandatory_inputs=True), name="outputnode"
    )


class ButterworthFilterInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc="Image to be normalized", mandatory=False)
    hp = traits.Float(
        desc="High-pass cutoff value. Set to -1 to disable", mandatory=True
    )
    lp = traits.Float(
        desc="Low-pass cutoff value. Set to -1 to disable", mandatory=True
    )
    tr = traits.Float(desc="Repetition time.", mandatory=True)
    order = traits.Float(desc="Order of the filter", mandatory=True)
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

        filter = calc_filter(
            self.inputs.hp, self.inputs.lp, self.inputs.tr, self.inputs.order
        )
        filtered_data = apply_filter(filter, data)

        new_img = nb.Nifti1Image(filtered_data, img.affine, img.header)

        if not isdefined(self.inputs.out_file):
            _, base, _ = split_filename(fname)
            self.new_file = base + "_filtered.nii"
        else:
            self.new_file = self.inputs.out_file

        nb.save(new_img, self.new_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.new_file)

        return outputs


class RegressAromaRInputSpec(CommandLineInputSpec):
    script_file = File(
        exists=True,
        desc="Path to fsl_regfilt.R",
        mandatory=True,
        position=0,
        argstr="%s",
    )
    in_file = File(
        exists=True,
        desc="Image to be regressed",
        mandatory=True,
        position=1,
        argstr="%s",
    )
    mixing_file = File(
        exists=True,
        desc="The AROMA mixing file",
        mandatory=True,
        position=2,
        argstr="%s",
    )
    noise_file = File(
        exists=True,
        desc="The AROMA noise file",
        mandatory=True,
        position=3,
        argstr="%s",
    )
    n_threads = traits.Int(mandatory=True, position=4, argstr="%d")
    out_file = File(
        position=5,
        argstr="%s",
        name_source=["in_file"],
        name_template="%s_AROMAregressed.nii.gz",
    )


class RegressAromaROutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Regressed image")


class RegressAromaR(CommandLine):
    input_spec = RegressAromaRInputSpec
    output_spec = RegressAromaROutputSpec
    _cmd = "Rscript"

    def _filename_from_source(self, name, chain=None):
        retval = super()._filename_from_source(name, chain=chain)
        return os.path.abspath(retval)


class ImageSliceInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc="Image to be sliced", mandatory=False)
    trim_from_beginning = traits.Int(
        desc="Number of volumes to crop from beginning of timeseries.",
        mandatory=False,
        default_value=0,
    )
    trim_from_end = traits.Int(
        desc="Number of volumes to crop from end of timeseries.",
        mandatory=False,
        default_value=0,
    )
    out_file = File(mandatory=False)


class ImageSliceOutputSpec(TraitedSpec):
    out_file = File(exists=False, desc="Sliced image")


class ImageSlice(BaseInterface):
    input_spec = ImageSliceInputSpec
    output_spec = ImageSliceOutputSpec

    def _run_interface(self, runtime):
        fname = self.inputs.in_file
        img = nb.load(fname)

        # If user asked to drop first 5 volumes, we drop indexes 0:4, so we want to start on volume 5
        start_index = self.inputs.trim_from_beginning
        # Convert to a negative index to get last N volumes. If users wants to drop last 5 volumes, we'd drop indexes
        #   (last - 5):last
        #
        # Example:
        #   drop_from_end = 5
        #   last 7 indexes: 50, 51, 52, 53, 54, 55, 56, 57
        #   after drop: 50, 51, 52
        #   calculation of new end index: (5 * -1) = -5, 57 - 5 = 52
        end_index = self.inputs.trim_from_end * -1

        # Not using drop_from_beginning will work with a start_index of 0,
        #   however end_index as 0 will not work the same way, so it must be omitted from the slice
        #   if we aren't using drop_from_end
        if end_index == 0:
            cropped_img = img.slicer[..., start_index:]
        else:
            cropped_img = img.slicer[..., start_index:end_index]

        if not isdefined(self.inputs.out_file):
            _, base, _ = split_filename(fname)
            self.new_file = base + "_sliced.nii"
        else:
            self.new_file = self.inputs.out_file

        nb.save(cropped_img, self.new_file)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.new_file)

        return outputs


from nipype.interfaces.afni import Undump
from nipype.interfaces.afni.utils import UndumpInputSpec

class UndumpInputSpecFixed(UndumpInputSpec):
    in_file = File(
        desc="The input file(s) are ASCII files, with one voxel specification per line.",
        argstr="%s",
        position=-1,
        mandatory=True,
        exists=True,
        copyfile=False,
    )
    master_file = File(
        desc="The master dataset, whose geometry will determine the geometry of the output",
        argstr="-master %s",
        mandatory=True,
        exists=True,
        copyfile=False,
    )


class UndumpFixed(Undump):
    input_spec = UndumpInputSpecFixed