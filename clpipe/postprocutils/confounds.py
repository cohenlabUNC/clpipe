import os
import re
import logging
from pathlib import Path

import pandas as pd

from .utils import scrub_setup

def prepare_confounds(confound_file: Path, confounds_out: Path, postproccessing_config: dict):
   
    if not os.path.exists(confound_file):
        raise ValueError("Cannot find confound file: "+ confound_file)
    confounds = pd.read_table(confound_file, dtype="float", na_values="n/a")
    if len(postproccessing_config['Confounds']) > 0:
        cons_re = [re.compile(_regex_wildcard(co)) for co in postproccessing_config['Confounds']]
        target_cols = []
        for reg in cons_re:
            logging.debug(str([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None]))
            target_cols.extend([reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logging.debug("Confound Columns " + str(target_cols))
        confounds_mat = confounds[target_cols]
    if len(postproccessing_config['ConfoundsQuad']) > 0:
        cons_re = [re.compile(_regex_wildcard(co)) for co in postproccessing_config['ConfoundsQuad']]
        target_cols = []
        for reg in cons_re:
            target_cols.extend(
                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logging.debug("Quad Columns " + str(target_cols))
        confounds_quad_mat = confounds[target_cols]
        confounds_quad_mat.rename(columns =lambda x: x+"_quad", inplace = True)
        confounds_quad_mat = confounds_quad_mat**2
        confounds_mat = pd.concat([confounds_mat,confounds_quad_mat],axis=1, ignore_index=True)
        logging.debug(str(confounds_mat.shape))
    if len(postproccessing_config['ConfoundsDerive']) > 0:
        cons_re = [re.compile(_regex_wildcard(co)) for co in postproccessing_config['ConfoundsDerive']]
        target_cols = []
        for reg in cons_re:
            target_cols.extend(
                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logging.debug("Lagged Columns " + str(target_cols))
        confounds_lagged_mat = confounds[target_cols]
        confounds_lagged_mat.rename(columns =lambda x: x+"_lagged", inplace = True)
        confounds_lagged_mat = confounds_lagged_mat.diff()
        confounds_mat = pd.concat([confounds_mat,confounds_lagged_mat],axis=1, ignore_index=True)
        logging.debug(str(confounds_mat.shape))
        logging.debug(str(confounds_mat.head(5)))
    if len(postproccessing_config['ConfoundsQuadDerive']) > 0:
        cons_re = [re.compile(_regex_wildcard(co)) for co in postproccessing_config['ConfoundsQuadDerive']]
        target_cols = []
        for reg in cons_re:
            target_cols.extend(
                [reg.match(col).group() for col in confounds.columns if reg.match(col) is not None])
        logging.debug("Quadlagged Columns " + str(target_cols))
        confounds_qlagged_mat = confounds[target_cols]
        confounds_qlagged_mat = confounds_qlagged_mat.diff()
        confounds_qlagged_mat = confounds_qlagged_mat**2
        confounds_qlagged_mat.rename(columns =lambda x: x+"_qlagged", inplace = True)
        confounds_mat = pd.concat([confounds_mat,confounds_qlagged_mat],axis=1,ignore_index=True)
        logging.debug(str(confounds_mat.shape))
    if postproccessing_config['MotionOutliers']:
        logging.info("Computing Motion Outliers: ")
        logging.info("Motion Outlier Variable: "+ postproccessing_config['ScrubVar'])
        logging.info("Threshold: " + str(postproccessing_config['Threshold']))
        logging.info("Ahead: " + str(postproccessing_config['ScrubAhead']))
        logging.info("Behind: " + str(postproccessing_config['ScrubBehind']))
        logging.info("Contiguous: " + str(postproccessing_config['ScrubContiguous']))
        fdts = confounds[postproccessing_config['ScrubVar']]
        logging.debug(str(fdts))
        scrub_targets = scrub_setup(fdts, postproccessing_config['Threshold'], 
            postproccessing_config['ScrubBehind'], postproccessing_config['ScrubAhead'], postproccessing_config['ScrubContiguous'])
        logging.debug(str(scrub_targets))

    confounds_mat.fillna(0, inplace = True)
    confounds_mat.to_csv(confounds_out,sep='\t',index=False,header=False)
    logging.info("Outputting confound file to: " + str(confounds_out))


def _regex_wildcard(string):
    return '^'+re.sub("\*", ".*", string)+'$'