#!/usr/bin/env python
# coding: utf-8

# In[8]:


import psycopg2
import json
import numpy as np
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

number_of_results = 5

# Database configuration
db_config = {
    'dbname': 'wb_s2_embeddings',
    'user': 's2',
    'password': 'wb@s2',
    'host': 'localhost',
    'port': 5432
}

model = SentenceTransformer('sentence-transformers/paraphrase-mpnet-base-v2')

# Load the projects
with open("digital_agriculture_projects.json", "r") as f:
    projects = json.load(f)

# Function to perform the search
def search(query, model, db_config):
    # Encode the query
    query_embedding = model.encode([query])[0]
    query_embedding = [float(value) for value in query_embedding]

    
    # Connect to the database
    with psycopg2.connect(**db_config) as conn:
        c = conn.cursor()

        # Search for the top projects by cosine similarity
        c.execute("""
            SELECT project_id, chunk, embedding <-> %s::VECTOR AS distance
            FROM embeddings
            ORDER BY distance DESC
            LIMIT %s;
        """, (list(query_embedding), number_of_results))
        
        results = c.fetchall()
    
    return results

# Initialize the model
model = SentenceTransformer('sentence-transformers/paraphrase-mpnet-base-v2')

# Define the database configuration
db_config = {
    'dbname': 'wb_s2_embeddings',
    'user': 's2',
    'password': 'wb@s2',
    'host': 'localhost',
    'port': 5432
}



# In[9]:


#convert this notebook to a python script
get_ipython().system('jupyter nbconvert --to script search.ipynb')


# In[14]:


# Define the query
query = "Main challengues for Climate Smart Agriculture"

# Perform the search
results = search(query, model, db_config)
# Print the results
for project_id, chunk, distance in results:
    project = next((p for p in projects if ",".join(p["ids"]) == project_id), None)
    print(f"Project ID: {project_id}")
    print(f"Project title: {project['title']}")
    print(f"Project abstract: {project['abstract']}")
    print(f"Relevant snippet: {chunk}")
    print(f"Distance: {distance}")
    print("\n")


# In[ ]:




