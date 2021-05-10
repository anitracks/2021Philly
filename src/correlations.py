"""!
 @file correlations.py
 @brief Data analysis
 @details This finds some correlations between plaintiffs and outcomes

 @author Seth McNeill
 @date 2021 April 21
"""

import datetime  # used for start/end times
import argparse  # Improved command line functionality
import pdb       # Debugging
import csv       # CSV file operations
import pandas as pd  # Pandas data manipulation library
import sqlite3   # built in sql database
import numpy as np  # for data processing
import re  # regular expression library for processing
import math  # for isnan
import cleanPlaintiffs  # to clean the plaintiff names
import cleanCountOutcomes  # for cleaning df and outcomes


def main():
    """! This is the main function that reads in a csv file containing the
    court data from the filename passed as the first command line argument. 
    """
    parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')
    parser.add_argument('csvfile', help='The name of the csv file to load')

    start_time = datetime.datetime.now()  # save the time the script started
    args = parser.parse_args()  # parse the command line arguments

    # Plaintiff Attorney ID and Defendant Attorney ID come in as mixed types for some reason
    csvDF = pd.read_csv(args.csvfile)  # read in the csv data

    # need to look at cases where the same attorney is listed on both sides
    # try using sent2vec to sort out similar ones
    # pypi.org/project/sent2vec

    df = cleanCountOutcomes.cleanWholeDF(csvDF)
    (plaintiffs, df) = cleanPlaintiffs.plaintiffList(df, 'Plaintiff Name(s)')
    (outcomes, df) = cleanCountOutcomes.outcomeList(df, 'Case Outcome')
    print(df['PlaintiffCleaned'].head())

    # Look at rows where Plaintiff Name(s) == plaintiffs
    df.loc[df['PlaintiffCleaned'] == plaintiffs.index[0],'OutcomeCleaned'].value_counts()
    # need to use cleaned outcomes, not raw outcomes for line above ^

    # https://stackoverflow.com/questions/48465941/counting-combinations-between-two-dataframe-columns
    comparedPO = pd.crosstab(df['PlaintiffCleaned'], df['OutcomeCleaned'])  # Seems to be a good base dataset
    comparedPO.to_csv('comparedPO.csv')
    groupedPO = df.groupby(['PlaintiffCleaned','OutcomeCleaned']).size().reset_index().rename(columns={0:'count'})  # data not in right form
    pdb.set_trace()

    # This is a bootstrapping method to find more of the similar plaintiff names
    matched = 0
    diffMatched = 0
    for index, value in plaintiffs.items():
        nFind = len(cleanDF[cleanDF['Plaintiff Name(s)'].str.contains(index, case=False)])
        if nFind != value:
            print(f"{index} found {nFind} out of {value}")
            diffMatched += 1
            #pdb.set_trace()
        else:
            print(f"{index} matched")
            matched += 1

    print(f"{matched} matched, {diffMatched} didn't match")
    stop_time = datetime.datetime.now()
    print(f'{__file__} took {stop_time-start_time} seconds')

if __name__ == '__main__':
    main()