#!/usr/bin/env python
# coding: utf-8

# # Extract the HbA1c values from MIMIC-III dataset documents

# In this notebook I will be developing a python script for extracting the HbA1c values from text documents. The main thing I am looking for is going to be A1c followed by some value.
# 
# I will be using PyConText to accomplish this task. I have found when experimenting with PyConText on the MIMIC-III dataset that you sometimes get some very odd things that come back when you use modifiers with numbers, so I am going to use one regular expression to obtain both the mention of HbA1c and the value. I will then remove everything that is not the number to obtain the actual value. 
# 
# This notebook is almost identical to the previous notebook, except that in this notebook I am running this on the test dataset. 
# 

# First step, import PyConText and define the functions (taken from the PyConText github page and modified with help from Jeff Ferraro) so that I can run the actual text parsing. 

# In[1]:


import pyConTextNLP.pyConText as pyConText
# itemData has been rewritten, so that it can take relative local path, where you can redirect it to your customized yml files later
import os
import itemData
import re
import glob
import pandas as pd
from xml.etree import ElementTree
import math


# In[2]:


my_targets=itemData.get_items('Yaml_Files/A1c_targets.yml')
my_modifiers=itemData.get_items('Yaml_Files/A1c_modifiers.yml')


# The functions *markup_sentence* and *markup_doc* were both ones that we went over in the NLP lab.

# In[3]:


## This one is the same, it just doesn't split it into sentences. 
def markup_sentence(s, modifiers, targets, prune_inactive=True):
    """
    """
    markup = pyConText.ConTextMarkup()
    markup.setRawText(s)
    markup.cleanText()
    markup.markItems(my_modifiers, mode="modifier")
    markup.markItems(my_targets, mode="target")
    markup.pruneMarks()
    markup.dropMarks('Exclusion')
    # apply modifiers to any targets within the modifiers scope
    markup.applyModifiers()
    markup.pruneSelfModifyingRelationships()
    if prune_inactive:
        markup.dropInactiveModifiers()
    return markup

def markup_doc(doc_text:str)->pyConText.ConTextDocument:
    rslts=[]
    context = pyConText.ConTextDocument()
    #for s in doc_text.split('.'):
    m = markup_sentence(doc_text, modifiers=my_modifiers, targets=my_targets)
    rslts.append(m)

    for r in rslts:
        context.addMarkup(r)
    return context

def get_output(something):
    context=markup_doc(something)
    output = context.getDocumentGraph()
    return output


# Ok, I have figured out how to get the pieces of a node that I can use for every node. I can put these into lists and then add the lists into a dataframe, then transpose the dataframe and I can have something to work with. The next step is going to be reading in the documents and figuring out how to apply 

# In[4]:


os.listdir('Text_Files/')


# In[5]:


import glob
list_of_files = glob.glob("Text_Files/Testing_Dataset/*.txt") # New Folder
# print(len(list_of_files))
list_of_files[0:3]
#len(list_of_files)


# In[6]:


replaced_list = [w.replace('Text_Files/Testing_Dataset/', '') for w in list_of_files] # New Folder
list_of_identifiers = [i.replace(".txt", "") for i in replaced_list] 
# print(list_of_identifiers[0:10])


# In[7]:


list_of_text = [] 
for file in list_of_files:
    text_file = open(file, 'r')
    list_of_text.append(text_file.read()) # Not Readlines
    text_file.close()


# In[8]:


# print(list_of_text[0])


# In[9]:


text_df = pd.DataFrame({"Identifier" : list_of_identifiers, "Text": list_of_text}) 
text_df.head()
# I might end up changing the identifier to the index column, but for now I am just going to use this. 


# In[10]:


def get_a1c_flag(a):
    try:
        if float(a) < 7.1:
            return "Good"
        elif float(a) >= 7.1 and float(a) < 10.1:
            return "Moderate"
        elif float(a) >= 10.1:
            return "Poor"
        else:
            return "Not Sure"
    except:
        return "Not a value"
i = 0
output_array = []
while i < len(text_df):
    raw_text = text_df["Text"][i]
    remove_MIMIC_comments = re.sub(r"\[\*\*.*?\*\*\]", "", raw_text)
    remove_times = re.sub(r"\d{1,2}:\d{2}\s?P?A?\.?M\.?", "", remove_MIMIC_comments)
    cleaned_text = re.sub(r"\s{2,}", r" ", remove_times)
    
    context=markup_doc(cleaned_text)
    root = ElementTree.fromstring(context.getDocumentGraph().getXML())
    for node in root.findall('.//node'):
        phrase = node.find('.//phrase').text
        tmp1 =  re.sub(r"[A|a]1[C|c]", "", phrase)
        A1c_Value = re.sub(r"[^\d{1,2}\.?\d{0,1}]", "", tmp1)
        A1c_Flag = get_a1c_flag(A1c_Value)
        literal = node.find('.//literal').text
        Start = node.find('.//spanStart').text
        Stop = node.find('.//spanStop').text
        Node_ID = node.find('.//id').text
        category = node.find('.//category').text
        try:
            modified_by = node.find('.//modifyingNode').text
        except:
            modified_by = "None"
        try:
            modifying_category = node.find('.//modifyingCategory').text
        except:
            modifying_category = "None"
        try:
            node_modified = node.find('.//modifiedNode').text
        except:
            node_modified = "None"
        output_array.append([text_df["Identifier"][i], Start, Stop, phrase, literal, A1c_Value, A1c_Flag, Node_ID,
                             modifying_category, modified_by, node_modified])
    i += 1
            
#output_array


# In[11]:


len(output_array)


# In[12]:


type(output_array)


# In[13]:


test_df = pd.DataFrame(output_array, columns=("Identifier", "Start", "Stop", "Phrase", "Annotation_Type", "A1c_Value", "A1c_Flag", "Node_ID", "Modifying_Category", "Modified_By", "Node_Modified"))
test_df.head() # New dataframe name


# I had put in f/u as a modifier so that it would have a modifier file, but all of my targets require a value. In other words, if they put f/u and a value it is either a mistake typing or it refers to something else. As such, I can get rid of all of the modifier columns and the rows about node ID, modifying node, modified by, and node modified. 

# In[14]:


modifier_columns = test_df[test_df["Node_Modified"]!="None"]
modifier_columns


# In[15]:


modifier_columns = test_df[test_df["Node_Modified"]!="None"]
A1c_Value_Results = test_df[["Identifier", "Start", "Stop", "Phrase", "Annotation_Type", "A1c_Value", "A1c_Flag"]].drop(modifier_columns.index, axis = 0)
len(A1c_Value_Results)


# In[16]:


A1c_Value_Results.head()


# In[17]:


A1c_Value_Results["A1c_Value"] = A1c_Value_Results["A1c_Value"].apply(pd.to_numeric)
A1c_Value_Results = A1c_Value_Results.groupby("Identifier").apply(lambda x: x.loc[x.A1c_Value.idxmax()])
A1c_Value_Results.to_csv("Output_Files/A1c_Results_Test_Dataset.csv") #New output file names
modifier_columns.to_csv("Output_Files/Modifier_Columns_to_A1c_Test_Dataset.csv") # I know this isn't needed, but I am going to save it for just in case


## In[18]:


# A1c_Value_Results.head()


## In[19]:


# Manual_Results = pd.read_csv("Manual_Annotation_Results/Manual.Annotation.Test_Dataset.A1c.Results.csv", index_col = 1)


## In[20]:


# Manual_Results.head()


## In[21]:


# Manual_Results.dtypes


## In[22]:


# A1c_Value_Results.dtypes


## In[23]:


# A1c_Value_Results["Identifier"] = A1c_Value_Results["Identifier"].apply(pd.to_numeric)


## In[24]:


# Merged_Manual_and_Machine = pd.merge(Manual_Results, A1c_Value_Results, on=['Identifier'], how = 'outer')
# Merged_Manual_and_Machine.head(8)


## If both HbA1c and A1c_Value are NaN = True Negative
## <br>If both HbA1c and A1c_Value are Numbers (must be the same) = True Positive
## <br>If HbA1c is NaN and A1c_Value is a number = False Positive
## <br>If HbA1c is a number and A1c_Value is Nan = False Negative
## <br>If Both columns give a number, but it doesn't match, give it False Positive even though this isn't technically correct. Luckily, I don't think I have any of those. 

## In[25]:


# def get_category(manual, machine):
#     if math.isnan(manual):
#         if math.isnan(machine):
#             return "True_Negative"
#         else:
#             return "False_Positive"
#     else:
#         if math.isnan(machine):
#             return "False_Negative"
#         elif manual == machine:
#             return "True_Positive"
#         else:
#             return "Non_Matching_Values"


# Merged_Manual_and_Machine["Category"] = Merged_Manual_and_Machine.apply(lambda x: get_category(x["HbA1c"], x["A1c_Value"]), axis = 1)


## In[26]:


# Merged_Manual_and_Machine.head()


## In[27]:


# Merged_Manual_and_Machine.to_csv("Output_Files/Test_Dataset_A1c_Result_Comparison.csv")


## In[28]:


# results = Merged_Manual_and_Machine.groupby(["Category"]).size()
# results


## Again, this never gave anything where it grabbed a value that was the wrong value. This is pretty robust to only grab the correct value if it grabs one. I did not see any of these in the dataset, but if there was one that said "HbA1c last week of about 6.8%" it wouldn't pick it up. I have deleted all MIMIC added comments, and the only one I saw in the training dataset with a time in the middle was a MIMIC comment. Anyways, again I got 100%
## 
## I only have two possibilities here (Yes, A1c value or no, no A1c value)
## <br>Below, TP = True positives, TN = True Negatives, FP = False Positives, FN = False Negatives
## 
## Recall Yes A1c = TP/(TP+FP) = 17/(17+0) = 1
## <br>Precision Yes A1c = TP/(TP+FN) = 17/(17+0) = 1
## <br>F-Measure = 2xPrecisionxRecall/(Precision + Recall) = 2x1x1/(1+1) = 1
## 
## Accuracy = (TP + TN)/total = (58+17)/75 = 1
## <br>NPV = TN/(FN+TN) = 58/(0+58) = 1
## <br>PPV = TP/(TP+FP) = 17/(17+0) = 1
## <br>Sens = TP/(TP+FN) = 17/(17+0) = 1
## <br>Spec = TN/(FP+TN) = 58/(0+58) = 1
## 

## In[ ]:





## In[ ]:




