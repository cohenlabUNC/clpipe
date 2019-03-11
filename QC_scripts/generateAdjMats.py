import os,string
import sys
import pandas as pd
import numpy as np

### FUNCTIONS ###

def get_sublist(subdir):
    """ Lists all directories in a main directories of all subjects to create a subject list. Note that this is BIDS format specific (assumes all subject directories begin "sub-xxx". Could be modified.
 Return: subject list """
    sublist = []
    for subnum in np.sort(os.listdir(subdir)):
        if subnum[0:3]=='sub': ###Make sure it's a subject number, this is what's BIDS format specific
            BOLD_directory = os.path.join(subdir,subnum,'ses-1','func')
            if os.path.isdir(BOLD_directory): ###Pass only subject DIRECTORIES, not html summaries which also appear in directory
                os.chdir(BOLD_directory)
                for file in os.listdir(BOLD_directory):
                    if 'confounds' in file: ###Had to add this in since the script was failing because sub list included some who failed fmriprep
                        subparts=subnum.split('-')
                        sublist.append(subparts[1])
                    else:
                        pass
        os.chdir(subdir)

    return sublist

def get_adjmat(xcp_path,indiv_ts_file):
                        
    command = 'Rscript %s/ts2adjmat_edits.R --ts %s' %(xcp_path,indiv_ts_file) #Had to edit the script to '%s/ts2adjmat_edits_forcsv.R' to read in csv files from the short TS

    print(command)
    os.system(command)

### INPUTS ###

def main(argv = sys.argv):

    processing_streams = ['Schaefer100_scrubNANrm','Schaefer200_scrubNANrm','Schaefer300_scrubNANrm','Schaefer400_scrubNANrm']
    adjmat_type = 'adjMats_notSquare'
    
    basedir = '/proj/cohenlab/projects/'
    project = 'kki_adhd'
    deriv_dir = os.path.join(basedir,project,'data_BIDS/derivatives/')
    subdir = os.path.join(deriv_dir,'fmriprep','')
    proc_dir = os.path.join(deriv_dir,'processing_comparisons')
    xcp_path = os.path.join(basedir,project,'xcpEngine/utils/')
    
    for proc in processing_streams:

        ### Get sublist ###
        sublist = get_sublist(subdir)

        ts_dir = os.path.join(deriv_dir,'timeseries',proc,'')
        output_dir = os.path.join(ts_dir,adjmat_type,'')

        ### Change into output dir so that the files can be stored there without having to load up directories and paths within the R script. Make sure it exists, create it if not, and then move into ###
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        else:
            pass

        os.chdir(output_dir)

        ### Load in each subject's timeseries, generate, and store the adjacency matrix ###

        for subnum in sublist:
            print(subnum)
            atlas = proc.split('_')[0]
            scrub_type = proc.split('_')[1]
            ts_suffix = '%s_smooth_%s.tsv' %(scrub_type,atlas)
            indiv_ts_filename = 'sub-%s_ses-1_task-rest_run-1_bold_%s' %(subnum,ts_suffix) 
            indiv_ts_file = os.path.join(ts_dir,indiv_ts_filename)

            get_adjmat(xcp_path,indiv_ts_file)



### MAIN SCRIPT ###

if __name__ == '__main__':
    main()

        

        
