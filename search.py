#!/usr/bin/env python
# coding: utf-8

# In[11]:


import psycopg2
import json
import numpy as np

#importing local modules
from tokenize_sentences2db import openai_embeddings,log


# Function to perform the search
def search(query, model, db_config,number_of_results):
    # Encode the query
    log("Encoding the query...")
    query_embedding = openai_embeddings(model,query)[0]
    log("Finding the most similar projects...")
    # Connect to the database
    with psycopg2.connect(**db_config) as conn:
        c = conn.cursor()

        # Search for the top projects by cosine similarity
        c.execute("""
            SELECT project_id, chunk, embedding <=> %s::VECTOR AS distance
            FROM embeddings_openai
            ORDER BY distance DESC
            LIMIT %s;
        """, (list(query_embedding), number_of_results))
        
        results = c.fetchall()
    log("Done! Found {} results.".format(len(results)))
    return results


# Define the database configuration
db_config = {
    'dbname': 'wb_s2_embeddings',
    'user': 's2',
    'password': 'wb@s2',
    'host': 'localhost',
    'port': 5432
}



# In[12]:


#convert this notebook to a python script
get_ipython().system('jupyter nbconvert --to script search.ipynb')


# In[13]:


model="text-embedding-ada-002"
number_of_results = 5

# Database configuration
db_config = {
    'dbname': 'wb_s2_embeddings',
    'user': 's2',
    'password': 'wb@s2',
    'host': 'localhost',
    'port': 5432
}

# Load the projects
with open("digital_agriculture_projects.json", "r") as f:
    projects = json.load(f)

# Define the query
query = "Satellite Remote sensing for agriculture"

# Perform the search
results = search(query, model, db_config,number_of_results)
results[::-1]
# Print the results
for project_id, chunk, distance in results:
    project = next((p for p in projects if ",".join(p["ids"]) == project_id), None)
    print(f"Project ID: {project_id}")
    print(f"Project title: {project['title']}")
    print(f"Project abstract: {project['abstract']}")
    print(f"Relevant snippet: {chunk}")
    print(f"Distance: {distance}")
    print("\n")


# In[14]:


query_embedding = openai_embeddings(model,query)


# In[18]:


len(query_embedding[0])


# In[16]:


query


# In[17]:


query_embedding


# In[ ]:




