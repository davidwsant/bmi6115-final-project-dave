#!/usr/bin/env python
# coding: utf-8

# # Extract the HbA1c Values and Diabetes Mentions from MIMIC-III dataset documents

# In this notebook I will be developing a python script for extracting the HbA1c values from text documents. The main thing I am looking for is going to be A1c followed by some value.
# 
# I will be using PyConText to accomplish this task. I have found when experimenting with PyConText on the MIMIC-III dataset that you sometimes get some very odd things that come back when you use modifiers with numbers, so I am going to use one regular expression to obtain both the mention of HbA1c and the value. I will then remove everything that is not the number to obtain the actual value. 
# 
# This notebook is almost identical to the previous notebook, except that in this notebook I am running this on the test dataset. 
# 

# First step, import PyConText and define the functions (taken from the PyConText github page and modified with help from Jeff Ferraro) so that I can run the actual text parsing. 

# In[16]:


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


os.getcwd()


# In[6]:


os.listdir("/Users/david/Documents/David_Sant/MIMIC Database/")


# In[7]:


noteevents = pd.read_csv("/Users/david/Documents/David_Sant/MIMIC Database/NOTEEVENTS.csv")
len(noteevents)


# In[61]:


len(noteevents)


# In[8]:


noteevents.head()


# In[9]:


text_df = noteevents[["ROW_ID", "TEXT"]]
text_df.columns = ["Identifier", "Text"]
text_df.head()


# In[18]:


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
output_array = []
count_of_bad_lines = 0
for i in range(len(text_df)):
    raw_text = text_df["Text"][i]
    remove_MIMIC_comments = re.sub(r"\[\*\*.*?\*\*\]", "", raw_text)
    remove_times = re.sub(r"\d{1,2}:\d{2}\s?P?A?\.?M\.?", "", remove_MIMIC_comments)
    cleaned_text = re.sub(r"\s{2,}", r" ", remove_times)
    
    context=markup_doc(cleaned_text)
    
    try:
        root = ElementTree.fromstring(context.getDocumentGraph().getXML())
    except ElementTree.ParseError:
        print("Input Line " + str(i) + " contains a character that is not valid in XML.")
        count_of_bad_lines += 1
        continue
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
print("Number of documents containing invalid text = ", count_of_bad_lines)
            
#output_array


# In[19]:


len(output_array)


# In[17]:


type(output_array)


# In[19]:


test_df = pd.DataFrame(output_array, columns=("Identifier", "Start", "Stop", "Phrase", "Annotation_Type", "A1c_Value", "A1c_Flag", "Node_ID", "Modifying_Category", "Modified_By", "Node_Modified"))
test_df.tail() # New dataframe name


# I had put in f/u as a modifier so that it would have a modifier file, but all of my targets require a value. In other words, if they put f/u and a value it is either a mistake typing or it refers to something else. As such, I can get rid of all of the modifier columns and the rows about node ID, modifying node, modified by, and node modified. 

# In[20]:


modifier_columns = test_df[test_df["Node_Modified"]!="None"]
len(modifier_columns)


# In[21]:


modifier_columns = test_df[test_df["Node_Modified"]!="None"]
A1c_Value_Results = test_df[["Identifier", "Start", "Stop", "Phrase", "Annotation_Type", "A1c_Value", "A1c_Flag"]].drop(modifier_columns.index, axis = 0)
len(A1c_Value_Results)


# In[22]:


A1c_Value_Results.head()


# In[17]:


A1c_Value_Results["A1c_Value"] = A1c_Value_Results["A1c_Value"].apply(pd.to_numeric)
A1c_Value_Results = A1c_Value_Results.groupby("Identifier").apply(lambda x: x.loc[x.A1c_Value.idxmax()])
A1c_Value_Results.to_csv("Output_Files/A1c_Results_Test_Dataset.csv") #New output file names
modifier_columns.to_csv("Output_Files/Modifier_Columns_to_A1c_Test_Dataset.csv") # I know this isn't needed, but I am going to save it for just in case


# In[18]:


A1c_Value_Results.head()


# In[23]:


A1c_Value_Results.to_csv("Output_Files/MIMIC_Results_A1c.csv")


# In[25]:


A1c_Value_Results.groupby("A1c_Flag").count()


# It looks like it read all the way through the entire dataset. I have A1c values from 10,515 documents.
# 7,160 of them have a good A1c (below 7.0%)
# 2,428 of them have moderate A1c value (between 7 and 10%)
# 927 of them have high A1c values above 10%. 

# In[26]:


my_targets=itemData.get_items('Yaml_Files/Diabetes_targets.yml')
my_modifiers=itemData.get_items('Yaml_Files/Diabetes_modifiers.yml')


# In[14]:



output_array = []
count_of_bad_lines = 0
for i in range(len(text_df)):
    raw_text = text_df["Text"][i]
    remove_MIMIC_comments = re.sub(r"\[\*\*.*?\*\*\]", "", raw_text)
    remove_times = re.sub(r"\d{1,2}:\d{2}\s?P?A?\.?M\.?", "", remove_MIMIC_comments)
    cleaned_text = re.sub(r"\s{2,}", r" ", remove_times)
    
    context=markup_doc(cleaned_text)
    try:
        root = ElementTree.fromstring(context.getDocumentGraph().getXML())
    except ElementTree.ParseError:
        print("Line Number "+str(i)+ " contains a character that is not valid in XML.")
        count_of_bad_lines += 1
        continue
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
print("Number of documents containing invalid text = ", count_of_bad_lines)


