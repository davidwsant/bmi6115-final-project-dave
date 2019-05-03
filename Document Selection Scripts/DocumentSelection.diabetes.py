import pymysql
import pandas as pd
import os

query = "SELECT subject_id, row_id, text, category FROM NOTEEVENTS where text like '%diabet%' order by rand() limit 100"

output_directory = "Diabetes"
if not os.path.exists(output_directory):
    os.mkdir(output_directory)

#--------------------------------------------------------------------
conn = pymysql.connect(host="mysql.chpc.utah.edu", \
    port=3306, \
    user="BMI6115",
    passwd=input_password_here, \
    db='mimic3')

docs = pd.read_sql(query, conn)
#--------------------------------------------------------------------

for index, row in docs.iterrows():
    subject_id = row.subject_id
    doc_id = row.row_id
    doc_text = row.text
    new_file_path_txt = output_directory+"/"+ str(doc_id) + ".txt"
    f=open(new_file_path_txt, "w")
    f.write(doc_text)
    f.close()
#--------------------------------------------------------------------
