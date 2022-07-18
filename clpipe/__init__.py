from clpipe import batch_manager
from clpipe import config_json_parser
from clpipe import fmri_preprocess
from clpipe.postprocutils import utils
from clpipe.postprocutils import spec_interpolate

import logging
logging.basicConfig(level=logging.WARNING, 
    format='%(message)s')

logger = logging.getLogger("clpipe")
logger.setLevel(logging.INFO)
logger.handlers = []