
# 2021 Philly Project
This is a collection of code for analyzing the Philly data. The doxygen 
generated html documentation can be found at 
https://anitracks.github.io/2021Philly/index.html

Written by Seth McNeill  
Managed by David McNeill and Stacy Butler

# Usage
## cleanCount Outcomes.py
Cleaning and counting the most occurring outcomes is done as follows:
```
python .\src\cleanCountOutcomes.py ..\data\MC_specialreport_limiteddaterange_Nov6.csv
```

## cleanPlaintiffs.py - Creating the Comparison Matrix 
Running cleanPlaintiffs.py as shown below will create the comparison matrix pickle
file. This may take 9 minutes to run.
```
python .\src\cleanPlaintiffs.py ..\data\MC_specialreport_limiteddaterange_Nov6.csv -s
```
## cleanPlaintiffs.py - Plaintiff vs Outcome Matrix
The following is an example of running the cleanPlaintiffs.py script from inside the 
root folder to calculate the comparedPO.csv (plaintiffs vs outcomes matrix) file 
which takes about 41 seconds. It requires a camparison matrix pickle file to have 
already been created.
```
python .\src\cleanPlaintiffs.py ..\data\MC_specialreport_limiteddaterange_Nov6.csv -p .\src\20215121490-comparisonMatrix.pkl
```

## Updating Documentation Using Doxygen
The `docs` folder has a separate Git repository for the documentation. To update the 
documentation, `cd` into the `docs` folder. Inside that folder run:
```
doxygen ..\doxygen\Doxygen.in
```
This will create all the new documentation. To commit everything including the 
new/deleted files run:
```
git add -A
```
Now it is ready to `commit` and `push`.

# Progress
## 2021 March 18 
The code in cleanCountOutcomes.py reads in a csv file
from the Philidelphia court system, cleans, collates, and prints
out the outcomes column.

### Example output
```
Outcome Subcategories                                              Count
Judgment for Plaintiff by Default                                  40711
No Service, Dismissed without Prejudice                            28300
Continued To                                                       10414
Withdrawn without Prejudice                                         9647
Blank or NULL                                                       9236
Settled, Discontinued and Ended                                     5015
Administrative Continuance To                                       4694
Continued By Subpoena To                                            4511
Courtroom Transferred To                                            1613
Judgment for Plaintiff                                              1128
Judgment for Defendant                                               580
Judgment for Defendant by Default                                    308
Judgment Satisfied                                                   198
Held Under Advisement                                                143
Judgment for Plaintiff as Defendant on Counterclaim                  143
Deferred due to Bankruptcy filing                                    126
Withdrawn with Prejudice                                              98
Continuance Request Denied                                            47
Judgment for Defendant as Plaintiff on Counterclaim                   46
Transfer to Court of Common Pleas                                     42
Judgment by Agreement for money and/or possession                     27
Judgment by Agreement                                                 19
Withdrawn, Lack of Jurisdiction                                       13
Judgment for Defendant as Plaintiff on Counter Claim                  12
Adjudication Deferred                                                  9
Transfer to another jurisdiction                                       8
Petition/Affidavit Granted                                             8
Judgment for Plaintiff as Defendant on Counter Claim by Default        5
Withdrawn, Lack of Venue                                               3
Judgment for Defendant as Plaintiff on Counter Claim by Default        3
Petition / Continued To                                                2
Petition / Held Under Advisement                                       1
Petition/Affidavit Denied                                              1
Resolved by Criminal Mediation Agreement                               1
Defendant Administrative Continuance Request Denied                    1
Additional Information:                                                1
Discharged Bankruptcy Debt                                             1
Judgment for Plaintiff as Defendant on Counterclaim by Default         1
Petition/Affidavit Withdrawn Without Prejudice                         1
```
