"""!
 @file cleanPlaintiffs.py
 @brief Cleans the plaintiff names and counts frequency of occurance
 @details The main function reads in the name of a csv file to process. 

 @todo change the following documentation
 The "Case Outcome" column is processed via 
  \dot
 digraph example{
 node[shape=record, fontname=Helvetica, fontsize=10];
 b [label="main"  URL= "\ref cleanCountOutcomes.main" ];
 c [label="outcomeList" URL= "\ref cleanCountOutcomes.outcomeList" ];
 d [label="cleanOutcome" URL= "\ref cleanCountOutcomes.cleanOutcome" ];
 b -> c -> d [arrowhead= "open", style = "dashed"];
 }
 \enddot
 It is cleaned via the following
 processes:
 -# Check for nan which arise from blank or Null input values
 -# Remove all trailing ALL CAPS WORDS
 -# Remove everything after the first period (.)
 -# Remove date/time and everything after it (typical format 07/17/2017 1:15)

 Then the count of each unique value is calculated and printed.

 @author Seth McNeill
 @date 2021 March 11
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
import cleanCountOutcomes  # for cleanWholeDF and outcome cleaning

## match up to case insensitive first LLC or first comma
llcMatch = re.compile(r'(llc|,).*', re.I)
## clean all non-alpha and space characters out
alphaMatch = re.compile(r'[^a-z A-Z0-9]')

## matches all caps words to the end of the line
endCaps = re.compile(r'(\b(?:[A-Z]+)\b(?:\s[A-Z]+\b)*\.*)$')
## matches date and time to end of line in format 07/17/2017 1:15
datetimeToEnd = re.compile(r'(\s\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} [AP]M.*)$')  # selects date time to end


def cleanPlaintiff(fullPlaintiff):
    """! Removes everything from LLC or comma to the end of the name
       @param fullPlaintiff is the whole plaintiff name
       @returns cleaned string
    """
    # Catch the nan's from assumably empty fields
    # nan's are both the empty strings and NULLs in David's data
    if(isinstance(fullPlaintiff, float)):
        if(math.isnan(fullPlaintiff)):
            return('Blank or NULL')
        else:
            pdb.set_trace()  # it isn't an expected value
    try:
        cleanedString = llcMatch.sub('', fullPlaintiff).strip()
    except TypeError as e:
        pdb.set_trace()  # unexpected type
    # remove everything not alphanumeric or space
    cleanedOut = alphaMatch.sub('', cleanedString).strip().upper()
    if(cleanedOut == ''):
        print('blank output')
        pdb.set_trace()
    return(cleanedOut)


def plaintiffList(df, fieldName):
    """!  Returns df with added column of cleaned plaintiff names
    @param df is a panda dataframe of plaintiff names from reading in the csv file 
        of data that has had duplicates removed and other cleaning done
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
    return((cleanedPlaintiffs.value_counts(), df))

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
#    parser.add_argument('dbfile', help='The name of the sqlite db file')

    start_time = datetime.datetime.now()  # save the time the script started
    args = parser.parse_args()  # parse the command line arguments

    # Plaintiff Attorney ID and Defendant Attorney ID come in as mixed types for some reason
    csvDF = pd.read_csv(args.csvfile)  # read in the csv data
    print(f'The column names are:\n{csvDF.columns.values}')

    print("\nThe column types are:")
    print(csvDF.dtypes)  # print out the data type for each column

    # need to look at cases where the same attorney is listed on both sides
    # try using sent2vec to sort out similar ones
    # pypi.org/project/sent2vec

    df = cleanCountOutcomes.cleanWholeDF(csvDF)
    (plaintiffs, df) = plaintiffList(df, 'Plaintiff Name(s)')
    (outcomes, df) = cleanCountOutcomes.outcomeList(df, 'Case Outcome')
    print('\nPlaintiff Frequency')
    print(f'{plaintiffs}')

    for plaintiff, pCount in plaintiffs.items():
        if(pCount > 10):
            print(f"{plaintiff},{pCount}")

    # the following line counts the Plaintiff names that contain Midland as a check
    #nMidlands = len(csvNoDups[csvNoDups['Plaintiff Name(s)'].str.contains('Midland', flags=re.IGNORECASE)]['Plaintiff Name(s)'])

    #conn = sqlite3.connect(args.dbfile)  # connect to the database
    # load the csvData into the database
    #csvNoDups.to_sql('csvNoDups', conn, if_exists='fail', index=False)

    stop_time = datetime.datetime.now()
    print(f'{__file__} took {stop_time-start_time} seconds')

if __name__ == '__main__':
    main()