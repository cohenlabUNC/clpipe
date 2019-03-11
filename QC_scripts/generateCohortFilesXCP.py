import sys, os
import numpy as np
import pandas as pd
import subprocess
import datetime

def get_subs(group):
    if group =='AllGoodSubs_NoMatch':
        sublist = ['1504', '1412', '1736', '1462', '1611', '1676', '1256', '1472', '1507', '1930', '1063', '1118', '1896', '1229', '1489', '1775', '1214', '1633', '1700', '1857', '1386', '1707', '1978', '1460', '1944', '1304', '1950', '1127', '1515', '1654', '1681', '1781', '1875', '1455', '1297', '1365', '1137', '1769', '1859', '2029', '1039', '1458', '1865', '1890', '1917', '1144', '1325', '1437', '1677', '1383', '1129', '1479', '1956', '1805', '1096', '1264', '1308', '1705', '1309', '1985', '2000', '1338', '1796', '1969', '1342', '1406', '1199', '1747', '1360', '1505', '1807', '1202', '1374', '1697', '1331', '1433', '1708', '1007', '1502', '1551', '1348', '1532', '1839', '1867', '1683', '1793', '1494', '1638', '1797', '0971', '1056', '1301', '1879', '0987', '1252', '1501', '1653', '1846', '1168', '1358', '1899', '1245', '1380', '1749', '1984', '1721', '1618', '0947', '0995', '1046', '1101', '1204', '1399', '1434', '1671', '1935', '1141', '1246', '1299', '1346', '1353', '1510', '1945', '1119', '1134', '1164', '1171', '1251', '1378', '1384', '1499', '1634', '1662', '1673', '1693', '1731', '1823', '1827', '1918', '1065', '1836', '1276', '1965', '1227', '0943', '1521', '1464', '1073', '1414', '1684', '1177', '1388', '1506', '1941']
    elif group == 'Matched_GoodSubs':
        sublist = ['1353', '1700', '1494', '1633', '1807', '1653', '1499', '2000', '1879', '1705', '1899', '1634', '1677', '1338', '1654', '1551', '1437', '1299', '1839', '1297', '1399', '1325', '1611', '1827', '1434', '1708', '1875', '1504', '1412', '1867', '1638', '1510', '1896', '1857', '1697', '1681', '1676', '2029', '1127', '1433', '1769', '1380', '1374', '1797', '1046', '1985', '1693', '1707', '1462', '1264', '1204', '1096', '1007', '1342', '1331', '1472', '1673', '1823', '1414', '1965', '1177', '1731', '1721', '1168', '1684', '1360']
    elif group == 'AllPossible_Matched':
        sublist = ['1846', '1353', '1700', '1494', '1633', '1807', '1489', '1653', '1365', '1499', '2000', '1301', '1309', '1879', '1705', '1899', '1634', '1677', '1141', '1338', '1378', '1654', '1551', '1348', '1437', '1865', '1479', '1978', '1299', '1839', '1297', '1399', '1935', '1325', '1611', '1827', '1434', '1708', '1950', '1875', '1504', '1412', '1867', '1944', '1507', '1638', '1510', '1896', '1857', '1697', '1681', '1676', '1930', '1956', '1252', '1532', '2029', '1127', '1433', '1793', '1769', '1380', '1917', '1797', '1039', '1985', '1859', '1707', '1462', '1458', '1264', '1781', '1204', '1096', '1007', '1342', '1331', '1245', '1472', '1137', '1673', '1046', '1823', '1168', '1414', '1965', '1177', '1731', '1721', '1168', '1684', '1360']
    elif group == 'Matched_GoodSubs_ADHD':
        sublist = ['1353', '1700', '1494', '1633', '1807', '1653', '1499', '2000', '1437', '1299', '1839', '1297', '1399', '1325', '1611', '1827', '1434', '1708', '1875', '1504', '1412', '1867', '1638', '1510', '1896', '1857', '1697', '1681', '1676', '1414', '1965', '1177', '1684']
    elif group == 'Matched_GoodSubs_TD':
        sublist = ['1879', '1705', '1899', '1634', '1677', '1338', '1654', '1551', '2029', '1127', '1433', '1769', '1380', '1374', '1797', '1046', '1985', '1693', '1707', '1462', '1264', '1204', '1096', '1007', '1342', '1331', '1472', '1673', '1823', '1731', '1721', '1168', '1360']
    else:
        print('SUBJECT LIST NOT DEFINED FOR THIS GROUP')

    return sublist

def get_meanFD(confoundname):
    """ This function loads confound file and outputs FD values as a vector, then averages them to return mean FD to put in the document """

    confounds=np.loadtxt(confoundname,dtype='bytes') 
    col=np.where(confounds[0,:]=='FramewiseDisplacement'.encode('utf-8'))
    if len(col)==1: # If exists at all
        if len(col[0])==1: # Need to get out of array
            FDcol=col[0][0] # Need a second index to get out of array 
            FDvalues_str=confounds[2:confounds.shape[0],FDcol] # Remove header row and first data row (N/A since FD requires CHANGE)
            #FDvalues=map(float,FDvalues_str) # Convert FD to float, but only works with rgular strings
            FDvalues=[float(i) for i in FDvalues_str] # Needed if a string of bytes
        elif len(col[0])==0:
            sys.exit('Confound file has no column for FramewiseDisplacement. CHECK.')
        else:
            sys.exit('Confound file has mutliple columns for FramewiseDisplacement. CHECK.')
    else:
        sys.exit('Unexpected output for confound file. CHECK.')

    meanFD = np.mean(FDvalues)
    
    return meanFD

def values_to_tsv(count,outfile,subnum,meanFD,adjmat_file):
 # Header row ONLY if first time opening                                     
    if count==0:
        f = open(outfile, "w") # First time open, clear anything that may be there already
        # Write header row
        f.write('id0\tmotion\tconnectivity\n')
        f.close()

    # Reopen and output all values for subsequent rows, appending each time
    f = open(outfile,"a") # Append subject data to header row
    # Write data rows   
    f.write('%s\t%0.4f\t%s\n' %(subnum,meanFD,adjmat_file))
    f.close()

def tsv_to_csv(tsv_cohort_file,csv_cohort_file):
    """ Since writing to a csv file is suprisingly difficult in python, and I wanted to maintain the current system, I'm writing a tsv file and then converting it to a csv file with pandas. Should ultimately write directly to a csv """

    csv_table=pd.read_table(tsv_cohort_file,sep='\t')
    csv_table.to_csv(csv_cohort_file,index=False)

    

def main(argv = sys.argv):

    # Variables that may have to change
    procstreams = ['Schaefer100_scrubNANrm','Schaefer200_scrubNANrm','Schaefer300_scrubNANrm','Schaefer400_scrubNANrm']
    
    subgroups = ['AllGoodSubs_NoMatch','Matched_GoodSubs']

    homedir = '/proj/cohenlab/projects/'
    project = 'kki_adhd'
    scriptdir = os.path.join(homedir,project,'scripts','')
    bidsdir = os.path.join(homedir,project,'data_BIDS','')
    bids_derivdir = os.path.join(bidsdir,'derivatives','')
    fmriprepdir = os.path.join(bids_derivdir,'fmriprep','')
    fmriprep_outdir = os.path.join('ses-1','func','')
    proc_comparison_dir = os.path.join(bids_derivdir,'processing_comparisons')
    tasks = ['rest']
    confoundbase = 'confounds.tsv'
    adj_matrix_dirname = 'adjMats_notSquare'
    
    for proc in procstreams:
        for group in subgroups:
            sublist = get_subs(group)

             # Create output file name incorporating user input
            cohort_outfile = os.path.join(bids_derivdir,'cohort_files','cohort_%s_%s_%s.tsv' %(proc,group,datetime.datetime.now().strftime('%m-%d-%Y')))

            count = 0 # Define count so only output header if count = 0
            for subnum in sublist:

                print('%s' %(subnum))

                indiv_subdir = os.path.join(fmriprepdir,'sub-%s' %(subnum),fmriprep_outdir,'')

                for task in tasks:
                    if task=='rest':
                        runs = [1]
                    else:
                        sys.exit('Runs not determined for this task!!!')

                for runnum in runs:
                
                    confoundname = os.path.join(indiv_subdir,'sub-%s_ses-1_task-%s_run-%d_bold_%s' %(subnum,task,runnum,confoundbase))

                    meanFD = get_meanFD(confoundname) # Get meanFD value

                    adjmat_filename = '%s_adjmat.csv' %(subnum)
                    #adjmat_file = os.path.join(proc_comparison_dir,proc,adj_matrix_dirname,adjmat_filename)
                    adjmat_file = os.path.join(bids_derivdir,'timeseries',proc,adj_matrix_dirname,adjmat_filename)

                    values_to_tsv(count,cohort_outfile,subnum,meanFD,adjmat_file)

                    count = count+1

                tsv_cohort_file = os.path.join(bids_derivdir,'cohort_files','cohort_%s_%s_%s.tsv' %(proc,group,datetime.datetime.now().strftime('%m-%d-%Y')))
                csv_cohort_file = os.path.join(bids_derivdir,'cohort_files','cohort_%s_%s_%s.csv' %(proc,group,datetime.datetime.now().strftime('%m-%d-%Y')))

                tsv_to_csv(tsv_cohort_file,csv_cohort_file)
    

### MAIN SCRIPT ###

if __name__ == '__main__':
    main()


"""
                    # Print output to datafile
                    values_to_txt(count,motstats_outfile,subnum,thr,task,runnum,meanFD,medFD,numOutl,pctScrub)

### What I need to do now is:
generate the connectome (and figure out what it is). So the adjacency matrix is the same length as the total sum of the positive and negative values in the upper tri of the correlation matrix (34716). But I'm not really sure how to get this. So I think what I need to do is just run the script/create a script to run exactly what they have an obtain an adjacency matrix for each subject, just to be sure that it's exactly what the function needs and will work.
set up a function to return the file path and name of the connectome
set up a function to write the subnum, FD, and connectome file path to a csv. This will be just like the one in the checkCorrelations script I think, except using comma separators, rather than tabs
###

### Now run the following to convert the final tsv file into a csv file

bids_derivdir = os.path.join(bidsdir,'derivatives','')

tsv_cohort_file = os.path.join(bids_derivdir,'cohort_files','cohort_%s_%s.tsv' %(procstream,datetime.datetime.now().strftime('%m-%d-%Y')))
csv_cohort_file = os.path.join(bids_derivdir,'cohort_files','cohort_%s_%s.csv' %(procstream,datetime.datetime.now().strftime('%m-%d-%Y')))

tsv_to_csv(tsv_cohort_file,csv_cohort_file)
"""        

"""
Need to add the outfile into the values_to_tsv loop! (make sure the motion script does this by pulling it into the function (e.g. values_to_tsv(outfile,jfakjfa)
"""
