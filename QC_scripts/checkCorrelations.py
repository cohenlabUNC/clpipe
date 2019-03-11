# Usage: python3 checkCorrelations.py 

# Used to check the positive and negative correlations of the ROI timeseries for each individual in a processing stream 


import os, sys
import numpy as np
import pandas as pd

### FUNCTIONS ###

def get_subs(subdir):
    """ This function lists all directories in a single main subject directory to get a subject list
        Return: subject list
    """

    sublist=[]
    for subnum in np.sort(os.listdir(subdir)):
        if subnum[0:3]=='sub': # Make sure it isn't a diff file with diff name
            subparts=subnum.split('-')
            subses = subparts[1]
            sub = subses.split('_')
            sublist.append(sub[0])
 
    return sublist

def remove_scrubbed(sub_ts):

    tsdata = np.loadtxt(sub_ts)
    df = pd.DataFrame(tsdata)
    ts_noscrub = df.dropna(axis = 0, how = 'all') #Remove only rows that are ALL nans
    
    #check to make sure the right number of rows are being removed
    nan_rows = df[df.isnull().T.all().T]
    if len(nan_rows) == len(df) - len(ts_noscrub):
        #print('***Scrubbed data points being removed for %s***' %(sub_ts))
        pass
    else:
        sys.exit('***ATTEMPTED TO REMOVED INCORRECT NUMBER OF SCRUBBED POINTS FOR %s. System exiting***' %(ts))

    sub_ts_noscrub = ts_noscrub.values #Return to np array so that corrmats can run
    
    return sub_ts_noscrub

def get_correlations(sub_ts_noscrub):
    """ This function gets the mean positive and mean negative correlations for the upper triangle only of each subject's ROI time series correlation matrix """

    #ROImat = np.loadtxt(sub_ts) #Commented out because get_scrubbed now loads the file
    ROImat = sub_ts_noscrub

    corrmat = np.corrcoef(ROImat, rowvar = False)

    upper = np.triu(corrmat, k = 1)

    pos_vals = upper[upper > 0]
    neg_vals = upper[upper < 0]

    pos_mean = np.mean(pos_vals)
    neg_mean = np.mean(neg_vals)

    return pos_mean, neg_mean

def values_to_txt(count,outfile,subnum,processing_stream,pos_mean,neg_mean):
    """ This function takes in metrics and outputs all relevant information to a textfile in matrix format. """

    # Header row ONLY if first time opening                                     
    if count==0:
        f = open(outfile, "w") # First time open, clear anything that may be there already
        # Write header row
        f.write('Sub\tProcessingStream\tMeanPosCorr\tMeanNegCorr\n')
        f.close()

    # Reopen and output all values for subsequent rows, appending each time
    f = open(outfile,"a") # Append subject data to header row
    # Write data rows   
    f.write('%s\t%s\t%0.4f\t%0.4f\n' %(subnum,processing_stream,pos_mean,neg_mean))
    f.close()



### INPUTS ###
def main(argv = sys.argv):

    # Variables that may have to change
    #processing_stream = 'noscrub_smooth_Power' #Name of directory within timeseries to get values for (for Kelly's, will also be name in tsv file)
    processing_stream = 'MtdNogsrScrub'
    #ts_file_suffix = 'noscrub_smooth_Power.tsv'
    ts_file_suffix = 'MtdNogsrScrub_smooth_Power.tsv'
    task = 'rest'
    ses = 1
    run = 1
    project = 'kki_adhd'

    homedir = '/proj/hng/cohenlab/projects/'   
    #tsdir = os.path.join(homedir,project,'data_BIDS','derivatives','timeseries','')
    tsdir = os.path.join(homedir,project,'data_BIDS','derivatives','processing_comparisons',processing_stream,'timeseries','')
    processingdir = os.path.join(tsdir,processing_stream,'')

    # Create output file name using processing stream, store in ts dir
    outfile = os.path.join(tsdir, 'subjectCorrelations_%s.txt' %(processing_stream))

    sublist = get_subs(tsdir)

    count = 0 # Define count so only output header if count = 0
    for subnum in sublist: 
        
        sub_ts = os.path.join(tsdir,'sub-%s_ses-%d_task-%s_run-%d_bold_%s' %(subnum,ses,task,run,ts_file_suffix)) 

        sub_ts_noscrub = remove_scrubbed(sub_ts)

        pos_mean,neg_mean = get_correlations(sub_ts_noscrub)

        values_to_txt(count,outfile,subnum,processing_stream,pos_mean,neg_mean)

        count = count + 1

### MAIN SCRIPT ###

if __name__ == '__main__':
    main()

        
    
