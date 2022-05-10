"""!
 @file cleanPlaintiffs.py
 @brief Cleans the plaintiff names and counts frequency of occurance
 @details The functions in this script can clean plaintiff names and 
 then cluster the names to put similar names together. For instance,
   - Victoria Fire and Casualty Co. a/s/o Robert Logan
   - Victoria Fire and Casualty Company a/s/o Francisco Mulero
both refer to the came plaintiff and should be clustered together.

We did the following to clean the plaintiff names:
   - Removed "a/s/o", "as subrogee of", “aso”, commas, and the text that followed those items
   - Removed any non-alphanumeric characters
   - Used CleanCo to remove LLC, INC, etc.
   - Put the names into all uppercase

Clustering plaintiffs is started by using the [jellyfish](https://github.com/jamesturk/jellyfish) 
jaro_similarity function as can be seen in the createSimilarityMatrix() function to 
calculate similarities between all the cleaned plaintiff names. Once the 
similarity matrix has been created, the [DBSCAN](https://towardsdatascience.com/dbscan-algorithm-complete-guide-and-application-with-python-scikit-learn-d690cbae4c5d)
algorithm is used to cluster similar names.

Typical use cases are as follows:

    python .\src\cleanPlaintiffs.py ..\data\MC_specialreport_limiteddaterange_Nov6.csv -s
    python .\src\cleanPlaintiffs.py ..\data\MC_specialreport_limiteddaterange_Nov6.csv -p .\src\20215121490-comparisonMatrix.pkl

The first creates the similarity matrix (may take 9 minutes). The second uses this
similarity matrix to build a plaintiff vs outcome matrix.

 @author Seth McNeill
 @date 2021 March 11
"""

import datetime  # used for start/end times
import argparse  # Improved command line functionality
import pdb       # Debugging
import pandas as pd  # Pandas data manipulation library
import numpy as np  # for data processing
import re  # regular expression library for processing
import math  # for isnan
import cleanCountOutcomes  # for cleanWholeDF and outcome cleaning
from sklearn.feature_extraction.text import TfidfVectorizer  # TF-IDF tokanizer
import matplotlib.pyplot as plt  # plotting capability
from sklearn.cluster import KMeans  # K-Means Clustering
from cleanco import prepare_terms, basename  # removes co, llc, lp, etc. from names
import distance  # library that has string comparison functions (docs say it is slow)
import jellyfish  # library for string comparisons that is supposed to be fast
#import strsimpy  # string comparison library
import textdistance  # string comparison library
#import abydos  # string comparison library
import inspect  # for looking at base class of method
#import copy  # for deep copying
from sklearn.cluster import DBSCAN  # DBSCAN clustering algorithm

# methods to try:
# Bag of Words
# TF-IDF
# Word2Vec
# references:
# https://towardsdatascience.com/clustering-documents-with-python-97314ad6a78d
# https://medium.com/swlh/text-classification-using-the-bag-of-words-approach-with-nltk-and-scikit-learn-9a731e5c4e2f
# https://www.excelr.com/blog/data-science/natural-language-processing/implementation-of-bag-of-words-using-python
# https://stackoverflow.com/questions/6400416/figure-out-if-a-business-name-is-very-similar-to-another-one-python

# cleanco company terms
cleanco_terms = prepare_terms()
# Also need to remove The and A from the beginning
stopwords = ['a', 'an', 'the', 'are']
# Also need to filter on a/s/o
## match up to case insensitive first LLC or first comma
llcMatch = re.compile(r'(llc|,|a/s/o|as subrogee of|\saso\s).*', re.I)
## clean all non-alpha and space characters out
alphaMatch = re.compile(r'[^a-z A-Z0-9]')

## matches all caps words to the end of the line
endCaps = re.compile(r'(\b(?:[A-Z]+)\b(?:\s[A-Z]+\b)*\.*)$')
## matches date and time to end of line in format 07/17/2017 1:15
datetimeToEnd = re.compile(r'(\s\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} [AP]M.*)$')  # selects date time to end

def get_class_that_defined_method(meth):
    """! from 
    """
    if inspect.ismethod(meth) or (inspect.isbuiltin(meth) and getattr(meth, '__self__', None) is not None and getattr(meth.__self__, '__class__', None)):
        for cls in inspect.getmro(meth.__self__.__class__):
            if meth.__name__ in cls.__dict__:
                return cls
        meth = getattr(meth, '__func__', meth)  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0],
                      None)
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects


