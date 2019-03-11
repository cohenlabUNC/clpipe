# Usage: python3 runQCFC.py

import os, sys

date = '11-16-2018' #date on generated cohort files you want to use
subgroups = ['AllGoodSubs_NoMatch','Matched_GoodSubs']

procstreams = ['Schaefer100_noscrub','Schaefer200_noscrub','Schaefer300_noscrub','Schaefer400_noscrub']

homedir = '/proj/cohenlab/projects/'
project = 'kki_adhd'
scriptdir = os.path.join(homedir,project,'scripts','')
bidsdir = os.path.join(homedir,project,'data_BIDS','')
bids_derivdir = os.path.join(bidsdir,'derivatives','')
cohort_file_dir = os.path.join(bids_derivdir,'cohort_files','')
corrmat_output_dir = os.path.join(bids_derivdir,'processing_comparisons','qcfc_corrmats','')
xcp_dir = '/proj/cohenlab/projects/xcpEngine/utils/'


for proc in procstreams:
    for group in subgroups:
        command = 'Rscript %s/getQCFCmats.R -c %s/cohort_%s_%s_%s.csv -o %s/%s_%s' %(scriptdir,cohort_file_dir,proc,group,date,corrmat_output_dir,proc,group)

        print(command)
        os.system(command)
