#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import os
import requests
import re


def clean_text(text):
    out = text.replace('\n', ' ').strip()
    out = re.sub(r'\.(\s*\.+)+', '.', out) # remove multiple dots
    out = re.sub(r'\bPage\s+\d+\s+of\s+\d+\b', '', out) # remove page numbers
    out = out.replace("'", "").replace('"', "").replace('"', "").replace('[', "").replace(']', "")
    out = " ".join(out.split())
    return out

def retrieve_full_text(document):
    # Define the local file path
    #print(document)
    filename = "-".join(document["ids"])
    local_file_path = os.path.join(text_folder, f"{filename}.txt")
    
    # Check if the local file exists
    if os.path.isfile(local_file_path):
        with open(local_file_path, "r") as file:
            document["full_text"] = file.read()
    else:
        text_url = document["txturl"]
        response = requests.get(text_url)
        
        if response.status_code == 200:
            document["full_text"] = clean_text(response.text)
            
            # Save the full_text to the local file
            with open(local_file_path, "w") as file:
                file.write(document["full_text"])
        else:
            print(f"Failed to download the text from the URL: {text_url}")
    return



# In[ ]:


if __name__ == "__main__":
    # Create a folder to store text files
    text_folder = "text_files"
    os.makedirs(text_folder, exist_ok=True)

    # Load the projects
    with open("digital_agriculture_projects.json", "r") as f:
        projects = json.load(f)

    i=0
    for project in projects:
        retrieve_full_text(project)
        i+=1
        print(f"Processed {i} projects out of {len(projects)}", end="\r")

