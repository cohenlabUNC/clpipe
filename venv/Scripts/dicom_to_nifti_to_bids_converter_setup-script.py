#!C:\Users\teagu\Documents\GitHub\clpipe\venv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'clpipe==0.1','console_scripts','dicom_to_nifti_to_bids_converter_setup'
__requires__ = 'clpipe==0.1'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('clpipe==0.1', 'console_scripts', 'dicom_to_nifti_to_bids_converter_setup')()
    )