def cleanPlaintiff(fullPlaintiff):
    """! Removes everything from LLC or comma to the end of the name
       @param fullPlaintiff is the whole plaintiff name
       @returns cleaned string
    """
    ## Catch the nan's from assumably empty fields
    ## nan's are both the empty strings and NULLs in David's data
    if(isinstance(fullPlaintiff, float)):
        if(math.isnan(fullPlaintiff)):
            return('Blank or NULL')
        else:
            pdb.set_trace()  # it isn't an expected value
    try:
        cleanedString = llcMatch.sub('', fullPlaintiff).strip()
    except TypeError as e:
        pdb.set_trace()  # unexpected type
    ## Use the cleanco package to clean any other company text
    cleanco_name = basename(cleanedString, cleanco_terms, prefix=False, middle=False, suffix=True)
    if cleanco_name == '':
        cleanco_name = cleanedString
        print(f"cleanco failed on: {cleanedString}")
    ## remove everything not alphanumeric or space
    cleanedOut = alphaMatch.sub('', cleanco_name).strip().upper()
    if(cleanedOut == ''):
        print('blank output')
        pdb.set_trace()
    return(cleanedOut)


def similarNameList(testName, matchList, compare_function, cutoff=90, nReturned=50):
    """! Returns a list of names similar to testName from the matchList
    whose match value is >= cutoff and returns no more than nReturned matches

    @param testName String to search match
    @param matchList List of names to compare against
    @param cutoff The minimum percent match to include in returned list
    @param nReturned The maximum number of results to return
    """
    comparisons = matchList.apply(compare_function, args=([testName]))
    return(comparisons)


def testComparisonMethod(seriesToTest, testFunction, numberToTry):
    """! Runs a test on a comparison method to estimate the total time
    required to run it on the full dataset

    @param seriesToTest A Pandas Series object to run the test against
    @param testFunction The text comparison function to try
    @param numberToTry The sampling size to run
    """
    nTest = numberToTry  # number of names to test
    startTime = datetime.datetime.now()
    print(f"Starting at {startTime}")
    ## took too long
    # deduped = process.dedupe(cleanedValueCounts.index.to_series(), threshold=95)
    ## took too long
    similarNames = seriesToTest.apply(similarNameList, \
        args=(seriesToTest[:nTest], testFunction))
    totalTime = datetime.datetime.now() - startTime
    print(f"similarNameList took {totalTime} seconds")
    print(f"Time per name: {totalTime/nTest}")
    print(f"Time estimate for whole table: {seriesToTest.size*totalTime/nTest}")


def createSimilarityMatrix(cleanedValueCounts):
    """! Taking the cleanedValueCount from plaintiffList, this 
    function creates a similarity matrix between the cleaned names
    @param cleanedValueCounts returned by plaintiffList
    @returns Name of pickle file similarity matrix is saved in
    """
    # vectorizer = TfidfVectorizer(stop_words={'english'})
    # X = vectorizer.fit_transform(df['Plaintiff Name(s)'])

    # create list of lists of similar names
    # do quick histogram analysis of lengths of lists to get an idea
    # of what is left to do

    # cutoff = 90  ## Percent match has to be >= to this
    # nReturned = None  ## number of matches to return

    ## Time tests for different algorithms
    # nTest = 500  # number of names to test
    # functionsToTest = {'textdistance.jaro.normalized_similarity': textdistance.jaro.normalized_similarity,
    # 'jellyfish.jaro_similarity': jellyfish.jaro_similarity,
    # 'textdistance.strcmp95.normalized_similarity': textdistance.strcmp95.normalized_similarity
    # }
    # for ind, fun in functionsToTest.items():
    #     print(f'Starting {ind}')
    #     testComparisonMethod(cleanedValueCounts.index.to_series(), \
    #         fun, nTest)

    startTime = datetime.datetime.now()
    print(f"Started at {startTime}")
    ## took too long
    # deduped = process.dedupe(cleanedValueCounts.index.to_series(), threshold=95)
    ## took too long
    similarNames = cleanedValueCounts.index.to_series().apply(similarNameList, \
        args=(cleanedValueCounts.index.to_series(), jellyfish.jaro_similarity))
    endTime = datetime.datetime.now()
    totalTime = endTime - startTime
    print(f"similarNameList took {totalTime} seconds")

    fname = f"{endTime:%Y%m%d%H%M%S}-comparisonMatrix.pkl"
    # saving Pandas dataframes:
    # https://towardsdatascience.com/the-best-format-to-save-pandas-data-414dca023e0d
    similarNames.to_pickle(fname)
    
    #  Elbow method of determining how many means to use
    # Sum_of_squared_distances = []
    # K = range(2,5)
    # for k in K:
    #     print(f"Trying {k} means")
    #     km = KMeans(n_clusters=k, max_iter=200, n_init=10)
    #     km = km.fit(X)
    #     Sum_of_squared_distances.append(km.inertia_)
    # plt.plot(K, Sum_of_squared_distances, 'bx-')
    # plt.xlabel('k')
    # plt.ylabel('Sum_of_squared_distances')
    # plt.title('Elbow Method For Optimal k')
    # plt.show()
    return fname


def plaintiffList(df, fieldName):
    """!  Returns df with added column of cleaned plaintiff names
    @param df is a panda dataframe of plaintiff names from reading in the csv file 
        of data that has had duplicates removed and other cleaning done
    @param fieldname The column name that contains the plaintiff names to be cleaned
    @returns Tuple (cleaned and sorted plaintiff names, 
        df with cleaned plaintiff names column)
    """
 
    outcomes = df[fieldName].copy(deep=True)
    # clean up the outcome string
    cleanedPlaintiffs = outcomes.apply(cleanPlaintiff)
    # add cleaned plaintiff names to the original dataframe
    # the following line caused a setting copy of slice from dataframe warning
    # https://www.dataquest.io/blog/settingwithcopywarning/
    df = df.assign(PlaintiffCleaned=cleanedPlaintiffs)

    # Good ways to count specific occurances: 
    # https://stackoverflow.com/a/35277776
    # see also cleanedOutcomes.value_counts()
    cleanedValueCounts = cleanedPlaintiffs.value_counts()
    return((cleanedValueCounts, df))


def dbscanFit(fname, eps, min_samples=2):
    """! Runs DBSCAN clustering on the similarity matrix in fname
    with epsilon (eps) set to eps and clusters requiring at least
    min_samples in them.

    @param fname The filename for a pickle file containing a similarity matrix
    @param eps Epsilon - the largest distance allowed to be considered a neighbor
    @param min_samples The minimum number of names in a cluster
    """
    similarNames = pd.read_pickle(fname)
    distanceNames = 1 - similarNames
    dbfit = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed').fit(distanceNames)
    return dbfit


def findBaseNames(fname, cutoff=0.9):
    """! Finds the base name of each cleaned name
    This method does not work as of 2021 May 12

    @param fname The filename of the pickle file created by plaintiffList
    @param cutoff The cutoff similarity between names to assume are the same
    """
    similarNames = pd.read_pickle(fname)
    test1 = similarNames.apply(lambda x: x > cutoff)
    seenNames = set()  # set of names already processed
    nameGroups = []  # list of name groups
    startTime = datetime.datetime.now()
    print(f'Starting the collation at {startTime}')
    for name in test1.index:
        if name not in seenNames:
            checkNamesSet = test1[test1[name] == True].index
            closeNamesSet = set(checkNamesSet)
            seenNames.add(name)
            for check in checkNamesSet:
                if check not in seenNames:
                    moreNames = test1[test1[check] == True].index
                    seenNames.add(check)
                    closeNamesSet.update(moreNames)
            nameGroups.append(closeNamesSet)
    stopTime = datetime.datetime.now()
    print(f'took {stopTime - startTime} seconds')
    pdb.set_trace()
    return(nameGroups)

    # closeNames = test1[test1['MIDLAND FUNDING'] == True].index.to_series()
    # closeNamesSet = set(test1[test1['MIDLAND FUNDING'] == True].index) 
    # for name in closeNamesSet:
    #     moreNames = set(test1[test1[name] == True].index)
    #     closeNamesSet = closeNamesSet.union(moreNames)
    # pdb.set_trace()


def main():
    """! This is the main function that reads in a csv file containing the
    court data from the filename passed as the first command line argument. 
    It then prints out the column names for reference, filters out the
    duplicate rows, and prints out the column types for reference. It also
    calculates the median judgement amount as a proof of concept. Lastly,
    it calls outcomeList to create a cleaned and counted list of the outcomes
    and prints the results.
    """
    parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')
    parser.add_argument('csvfile', help='The name of the csv file to load')
    parser.add_argument('-p', '--picklefile', help='The name of the pickle file to load')
#    parser.add_argument('-c', '--cutoff', help='The cutoff for similarity checking', type=float)
    parser.add_argument('-e', '--eps', help='The neighbor distance setting for DBSCAN', type=float)
    parser.add_argument('-s', '--similarity', action='store_true', help='Do similarity calculations')

    start_time = datetime.datetime.now()  # save the time the script started
    args = parser.parse_args()  # parse the command line arguments

    # Plaintiff Attorney ID and Defendant Attorney ID come in as mixed types for some reason
    csvDF = pd.read_csv(args.csvfile)  # read in the csv data
    # print(f'The column names are:\n{csvDF.columns.values}')

    df = cleanCountOutcomes.removeDuplicates(csvDF)
    (cleanedValueCounts, df) = plaintiffList(df, 'Plaintiff Name(s)')
    (outcomes, df) = cleanCountOutcomes.outcomeList(df, 'Case Outcome')

    if args.similarity:  # create the similarity matrix. Takes hours to calculate
        pickleFileName = createSimilarityMatrix(cleanedValueCounts)
    elif args.picklefile:
        pickleFileName = args.picklefile
    else:
        raise Exception("Need to either pass the -s flag or the -p with pickle file name")
    
    print(f'Using {pickleFileName} for similarity matrix')

    if args.eps:
        eps = args.eps
    else:
        eps = 0.1
    dbfit = dbscanFit(pickleFileName, eps)
    similarNames = pd.read_pickle(pickleFileName)
    distanceNames = 1 - similarNames

    # print('\nPlaintiff Frequency')
    # print(f'{plaintiffs}')
    # for plaintiff, pCount in plaintiffs.items():
    #     if(pCount > 10):
    #         print(f"{plaintiff},{pCount}")

    # data we have
    clusterSet = set(dbfit.labels_)
    # clusterSet.discard(-1)  # discard the "noise" names
    clusterNameLists = []
    for clust in clusterSet:
        clusterNameLists.append(distanceNames.index[dbfit.labels_ == clust])
    clusterDF = pd.DataFrame(clusterNameLists)  # each row is list of names in cluster
    
    df  # whole dataset with cleaned plaintiff and outcomes
    dbfit.labels_  # cluster number for cleanedPlaintiff
    df.iloc[0]['PlaintiffCleaned']  # Need to know what group this is in
    df.iloc[0]['OutcomeCleaned']

    df['ClusterNum'] = -5  # set clusterNum to an invalid number to make sure all get changed
    df['ClusterName'] = 'ZZ-Unclustered'  # set clusterNum to an invalid number to make sure all get changed
    maxClusterIndex = max(clusterDF.index)  # store off max index for use later
    clusterDF.insert(0, 'Count', -1)  # set count to an invalid number to allow checking
    clusterNames = []  # list of cluster names
    # Set the cluster number for each entry in df
    for ind in clusterDF.index:
        rowIndexer = df['PlaintiffCleaned'].isin(clusterDF.iloc[ind])
        clusterDF.loc[ind,'Count'] = len(df.loc[rowIndexer,'ClusterNum'])
        if(ind != maxClusterIndex):
            df.loc[rowIndexer,'ClusterNum'] = ind
            df.loc[rowIndexer, 'ClusterName'] = df.loc[rowIndexer, 'PlaintiffCleaned'].mode()[0]
            clusterNames.append(df.loc[rowIndexer, 'PlaintiffCleaned'].mode()[0])
        else:  # set the catchall/not in cluster values to -1
            df.loc[df['PlaintiffCleaned'].isin(clusterDF.iloc[ind]),'ClusterNum'] = -1
            df.loc[rowIndexer, 'ClusterName'] = df.loc[rowIndexer, 'PlaintiffCleaned']

    # create the comparison matrix
    # https://stackoverflow.com/questions/48465941/counting-combinations-between-two-dataframe-columns
    time_now = datetime.datetime.now()
    comparedPO = pd.crosstab(df['ClusterName'], df['OutcomeCleaned'])  # Seems to be a good base dataset
    comparedPO.insert(0, 'Clustered','unknown')
    comparedPO.loc[comparedPO.index.isin(clusterNames),'Clustered'] = True
    comparedPO.loc[~comparedPO.index.isin(clusterNames),'Clustered'] = False
    comparedPO.to_csv(f'{time_now:%Y%m%d%H%M%S}-comparedPO.csv')

    stop_time = datetime.datetime.now()
    print(f'{__file__} took {stop_time-start_time} seconds so far')
    # the following line counts the Plaintiff names that contain Midland as a check
    #nMidlands = len(csvNoDups[csvNoDups['Plaintiff Name(s)'].str.contains('Midland', flags=re.IGNORECASE)]['Plaintiff Name(s)'])

    stop_time = datetime.datetime.now()
    print(f'{__file__} took {stop_time-start_time} seconds')

if __name__ == '__main__':
    main()