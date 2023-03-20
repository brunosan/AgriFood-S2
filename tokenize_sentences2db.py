#!/usr/bin/env python
# coding: utf-8

# In[1]:


#if needed 
#!set_db.sh


# In[90]:


import re
import numpy as np
import psycopg2
from psycopg2.extensions import register_adapter, AsIs
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import os, json
from nltk.tokenize import sent_tokenize,word_tokenize
import datetime
import os
import openai
import time

openai.api_key = os.getenv("OPENAI_API_KEY")

MAX_TOKENS = 100
EMBEDDING_SIZE = 1536
special_splitter="#!#" #used to always split text into chunks on that token.



#cross project import
from get_full_text import clean_text,retrieve_full_text 



def log(text, end="\n"):
    print(f"{datetime.datetime.now().strftime('%H:%M:%S')} - {text}", end=end)
import re
from typing import List

def split_sentence(sentence: str, max_length: int=MAX_TOKENS) -> List[str]:
    comma_parts = sentence.split(', ')
    chunks = []
    current_chunk = []

    for part in comma_parts:
        words = part.split()

        if len(current_chunk) + len(words) + 1 <= max_length:  # +1 for space between comma parts
            current_chunk.extend(words)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

            if len(words) > max_length:
                for i in range(0, len(words), max_length):
                    sub_chunk = words[i:i + max_length]
                    chunks.append(" ".join(sub_chunk))
            else:
                current_chunk.extend(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def chunk_splitter(input_string: str, max_length: int = MAX_TOKENS, special_string: str = special_splitter) -> List[str]:

    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', input_string)
    flat_sentences = []
    for sentence in sentences:
        flat_sentences.extend(sentence.split(special_string))
    sentences = flat_sentences

    #deal with sentences that are longer than max_length, by splitting them into max chunks of ","
    sentences = [split_sentence(sentence, max_length) for sentence in sentences]
    sentences = [item for sublist in sentences for item in sublist]  # Flatten the list of sentences

    chunks = []
    chunk = []

    for sentence in sentences:
        words = sentence.split()
        
        if len(chunk) + len(words) + 1 <= max_length:  # +1 for space between sentences
            chunk.extend(words)
        else:
            #adding words to the chunk would exceed the max length
            if chunk:
                chunks.append(" ".join(chunk))
                chunk = []    
            chunk.extend(words)
    #last chunk
    if chunk:
        chunks.append(" ".join(chunk))

    return chunks

# Add these lines to register np.ndarray for psycopg2
def adapt_np_array(array):
    return AsIs(np.array(array).tolist())
register_adapter(np.ndarray, adapt_np_array)

def fetch_openai(model,chunk):
    response = openai.Embedding.create(
        input=chunk,
        model=model
    )
    return response

def openai_embeddings(model,chunks):
    i=0
    sentence_embeddings =[]
    for chunk in chunks:
        i+=1
        if i % 50 == 0:
            log(f"Doing -> Embedding chunk: {i} of {len(chunks)}. Chunk:\n\t {chunk}...")
        
        try:
            response = fetch_openai(model,chunk)
        except Exception as e:
            log(f"Error -> Retry in 5 seconds.")
            time.sleep(5)
            response = fetch_openai(model,chunk)
        sentence_embeddings.append(response['data'][0]['embedding'])
    return sentence_embeddings

def project_exists(project_id, conn):
    c = conn.cursor()
    c.execute("SELECT 1 FROM embeddings_openai WHERE project_id = %s LIMIT 1", (project_id,))
    return c.fetchone() is not None



# Function to process a project
def process_project(thread_id, project):
    retrieve_full_text(project)
    project["keywords"] = project["keywords"].replace(";", ". ").replace(",", ". ")
    project["full_text"] = "Title: "    + project["title"] + special_splitter +\
                           "Abstract: " + project["abstract"] + special_splitter +\
                           "Fullt text: " + project["full_text"]
                           #"Keywords: " + project["keywords"] + special_splitter #bad results
    project["full_text"] = clean_text(project["full_text"])

    local_counter = 1
    with psycopg2.connect(**db_config) as conn:
        project_id = ",".join(project['ids'])
        if project_exists(project_id, conn):
            log(f"Skipping -> Project {project['title']} already exists in the table.")
            return
        chunks = chunk_splitter(project["full_text"])
        log(f"Starting -> {len(chunks)} chunks for project {project['title']}.")
        sentence_embeddings = openai_embeddings(model,chunks)
        c = conn.cursor()
        for chunk, embedding in zip(chunks, sentence_embeddings):
            unique_id = thread_id * 1000000 + local_counter
            chunk = chunk.replace('\x00', ' ')  # Replace NUL characters with a space
            c.execute("INSERT INTO embeddings_openai (id, project_id, chunk, embedding) VALUES (%s, %s, %s, %s::VECTOR)", (unique_id, project_id, chunk, embedding))
            local_counter += 1
        conn.commit()
        log(f"Done -> Project {project['title']}")





# In[8]:


#convert notebook to python
get_ipython().system('jupyter nbconvert --to script tokenize_sentences2db.ipynb')


# In[91]:


reset_db = True #drop table and create new one

# Database configuration
db_config = {
    'dbname': 'wb_s2_embeddings',
    'user': 's2',
    'password': 'wb@s2',
    'host': 'localhost',
    'port': 5432
}

model="text-embedding-ada-002"



# Create a folder to store text files
text_folder = "text_files"

with psycopg2.connect(**db_config) as conn:
    c = conn.cursor()
    if reset_db:
        log("Resetting database.")
        c.execute("DROP TABLE IF EXISTS embeddings_openai;")
        c.execute("DROP SEQUENCE IF EXISTS embeddings_openai_id_seq;")
    c.execute('CREATE SEQUENCE IF NOT EXISTS embeddings_openai_id_seq;')
    c.execute(f'CREATE TABLE IF NOT EXISTS embeddings_openai (id INTEGER PRIMARY KEY DEFAULT nextval(\'embeddings_openai_id_seq\'), project_id TEXT, chunk TEXT, embedding VECTOR({EMBEDDING_SIZE}));')
    
    conn.commit()


# Load the projects
with open("digital_agriculture_projects.json", "r") as f:
    projects = json.load(f)


# Initialize counter and lock
counter = 1
counter_lock = Lock()

# Process texts and save embeddings into the database using 8 threads
with ThreadPoolExecutor(max_workers=2) as executor:
    for i, _ in enumerate(executor.map(process_project, range(len(projects[:3])), projects[:])):
        pass


# In[85]:


import re
from typing import List

def split_sentence(sentence: str, max_length: int) -> List[str]:
    comma_parts = sentence.split(', ')
    chunks = []
    current_chunk = []

    for part in comma_parts:
        words = part.split()

        if len(current_chunk) + len(words) + 1 <= max_length:  # +1 for space between comma parts
            current_chunk.extend(words)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

            if len(words) > max_length:
                for i in range(0, len(words), max_length):
                    sub_chunk = words[i:i + max_length]
                    chunks.append(" ".join(sub_chunk))
            else:
                current_chunk.extend(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def chunk_string(input_string: str, max_length: int, special_string: str = "#!#") -> List[str]:

    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', input_string)
    flat_sentences = []
    for sentence in sentences:
        flat_sentences.extend(sentence.split(special_string))
    sentences = flat_sentences

    #deal with sentences that are longer than max_length, by splitting them into max chunks of ","
    sentences = [split_sentence(sentence, max_length) for sentence in sentences]
    sentences = [item for sublist in sentences for item in sublist]  # Flatten the list of sentences

    chunks = []
    chunk = []

    for sentence in sentences:
        words = sentence.split()
        
        if len(chunk) + len(words) + 1 <= max_length:  # +1 for space between sentences
            chunk.extend(words)
        else:
            #adding words to the chunk would exceed the max length
            if chunk:
                chunks.append(" ".join(chunk))
                chunk = []    
            chunk.extend(words)
    #last chunk
    if chunk:
        chunks.append(" ".join(chunk))

    return chunks

# Example usage
with open("digital_agriculture_projects.json", "r") as f:
    projects = json.load(f)
project=projects[2]
retrieve_full_text(project)
project["full_text"]="words words words words words words words, in sentence. another sentence. "+project["full_text"]
chunks = chunk_string(project["full_text"], max_length=50, special_string="#!#")
print("OUTOUT:")
for chunk in chunks[20:30]:
    print(len(chunk.split(" ")),chunk)


# In[78]:





# In[ ]:




