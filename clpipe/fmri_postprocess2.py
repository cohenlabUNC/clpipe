import os
import nipype.pipeline.engine as pe

from .postprocutils.nodes import ButterworthFilter
from .postprocutils.workflows import build_10000_global_median_workflow, build_100_voxel_mean_workflow

class PostProcessSubjectJob():
    wf: pe.Workflow = None
    config: dict = None
    
    def __init__(self, config, subject_id: str, in_file: os.PathLike, out_file: os.PathLike):
        #self.ppconfig = config["PostProcessingOptions"]
        self.config=config
        self.subject_id=subject_id
        self.in_file=in_file
        self.out_file=out_file
        self.wf = pe.Workflow(name=PostProcessSubjectJob.__class__.__name__ + subject_id)
        self._compose_workflow()

    def _compose_workflow(self):
        voxel_mean_wf = build_100_voxel_mean_workflow(None, self.out_file, base_dir=self.wf.base_dir)
        butterworth_node = pe.Node(ButterworthFilter(in_file=self.in_file,
                                hp=.008,lp=-1,order=2,tr=2), name="butterworth_filter")

        self.wf.add_nodes([butterworth_node, voxel_mean_wf])

    def run(self):
        self.wf.run()