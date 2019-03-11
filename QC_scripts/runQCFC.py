# Usage: python3 runQCFC.py

import os, sys

date = '11-16-2018' #date on generated cohort files you want to use
subgroups = ['AllGoodSubs_NoMatch','Matched_GoodSubs']

procstreams = ['Schaefer100_scrubNANrm','Schaefer200_scrubNANrm','Schaefer300_scrubNANrm','Schaefer400_scrubNANrm']

homedir = '/proj/cohenlab/projects/'
project = 'kki_adhd'
scriptdir = os.path.join(homedir,project,'scripts','')
bidsdir = os.path.join(homedir,project,'data_BIDS','')
bids_derivdir = os.path.join(bidsdir,'derivatives','')
cohort_file_dir = os.path.join(bids_derivdir,'cohort_files','')
qcfc_output_dir = os.path.join(bids_derivdir,'processing_comparisons','qcfc_output','')
xcp_dir = os.path.join(basedir,'xcpEngine','utils','')


for proc in procstreams:
    for group in subgroups:
        command = 'Rscript %s/qcfc.R -c %s/cohort_%s_%s_%s.csv -o %s/%s_%s' %(xcp_dir,cohort_file_dir,proc,group,date,qcfc_output_dir,proc,group)

        print(command)
        os.system(command)