# This gives a parse error for both of these, but the number of documents containing mentions actually matches what I got using SQL, so I believe both systems have finished correctly. 

# In[28]:


output_array
train_df = pd.DataFrame(output_array, columns=("Identifier", "Start", "Stop", "Phrase", "Annotation_Type", "Node_ID", "Modifying_Category", "Modified_By", "Node_Modified"))
train_df


# In[29]:


len(train_df)


# In[30]:


modifier_columns = train_df[train_df["Node_Modified"]!="None"]
Diabetes_Results = train_df.drop(modifier_columns.index, axis = 0)
# print(len(Diabetes_Results))
# print(len(modifier_columns))
modifier_columns.head()


# In[31]:


node_locations = Diabetes_Results[["Start", "Stop", "Node_ID"]]
node_locations.head()


# In[32]:


node_locations.rename(columns={"Start":"Node_Start", "Stop":"Node_Stop", "Node_ID":"Node_Modified"}, inplace = True)
node_locations.head()


# In[33]:


modifier_columns = pd.merge(modifier_columns, node_locations, on='Node_Modified') #, how='right'
modifier_columns = modifier_columns[pd.notnull(modifier_columns['Identifier'])] # Drop the ones that weren't modifier nodes
len(modifier_columns)



# In[34]:


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
        


# In[37]:


modifier_columns["Distance"] = modifier_columns.apply(lambda x: max((int(x["Start"]) - int(x["Node_Stop"])), (int(x["Node_Start"])-int(x["Stop"]))), axis = 1)
modifier_columns
modifier_columns.head()


# In[38]:


modifier_columns["Keep"] = modifier_columns.apply(lambda x: out_of_range(x["Annotation_Type"], int(x["Distance"])), axis = 1)
modifier_columns.head()


# In[39]:


modifier_columns = modifier_columns[modifier_columns["Keep"] == "Keep"]
len(modifier_columns)


# In[40]:


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


# In[41]:


def max_len(s):
    return max(s, key=len)
def max_val(s):
    return max(s, key=int)
subset = modifier_columns.groupby("Node_Modified").agg({'Diabetes_in_other': max_len, "Hypothetical": max_len, "Negated": max_len, "Type": max_len, "Distance": max_val})


# In[42]:


subset = subset.reset_index()
subset.rename(columns={"Node_Modified":"Node_ID"}, inplace = True)
subset


# In[43]:


Final_table = pd.merge(Diabetes_Results, subset, on='Node_ID', how = "left") # how='right'
Final_table


# In[44]:


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


# In[45]:


Final_table["Diabetes_Negated"] = Final_table.apply(lambda x: "Negated_Diabetes" if x["Negated"] == "Negated_Diabetes" else None, axis = 1)
Final_table["Diabetes_Hypothetical"] = Final_table.apply(lambda x: "Diabetes_Hypothetical" if x["Hypothetical"] == "Diabetes_Hypothetical" else None, axis = 1)
Final_table["Diabetes_In_Other_Person"] = Final_table.apply(lambda x: "Diabetes_in_other" if x["Diabetes_in_other"] == "Diabetes_in_other" else None, axis = 1)


Final_table.head()


# In[53]:


Relevant_Columns = Final_table[["Identifier", "Start", "Stop", "Phrase", "Annotation_Type", "Distance",
                             "Diabetes_Type", "Diabetes_Negated", "Diabetes_Hypothetical", "Diabetes_In_Other_Person"]]




# In[ ]:





# In[54]:


Relevant_Columns.to_csv("Output_Files/MIMIC_Diabetes_mention.csv")


# In[55]:


Relevant_Columns.groupby("Diabetes_Type").count()


# In[56]:


Relevant_Columns.groupby("Diabetes_Negated").count()


# In[57]:


Relevant_Columns.groupby("Diabetes_Hypothetical").count()


# In[58]:



Relevant_Columns.groupby("Diabetes_In_Other_Person").count()


# In[59]:


len(Relevant_Columns)


# In[60]:


len(Relevant_Columns.groupby("Identifier"))


# OK, it finally ran!
# 
# Out of the 2,083,180 documents, 102,169 of them have a mention of diabetes. There are a total of 211,326 mentions of diabetes (just over 2 per document that mentions diabetes on average). Of these 211,326 mentions, 565 of them are gestational diabetes, 21,531 are Type 1 diabetes and 41,139 are Type 2 diabetes. I don't trust those numbers because in my test dataset it guessed less than 2/3 of the types correctly. Additionally, 8,842 of those mentions are negated, 6,140 are hypothetical and 3,468 are in a person other than the patient. Again, I think these numbers are underestimates, just like the types. 
# 
# As for the A1c, there are 10,515 documents that give an HbA1c value. 7,160 (68.1%) of them have a good A1c (7.0% or below). This is a good sign. Another 2,428 (23.1%) are fair management of diabetes and only 927 (8.8%) are high (above 10%, poor management of diabetes). This isn't bad at all. 

# In[ ]:




