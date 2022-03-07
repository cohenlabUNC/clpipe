import os
from pathlib import Path
import getpass
import pkg_resources

CLPIPE_R_LIBS_PATH = Path("/nas/longleaf/home/") / Path(getpass.getuser()) / Path(".local/lib/clpipe_R")

def setup_clpipe_R_lib():
    """
    Sets up an R library folder for R dependencies
    """
    os.environ['R_LIBS_USER'] = str(CLPIPE_R_LIBS_PATH)

    print(CLPIPE_R_LIBS_PATH)
    if not CLPIPE_R_LIBS_PATH.exists():
        CLPIPE_R_LIBS_PATH.mkdir(parents=True)
