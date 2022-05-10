"""!
 @file cleanCountOutcomes.py
 @brief Cleans the outcome data and counts how many of each there are
 @details The main function reads in the name of a csv file to process. 
 It then removes all rows that are exact duplicates of each other. Lastly,
 it processes the "Case Outcome" column via the following function stack:
  \dot
 digraph example{
 node[shape=record, fontname=Helvetica, fontsize=10];
 b [label="main"  URL= "\ref cleanCountOutcomes.main" ];
 c [label="outcomeList" URL= "\ref cleanCountOutcomes.outcomeList" ];
 d [label="cleanOutcome" URL= "\ref cleanCountOutcomes.cleanOutcome" ];
 b -> c -> d [arrowhead= "open", style = "dashed"];
 }
 \enddot
 It is cleaned via the following process:
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
import pandas as pd  # Pandas data manipulation library
import numpy as np  # for data processing
import re  # regular expression library for processing
import math  # for isnan


## matches all caps words to the end of the line
endCaps = re.compile(r'(\b(?:[A-Z]+)\b(?:\s[A-Z]+\b)*\.*)$')
## matches date and time to end of line in format 07/17/2017 1:15
datetimeToEnd = re.compile(r'(\s\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} [AP]M.*)$')  # selects date time to end

def removeDuplicates(df):
    """! Cleans the main df by removing duplicate rows
        @param df DataFrame that needs cleaning
        @returns cleaned df
    """
    # need to filter out exact duplicate rows in base dataset
    # keep=False keeps both original and duplicate
    # keep='first' marks all but first as True
    dups = df.duplicated(keep='first')  
    print(f'\n{len(dups[dups==True])} duplicates found') 
    #display(csvDF.loc[619,:])  # display a particular row
    df = df.drop_duplicates(keep='first')
    return(df)

def cleanOutcome(dirtyString):
    """! Removes the ALL CAPS words at the end of a string dirtyString, 
    everything after the first period (.), and any date/time and everything after it
       @param dirtyString string that contains extra case specific text
       @returns cleaned string
    """
    #endCaps.sub('', csvNoDups['Case Outcome'][10129]).strip()
    # Catch the nan's from assumably empty fields
    # nan's are both the empty strings and NULLs in David's data
    if(isinstance(dirtyString, float)):
        if(math.isnan(dirtyString)):
            return('Blank or NULL')
        else:
            pdb.set_trace()  # it isn't an expected value
    try:
        cleanedString = endCaps.sub('', dirtyString).strip()
    except TypeError as e:
        pdb.set_trace()  # unexpected type
    firstCleaned = cleanedString.split('.')[0] # remove everything after first .
    # remove everything including and after date-time 
    #   (typical format 07/17/2017 1:15)
    dateCleaned = datetimeToEnd.sub('', firstCleaned).strip()
    return(dateCleaned)


def outcomeList(df, columnName='Case Outcome'):
    """! Returns a list of cleaned and sorted outcomes that
    have been grouped by commonality and counts the number
    of occurrences of each one. It applies the cleanOutcome
    function to the dataframe of case outcomes.

    @param df is a panda dataframe of outcomes from reading in the csv file 
        of data
    @returns cleaned and sorted outcomes
    """
    outcomes = df[columnName]
    # clean up the outcome string
    cleanedOutcomes = outcomes.apply(cleanOutcome)
    # Good ways to count specific occurances: 
    # https://stackoverflow.com/a/35277776
    # see also cleanedOutcomes.value_counts()
    df = df.assign(OutcomeCleaned=cleanedOutcomes)
    return((cleanedOutcomes.value_counts(), df))


def main():
    """! This is the main function that reads in a csv file containing the
    court data from the filename passed as the first command line argument. 
    It then filters out the duplicate rows. It also calculates the median 
    judgement amount as a proof of concept. Lastly, it calls outcomeList to 
    create a cleaned and counted list of the outcomes and prints the results.
    """
    parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')
    parser.add_argument('csvfile', help='The name of the csv file to load')
#    parser.add_argument('dbfile', help='The name of the sqlite db file')

    start_time = datetime.datetime.now()  # save the time the script started
    args = parser.parse_args()  # parse the command line arguments

    # Plaintiff Attorney ID and Defendant Attorney ID come in as mixed types for some reason
    csvDF = pd.read_csv(args.csvfile)  # read in the csv data
    #print(f'The column names are:\n{csvDF.columns.values}')

    csvNoDups = removeDuplicates(csvDF)

    #print("\nThe column types are:")
    #print(csvNoDups.dtypes)  # print out the data type for each column
    
    # calculate the median judgment amount as a demonstration of reading the file
    medJudgment = np.nanmedian(csvNoDups['Judgment Amount'])
    print(f'\nThe median judgment amount is ${medJudgment}')

    # need to look at cases where the same attorney is listed on both sides
    # try using sent2vec to sort out similar ones
    # pypi.org/project/sent2vec
    outs = outcomeList(csvNoDups)[0]
    print('\nOutcome Subcategories')
    print(outs.to_string())

    stop_time = datetime.datetime.now()
    print(f'{__file__} took {stop_time-start_time} seconds')

if __name__ == '__main__':
    main()