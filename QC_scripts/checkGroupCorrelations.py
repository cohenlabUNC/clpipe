# Usage: python3 checkGroupCorrelations.py

"""
 Created to run specifically to evaluate the GROUP-level mean positive and negative functional correlations, as well as the range. For now imports specific subject lists from pre-determined groups. Will one day be more generalized. 
"""

import sys, os
import numpy as np
import pandas as pd

def get_subs(group):
    if group =='AllGoodSubs_NoMatch':
        sublist = ['1504', '1412', '1736', '1462', '1611', '1676', '1256', '1472', '1507', '1930', '1063', '1118', '1896', '1229', '1489', '1775', '1214', '1633', '1700', '1857', '1386', '1707', '1978', '1460', '1944', '1304', '1950', '1127', '1515', '1654', '1681', '1781', '1875', '1455', '1297', '1365', '1137', '1769', '1859', '2029', '1039', '1458', '1865', '1890', '1917', '1144', '1325', '1437', '1677', '1383', '1129', '1479', '1956', '1805', '1096', '1264', '1308', '1705', '1309', '1985', '2000', '1338', '1796', '1969', '1342', '1406', '1199', '1747', '1360', '1505', '1807', '1202', '1374', '1697', '1331', '1433', '1708', '1007', '1502', '1551', '1348', '1532', '1839', '1867', '1683', '1793', '1494', '1638', '1797', '0971', '1056', '1301', '1879', '0987', '1252', '1501', '1653', '1846', '1168', '1358', '1899', '1245', '1380', '1749', '1984', '1721', '1618', '0947', '0995', '1046', '1101', '1204', '1399', '1434', '1671', '1935', '1141', '1246', '1299', '1346', '1353', '1510', '1945', '1119', '1134', '1164', '1171', '1251', '1378', '1384', '1499', '1634', '1662', '1673', '1693', '1731', '1823', '1827', '1918', '1065', '1836', '1276', '1965', '1227', '0943', '1521', '1464', '1073', '1414', '1684', '1177', '1388', '1506', '1941']
    elif group == 'MotionMatched':
        sublist = ['1353', '1700', '1494', '1633', '1807', '1653', '1499', '2000', '1879', '1705', '1775', '1634', '1677', '1338', '1654', '1551', '1437', '1299', '1839', '1297', '1399', '1325', '1611', '1827', '1434', '1708', '1875', '1504', '1412', '1867', '1638', '1510', '1896', '1857', '1697', '1681', '1676', '2029', '1127', '1433', '1769', '1380', '1374', '1797', '1256', '1985', '1460', '1707', '1462', '1264', '1406', '1096', '1007', '1342', '1331', '1472', '1890', '1458', '1414', '1965', '1177', '1501', '1721', '1168', '1684', '1360']
    elif group == 'Matched_GoodSubs':
        sublist = ['1353', '1700', '1494', '1633', '1807', '1653', '1499', '2000', '1879', '1705', '1899', '1634', '1677', '1338', '1654', '1551', '1437', '1299', '1839', '1297', '1399', '1325', '1611', '1827', '1434', '1708', '1875', '1504', '1412', '1867', '1638', '1510', '1896', '1857', '1697', '1681', '1676', '2029', '1127', '1433', '1769', '1380', '1374', '1797', '1046', '1985', '1693', '1707', '1462', '1264', '1204', '1096', '1007', '1342', '1331', '1472', '1673', '1823', '1414', '1965', '1177', '1731', '1721', '1168', '1684', '1360']
    elif group == 'AllPossible_Matched':
        sublist = ['1846', '1353', '1700', '1494', '1633', '1807', '1489', '1653', '1365', '1499', '2000', '1301', '1309', '1879', '1705', '1899', '1634', '1677', '1141', '1338', '1378', '1654', '1551', '1348', '1437', '1865', '1479', '1978', '1299', '1839', '1297', '1399', '1935', '1325', '1611', '1827', '1434', '1708', '1950', '1875', '1504', '1412', '1867', '1944', '1507', '1638', '1510', '1896', '1857', '1697', '1681', '1676', '1930', '1956', '1252', '1532', '2029', '1127', '1433', '1793', '1769', '1380', '1917', '1797', '1039', '1985', '1859', '1707', '1462', '1458', '1264', '1781', '1204', '1096', '1007', '1342', '1331', '1245', '1472', '1137', '1673', '1046', '1823', '1168', '1414', '1965', '1177', '1731', '1721', '1168', '1684', '1360']
    else:
        print('SUBJECT LIST NOT DEFINED FOR THIS GROUP')

    return sublist

def remove_scrubbed(sub_ts):

    tsdata = np.loadtxt(sub_ts)
    #tsdata = pd.read_csv(sub_ts) #Had to add this in to read in the csv files created by the short TS
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
    if neg_vals.size == 0:
        neg_mean = 0
    else:
        neg_mean = np.mean(neg_vals)

    pos_max = np.max(pos_vals)
    if neg_vals.size == 0:
        neg_min = 0
    else:
        neg_min = np.min(neg_vals)

    return pos_mean, neg_mean, pos_max, neg_min

def get_group_means(group_average):

    group_array = np.asarray(group_average)
    group_means = np.mean(group_array,axis = 0)

    group_pos_mean = group_means[0]
    group_neg_mean = group_means[1]
    group_max = group_means[2]
    group_min = group_means[3]

    return group_pos_mean, group_neg_mean, group_max, group_min

def values_to_txt(outfile,group_pos_mean,group_neg_mean,group_max,group_min):
    f = open(outfile, "w") # First time open, clear anything that may be there already
    # Write header row
    f.write('Pos_Mean\tNeg_Mean\tMax\tMin\n')
    f.write('%0.4f\t%0.4f\t%0.4f\t%0.4f\n' %(group_pos_mean,group_neg_mean,group_max,group_min))

    f.close()

def main(argv = sys.argv):

    #procstreams = ['MquadNogsrAll']
    procstreams = ['Schaefer100_noscrub','Schaefer200_noscrub','Schaefer300_noscrub','Schaefer400_noscrub']

    subgroups = ['AllGoodSubs_NoMatch','Matched_GoodSubs']
    #subgroups = ['AllGoodSubs_NoMatch_ADHD','AllGoodSubs_NoMatch_TD','AllPossibleMatched_wQuestionableADHD_ADHD','AllPossibleMatched_wQuestionableADHD_TD','Matched_GoodSubs_ADHD','Matched_GoodSubs_TD','MotionMatched_ADHD','MotionMatched_TD']
    
    homedir = '/proj/cohenlab/projects/'
    project = 'kki_adhd'
    scriptdir = os.path.join(homedir,project,'scripts','')
    bidsdir = os.path.join(homedir,project,'data_BIDS','')
    deriv_dir = os.path.join(bidsdir,'derivatives')

    proc_dir = '/proj/cohenlab/projects/kki_adhd/data_BIDS/derivatives/processing_comparisons/'
    

    for proc in procstreams:
        for group in subgroups:
            sublist = get_subs(group)
            
            #Define in the processing specific ts dir to load in individual ts'
            #ts_dir = os.path.join(proc_dir,proc,'timeseries','')
            ts_dir = os.path.join(deriv_dir,'timeseries',proc,'')
            
            #Define the group and processing specific text outfile where results will be written and where it is stored
            outfile_name = 'group_correlation_vals_%s_%s.txt' %(proc,group)
            outfile = os.path.join(proc_dir,'group_corr_vals','',outfile_name)
             
            #Print outfile name for troubleshooting
            print(outfile_name)

            #Index an empty matrix to append subject values to, so that group level averages can be created
            group_average = []

            for sub in sublist:
                #indiv_ts_filename = 'sub-%s_ses-1_task-rest_run-1_bold_%s_smooth_Power.tsv' %(sub,proc)
                atlas = proc.split('_')[0]
                scrub_type = proc.split('_')[1]
                ts_suffix = '%s_smooth_%s_17net.tsv' %(scrub_type,atlas)
                indiv_ts_filename = 'sub-%s_ses-1_task-rest_run-1_bold_%s' %(sub,ts_suffix) #csv NOT tsv for the short TS ones

                #Load individual ts file
                indiv_ts_file = os.path.join(ts_dir,indiv_ts_filename)

                #Remove scrubbed timepoints (if any) from file
                sub_ts_noscrub = remove_scrubbed(indiv_ts_file)

                #Get individual correlation values
                pos_mean,neg_mean,pos_max,neg_min = get_correlations(sub_ts_noscrub)

                #Concatenate individual values into a single row
                sub_values = np.array([pos_mean,neg_mean,pos_max,neg_min])

                #Append individual values to group matrix
                group_average.append(sub_values)

            group_pos_mean,group_neg_mean,group_max,group_min = get_group_means(group_average)
            values_to_txt(outfile,group_pos_mean,group_neg_mean,group_max,group_min)

### MAIN SCRIPT ###

if __name__ == '__main__':
    main()

            
