#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import psycopg2
import json
import numpy as np
import openai
import configparser

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
            ORDER BY distance ASC
            LIMIT %s;
        """, (list(query_embedding), number_of_results))
        
        results = c.fetchall()
    log("Done! Found {} results.".format(len(results)))
    return results

# Function to generate a summary using OpenAI
def generate_summary(question, context_sections, query):
    prompt = f"""
    You are a World Bank expert with access to all Bank projects who loves
    to help people! Given the following Question and top answers, provide a
    summary of the top results that answers the question and refers to the
    results, whith links, outputted in markdown format. Use only the provided 
    results to create your answer.
    If you are unsure say why and offer a similar question that might
    point the users and you in the right direction.

    Question:
    {query}

    Top hits ordered by cosine similarity of the snippet embedding to the query embedding:
    {context_sections}
    """

    # In production, we should handle possible errors
    completion_response = openai.Completion.create(
            prompt=prompt,
            temperature=0,
            max_tokens=512,  # Choose the max allowed tokens in completion
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            model='text-davinci-003')

    return completion_response.choices[0].text.strip()

def manage_results(projects,query,results):
    # Create a string with the results
    results_text = ""
    for project_id, chunk, distance in results:
        project = None
        for p in projects:
            if ",".join(p["ids"]) == project_id:
                project = p
                break
        results_text += f"\nProject ID: {project_id}\n"
        results_text += f"Project title: {project['title']}\n"
        results_text += f"Project url: {project['url']}\n"
        results_text += f"Project abstract: {project['abstract']}\n"
        results_text += f"Relevant snippet: {chunk}\n"
        results_text += f"Distance: {distance}\n"

    # Generate the summary using OpenAI
    log("Generating summary...")
    summary = generate_summary(query, results_text, query)
    return summary, results_text


# In[ ]:


if __name__ == "__main__":
    model="text-embedding-ada-002"
    number_of_results = 5

    # Database configuration
    config = configparser.ConfigParser()
    config.read('config.ini')

    db_config = {
        'dbname':   config['DB']['dbname'],
        'user':     config['DB']['user'],
        'password': config['DB']['password'],
        'host':     config['DB']['host'],
        'port':     int(config['DB']['port'])
    }  

    # Load the projects
    with open("digital_agriculture_projects.json", "r") as f:
        projects = json.load(f)
    # Define the query
    query = "Main challengues and oportunities to deploy Satellite Remote sensing for fertilizer management."
    # Perform the search
    results = search(query, model, db_config,number_of_results)
    summary, results_text = manage_results(projects,query,results)
    # Print the summary
    log(summary)
    log(results_text)


# In[ ]:




