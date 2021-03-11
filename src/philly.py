"""!
 @file philly.py
 @brief Data collection and analysis for Philly data
 @details 
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


def main():
    """! This is the main function that collects command line arguments
    and acts on them.
    """
    parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')
    parser.add_argument('csvfile', help='The name of the csv file to load')
    parser.add_argument('dbfile', help='The name of the sqlite db file')

    start_time = datetime.datetime.now()  # save the time the script started
    args = parser.parse_args()  # parse the command line arguments

    csvDF = pd.read_csv(args.csvfile)  # read in the csv data
    print(f'The column names are:\n{csvDF.columns.values}')

    # calculate the median judgment amount
    medJudgment = np.nanmedian(csvDF['Judgment Amount'])
    print(f'The median judgment amount is ${medJudgment}')

    #conn = sqlite3.connect(args.dbfile)  # connect to the database
    # load the csvData into the database
    #csvDF.to_sql('csvDF', conn, if_exists='fail', index=False)

    pdb.set_trace()
    stop_time = datetime.datetime.now()
    print(f'{__file__} took {stop_time-start_time} seconds')

if __name__ == '__main__':
    main()