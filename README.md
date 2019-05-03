<!-- vim: set textwidth=80 : -->

# BMI6115 Biomedical Text Processing Final Project

I know that this doesn't necessarily need to be posted here on GitHub, but I
think that this will be an easier way to share the code than trying to email it
back and forth.  
<br>This project is setting up a pipeline to process the text
from hospital records (obtained from the MIMIC-III dataset) and determine two
things: 
1) If the record specifically mentions diagnosis of diabetes
2) The HbA1c value if present in the notes.
<br>I can't post the actual text files from the MIMIC-III database because they
may still have some identifiers, but they can be obtained directly from the
MIMIC-III providers.
You can find the information about the MIMIC-III dataset in this publication:
Johnson et al., [“MIMIC-III, a freely accessible critical care database,”
Scientific Data 3:160035](https://www.ncbi.nlm.nih.gov/pubmed/27219127)

This was originally run in python notebooks, but for simplicity I have converted
them to python scripts that can be run from the command line. To do this I used
this function: 
~jupyter nbconvert --to script 'NLP_Extract_A1c_Values_Training.ipynb'~

Both of these systems use PyConText to perform this function. PyConText can be
found on it's
[GitHub](https://github.com/chapmanbe/pyConTextNLP/tree/master/pyConTextNLP)
page. The publication was put forth by Wendy and Brian Chapman ([Chapman BE, Lee
S, Kang KP, Chapman WW 2011. Document-level classification of CT pulmonary
angiography reports based on an extension of the ConText algorithm. J Biomed
Inform 44(5):728-737.](https://www.ncbi.nlm.nih.gov/pubmed/21459155) 

If you would like to repeat the analysis, you can use the python scripts in the
"Document Selection Scripts" folder, but you will have to modify the scripts to
point to your version of the SQL database of the MIMIC-III documents. Once
documents are obtained and split to one text file per document, you will have to
split the files into test and train datasets if you would like to run all of the
scripts. They are currently set up to use training documents in
"Text_Files/Training_Dataset/" and test documents in "Text_Files/Test_Dataset/".
My list of test and training documents can be found in the files
"Test_Files.txt" and "Training_Files.txt"
For the deployment script, NLP_Deployment_A1c_Values_and_Diabetes_Mentions.py,
you will have to update your script to point to your local version of the CSV
file NOTEEVENTS.csv from the MIMIC-III database that can be obtained with
permission [here](https://physionet.org/works/MIMICIIIClinicalDatabase/files/).

Additionally, if you want to change the SQL selection, I would recommend testing
it after obtaining access to the MIMIC-III dataset using the MIMIC query builder
which can be found [here](https://querybuilder-lcp.mit.edu/).

If you would like to try running the python scripts, here is the order that I
would use:
1) NLP_Extract_A1c_Values_Training.py
2) NLP_Extract_A1c_Values_Test.py
3) NLP_Diabetes_Mention_Training.py
4) NLP_Diabetes_Mention_Test.py
5) NLP_Deployment_A1c_Values_and_Diabetes_Mentions.py

I will also mention that the deployment script might take a couple of hours to
run because it does use the entire MIMIC-III dataset. Additionally, there are
628 documents in the NOTEEVENTS.csv file that have text that includes characters
that couldn't be parsed by ElementTree, so those documents are not included in
the results of the final analysis and the line number in the NOTEEVENTS.csv will
be printed out to the screen as the script runs. 

This is really just for me, but I hope it helps anyone that is interested in
learning how to use PyConTextNLP on the MIMIC-III dataset. Good luck!

