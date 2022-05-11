"""!
 @file dbscanTest.py
 @brief DBSCAN clustering tests
 @details Uses precomputed distance matrix loaded from disk 
 (created by cleanPlaintiffs.py with the -s option) to give a plot
 for different values of epsilon in the DBSCAN algorithm.

 @author Seth McNeill
 @date 2021 May 13
"""

import datetime  # used for start/end times
import argparse  # Improved command line functionality
import pdb       # Debugging
import csv       # CSV file operations
import pandas as pd  # Pandas data manipulation library
import numpy as np  # for data processing
import re  # regular expression library for processing
import math  # for isnan
from sklearn.feature_extraction.text import TfidfVectorizer  # TF-IDF tokanizer
import matplotlib.pyplot as plt  # plotting capability
from sklearn.cluster import KMeans  # K-Means Clustering
import distance  # library that has string comparison functions (docs say it is slow)
import jellyfish  # library for string comparisons that is supposed to be fast
import strsimpy  # string comparison library
import textdistance  # string comparison library
import abydos  # string comparison library
import copy  # for deep copying
from sklearn.cluster import DBSCAN  # DBSCAN clustering algorithm

def findBaseNames(fname, cutoff=0.9):
    """! Finds the base name of each cleaned name

    @param fname The filename of the pickle file created by plaintiffList
    @param cutoff The cutoff similarity between names to assume are the same
    """
    similarNames = pd.read_pickle(fname)
    distanceNames = 1 - similarNames

    # fitStartTime = datetime.datetime.now()
    # dbfit = DBSCAN(eps=0.1, min_samples=2, metric='precomputed').fit(distanceNames)
    # fitEndTime = datetime.datetime.now()
    # print(f'Fitting took {fitEndTime - fitStartTime}')
    # print(f'set of labels: {set(dbfit.labels_)}')
    # print(f'Group 0 contains: {distanceNames.index[dbfit.labels_ == 0]}')

    # scan through different eps values recording the numbers of core samples
    # and record the names at each step to show which names were added each time
    fitStartTime = datetime.datetime.now()
    fits = []
    min_eps = 0.01
    max_eps = 0.24
    eps_step = 0.01
    print("Testing different epsilon (eps) values for DBSCAN.")
    print(f"testing from {min_eps} to {max_eps} stepping {eps_step}")
    epsList = np.arange(min_eps, max_eps, eps_step)
    curveData = np.zeros([len(epsList),2])
    ii = 0
    for eps in epsList:
        print(f"Fitting {eps}:")
        dbfit = DBSCAN(eps=eps, min_samples=2, metric='precomputed').fit(distanceNames)
        fits.append(dbfit)
        curveData[ii,0] = eps
        curveData[ii,1] = dbfit.components_.shape[0]
        ii += 1
    fitEndTime = datetime.datetime.now()
    print(f'Fitting took {fitEndTime - fitStartTime}')
    fig = plt.figure(figsize=(9,6))
    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)
    plt.plot(curveData[:,0], curveData[:,1], 'bo--')
    plt.title('Clustered Name Count', fontsize=22)
    plt.ylabel('Number of Names that were Clustered', fontsize=16)
    plt.xlabel('Allowed Neighbor Distance (eps)', fontsize=16)
    plt.grid(True)
    plt.savefig(f'{fitEndTime:%Y%m%d%H%M%S}-CoreCount.png', bbox_inches='tight', pad_inches=0.1)
    plt.show()

# the following code collects the clusters of names to look at
    # Need list of names for each cluster to look over
    # matchFit = 9  # the number of the fit to use for subsquent processing
    # clusterSet = set(fits[matchFit].labels_)
    # clusterSet.discard(-1)  # discard the "noise" names
    # clusterNameLists = []
    # for clust in clusterSet:
    #     clusterNameLists.append(distanceNames.index[fits[matchFit].labels_ == clust])
    # clusterDF = pd.DataFrame(clusterNameLists)

    # distanceNames.index[fits[matchFit].labels_ == 0]
    # pdb.set_trace()

    # Need prototype (base) name for each cluster
    # output the "noise" names (cluster -1) as a separate file since so long


def main():
    """! This is the main function that reads in a similarity matrix pickle file 
    created by cleanPlaintiffs.py with a -s option. It then tries different 
    epsilon values for the DBSCAN clustering algorithm and plots the results.
    """
    parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')
    parser.add_argument('picklefile', help='The name of the similarity matrix pickle file to load')
    # parser.add_argument('-c', '--cutoff', help='The cutoff for similarity checking', type=float)

    start_time = datetime.datetime.now()  # save the time the script started
    args = parser.parse_args()  # parse the command line arguments

    if args.picklefile:
        if args.cutoff:
            cutoff = args.cutoff
        else:
            cutoff = 0.8
        findBaseNames(args.picklefile, cutoff)
        return
    stop_time = datetime.datetime.now()
    print(f'{__file__} took {stop_time-start_time} seconds')

if __name__ == '__main__':
    main()