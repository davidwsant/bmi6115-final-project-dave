#!/usr/bin/env python
# coding: utf-8

# # Extract the Diabetes Mention from MIMIC-III dataset documents

# In this notebook I will be developing a python script for finding the mention of Diabetes in text documents. This notebook is going to go through the actual MIMIC documents that I have selected to be my training documents. 
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

# Set distance for each modification type
distance_negation = 40
distance_other = 40
distance_hypothetical = 70
distance_type = 70


# In[2]:


os.listdir('Yaml_Files')


# In[3]:


my_targets=itemData.get_items('Yaml_Files/Diabetes_targets.yml')
my_modifiers=itemData.get_items('Yaml_Files/Diabetes_modifiers.yml')


# The functions *markup_sentence* and *markup_doc* were both ones that we went over in the NLP lab.

# In[4]:


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
    def markup_doc(doc_text:str)->pyConText.ConTextDocument:
        rslts=[]
        context = pyConText.ConTextDocument()
#         for s in doc_text.split('.'):
#             m = markup_sentence(s, modifiers=my_modifiers, targets=my_targets)
#             rslts.append(m)

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

# In[5]:


os.listdir('Text_Files/')


# In[6]:


import glob
list_of_files = glob.glob("Text_Files/Testing_Dataset/*.txt")
# print(len(list_of_files))
list_of_files[0:3]
#len(list_of_files)


# In[7]:


replaced_list = [w.replace('Text_Files/Testing_Dataset/', '') for w in list_of_files] 
list_of_identifiers = [i.replace(".txt", "") for i in replaced_list] 
# print(list_of_identifiers[0:10])


# In[8]:


list_of_text = [] 
for file in list_of_files:
    text_file = open(file, 'r')
    list_of_text.append(text_file.read()) # Not Readlines
    text_file.close()


# In[9]:


# print(list_of_text[0])


# In[10]:


text_df = pd.DataFrame({"Identifier" : list_of_identifiers, "Text": list_of_text}) 
text_df.head()


# In[11]:


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
        #tmp1 =  re.sub(r"[A|a]1[C|c]", "", phrase)
        #A1c_Value = re.sub(r"[^\d{1,2}\.?\d{0,1}]", "", tmp1)
        #A1c_Flag = get_a1c_flag(A1c_Value)
        literal = node.find('.//literal').text
        Start = node.find('.//spanStart').text
        Stop = node.find('.//spanStop').text
        Node_ID = node.find('.//id').text
        category = node.find('./category').text #This picks up target or modifier, not useful
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
        output_array.append([text_df["Identifier"][i], Start, Stop, phrase, literal, Node_ID,
                             modifying_category, modified_by, node_modified])
    i += 1
            
#output_array


# In[12]:


# output_array


# In[ ]:





# In[ ]:





# In[13]:


# raw_text = text_df["Text"][1]
# remove_MIMIC_comments = re.sub(r"\[\*\*.*?\*\*\]", "", raw_text)
# remove_times = re.sub(r"\d{1,2}:\d{2}\s?P?A?\.?M\.?", "", remove_MIMIC_comments)
# cleaned_text = re.sub(r"\s{2,}", r" ", remove_times)
    
# context=markup_doc(cleaned_text)
# root = ElementTree.fromstring(context.getDocumentGraph().getXML())
# for node in root.findall('.//node'):
#     phrase = node.find('.//phrase').text
#         #tmp1 =  re.sub(r"[A|a]1[C|c]", "", phrase)
#         #A1c_Value = re.sub(r"[^\d{1,2}\.?\d{0,1}]", "", tmp1)
#         #A1c_Flag = get_a1c_flag(A1c_Value)
#     literal = node.find('.//literal').text
#     Start = node.find('.//spanStart').text
#     Stop = node.find('.//spanStop').text
#     Node_ID = node.find('.//id').text
#     category = node.find('./category').text #This picks up target or modifier, not useful
#     try:
#         modified_by = node.find('.//modifyingNode').text
#     except:
#         modified_by = "None"
#     try:
#         modifying_category = node.find('.//modifyingCategory').text
#     except:
#         modifying_category = "None"
#     try:
#         node_modified = node.find('.//modifiedNode').text
#     except:
#         node_modified = "None"
#     output_array.append([text_df["Identifier"][1], Start, Stop, phrase, literal, Node_ID, modifying_category, modified_by, node_modified])


# In[14]:


output_array
train_df = pd.DataFrame(output_array, columns=("Identifier", "Start", "Stop", "Phrase", "Annotation_Type", "Node_ID", "Modifying_Category", "Modified_By", "Node_Modified"))
train_df


# In[15]:


# modifier_columns = train_df[train_df["Node_Modified"]!="None"]
# modifier_columns
modifier_columns = train_df[train_df["Node_Modified"]!="None"]
Diabetes_Results = train_df.drop(modifier_columns.index, axis = 0)
# print(len(Diabetes_Results))
# print(len(modifier_columns))


# In[16]:


modifier_columns


# In[17]:


Diabetes_Results


# In[18]:


node_locations = Diabetes_Results[["Start", "Stop", "Node_ID"]]
node_locations.head()


# In[19]:


node_locations.rename(columns={"Start":"Node_Start", "Stop":"Node_Stop", "Node_ID":"Node_Modified"}, inplace = True)
node_locations.head()


# In[20]:


modifier_columns = pd.merge(modifier_columns, node_locations, on='Node_Modified') #, how='right'
modifier_columns = modifier_columns[pd.notnull(modifier_columns['Identifier'])] # Drop the ones that weren't modifier nodes
modifier_columns


# In[21]:


modifier_columns["Distance"] = modifier_columns.apply(lambda x: max((int(x["Start"]) - int(x["Node_Stop"])), (int(x["Node_Start"])-int(x["Stop"]))), axis = 1)
modifier_columns


# In[22]:


modifier_columns.Annotation_Type.unique()


# In[23]:


distance_negation = 40
distance_other = 60
distance_hypothetical = 100
distance_type = 100

def out_of_range(anno_type, distance):
    if anno_type == " NOT " or anno_type == " DENIES ":
        if distance <= distance_negation:
            return "Keep"
        else:
            return "Discard"
    elif anno_type == " DIABETES_IN_OTHER ":
        if distance <= distance_other:
            return "Keep"
        else:
            return "Discard"
    elif anno_type == " HYPOTHETICAL_DIABETES ":
        if distance <= distance_hypothetical:
            return "Keep"
        else: 
            return "Discard"
    elif anno_type == " DIABETES_TYPE_1 " or anno_type == " DIABETES_TYPE_2 " or anno_type == " DIABETES_GESTATIONAL " or anno_type == " DIABETES_INSIPIDUS ":
        if distance <= distance_type:
            return "Keep"
        else:
            return "Discard"
    else:
        return "Didn't Work"
        
#Merged_Manual_and_Machine["Category"] = Merged_Manual_and_Machine.apply(lambda x: get_category(x["HbA1c"], x["A1c_Value"]), axis = 1)

#modifier_columns
#modifier_columns["Distance"] = modifier_columns.apply(lambda x: max((int(x["Start"]) - int(x["Node_Stop"])), (int(x["Node_Start"])-int(x["Stop"]))), axis = 1)


# In[24]:


modifier_columns["Keep"] = modifier_columns.apply(lambda x: out_of_range(x["Annotation_Type"], int(x["Distance"])), axis = 1)
modifier_columns


# In[ ]:





# In[25]:


modifier_columns = modifier_columns[modifier_columns["Keep"] == "Keep"]
modifier_columns


# Now I only have the modifiers that are within a specified distance (50 characters) of the node they modify.

# In[26]:


def get_negated(value):
    if value == " DENIES ":
        return "Negated_Diabetes"
    elif value == " NOT ":
        return "Negated_Diabetes"
    else:
        return ""
    
def get_other(value):
    if value == " DIABETES_IN_OTHER ":
        return "Diabetes_in_other"
    else:
        return ""
    
def get_type(value):
    if value == " DIABETES_TYPE_1 ":
        return "Diabetes_Type_1"
    elif value == " DIABETES_TYPE_2 ":
        return "Diabetes_Type_2"
    elif value == " DIABETES_GESTATIONAL ":
        return "Diabetes_Gestational"
    elif value == " INSIPIDUS ":
        return "Diabetes_Insipidus"
    else:
        return "No_Type"
    
    
    

def get_hypothetical(value):
    if value == " HYPOTHETICAL_DIABETES ":
        return "Diabetes_Hypothetical"
    else:
        return ""

modifier_columns["Negated"] = modifier_columns["Annotation_Type"].apply(get_negated)
modifier_columns["Diabetes_in_other"] = modifier_columns["Annotation_Type"].apply(get_other)
modifier_columns["Type"] = modifier_columns["Annotation_Type"].apply(get_type)
modifier_columns["Hypothetical"] = modifier_columns["Annotation_Type"].apply(get_hypothetical)


# In[27]:


modifier_columns


# In[28]:


def max_len(s):
    return max(s, key=len)
def max_val(s):
    return max(s, key=int)
subset = modifier_columns.groupby("Node_Modified").agg({'Diabetes_in_other': max_len, "Hypothetical": max_len, "Negated": max_len, "Type": max_len, "Distance": max_val})


# In[29]:


Diabetes_Results


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[30]:


subset = subset.reset_index()
subset.rename(columns={"Node_Modified":"Node_ID"}, inplace = True)
subset


# In[31]:


Final_table = pd.merge(Diabetes_Results, subset, on='Node_ID', how = "left") # how='right'
Final_table


# In[32]:


def get_new_type(anno_type, modify_type):
    if anno_type == " DMII " or anno_type == " DM2 " or anno_type == " T2DM " or anno_type == " NIDDM ":
        return "Diabetes_Type_2"
    elif anno_type == " DMI " or anno_type == " DM1 " or anno_type == " T1DM " or anno_type == " IDDM ":
        return "Diabetes_Type_1"
    elif anno_type == " GDM ":
        return "Diabetes_Gestational"
    else:
        if modify_type == "Diabetes_Type_1":
            return "Diabetes_Type_1"
        elif modify_type == "Diabetes_Type_2":
            return "Diabetes_Type_2"
        elif modify_type == "Diabetes_Gestational":
            return "Diabetes_Gestational"
        elif modify_type == "Diabetes_Insipidus":
            return "Diabetes_Insipidus"
        else:
            return "Diabetes_Type_Not_Specified"
        
        

Final_table["Diabetes_Type"] = Final_table.apply(lambda x: get_new_type(x["Annotation_Type"], x["Type"]), axis = 1)


# In[33]:


Final_table["Diabetes_Negated"] = Final_table.apply(lambda x: "Negated_Diabetes" if x["Negated"] == "Negated_Diabetes" else None, axis = 1)
Final_table["Diabetes_Hypothetical"] = Final_table.apply(lambda x: "Diabetes_Hypothetical" if x["Hypothetical"] == "Diabetes_Hypothetical" else None, axis = 1)
Final_table["Diabetes_In_Other_Person"] = Final_table.apply(lambda x: "Diabetes_in_other" if x["Diabetes_in_other"] == "Diabetes_in_other" else None, axis = 1)


Final_table


# In[34]:


Final_table.to_csv("Output_Files/Diabetes_mention_Test_Dataset.csv")


# There are too many of these that have two or more mentions per document. I am just going to get the counts of correct or incorrect using Excel and comparing them. 

# Ok, now for the contingency tables of picking up diabetes results
# This took too long to try it here, so I just ran it in Excel
# 
# 	Count	Recall	Precision	F-Value
# Diabetes Mention	106	100	100	100
# Hypothetical Mention	0	0	0	0
# Type not Specified	27	65.85	100	79.41
# Type 1	11	100	54.54	70.59
# Type 2	18	100	61.11	75.86
# Gestational	0	0	0	0
# Insipidus	0	0	0	0
# Negated Diabetes	1	100	100	100![image.png](attachment:image.png)
# 

# Now for the test data, and then deployment

# In[ ]:





# In[ ]:




