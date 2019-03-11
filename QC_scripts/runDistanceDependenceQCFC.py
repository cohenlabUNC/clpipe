# Usage: python3 runQCFC.py

import os, sys

subgroups = ['AllGoodSubs_NoMatch','Matched_GoodSubs']

procstreams = ['Schaefer100_noscrub','Schaefer200_noscrub','Schaefer300_noscrub','Schaefer400_noscrub']

homedir = '/proj/cohenlab/projects/'
project = 'kki_adhd'
scriptdir = os.path.join(homedir,project,'scripts','')
bidsdir = os.path.join(homedir,project,'data_BIDS','')
bids_derivdir = os.path.join(bidsdir,'derivatives','')
cohort_file_dir = os.path.join(bids_derivdir,'cohort_files','')
qcfc_output_dir = os.path.join(bids_derivdir,'processing_comparisons','qcfc_output','')
corrmat_dir = os.path.join(bids_derivdir,'processing_comparisons','qcfc_corrmats','')
xcp_dir = '/proj/cohenlab/projects/xcpEngine/utils/'
atlas_dir = os.path.join(bids_derivdir,'mask_files','')


for proc in procstreams:
    for group in subgroups:

        atlas = proc.split('_')[0]
        atlas_num = atlas.split('r')[1]
        group_proc = '%s_%s' %(proc,group)
        outdir = os.path.join(bids_derivdir,'processing_comparisons','distancedepend_output',group_proc,'')
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        else:
            pass

        os.chdir(xcp_dir)

        command = './qcfcDistanceDependence -a %s/Schaefer_%sparcels_17networks.nii.gz -q %s/%s_%s.txt -o %s/qcfcDistanceDependenceVal.txt -d %s/distancematrix.txt -f %s/plot -i %s/temp' %(atlas_dir,atlas_num,corrmat_dir,proc,group,outdir,outdir,outdir,outdir)

        print(command)
        os.system(command)
