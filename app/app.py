from flask import Flask, render_template, request
import json
import numpy as np
import psycopg2
import openai
import mistune


import sys
import os
# Add the parent folder to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tokenize_sentences2db import openai_embeddings, log
from search import search, manage_results
# (Import other necessary functions and variables)

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

app = Flask(__name__)

# set Jinja options
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form.get("query")
        results = search(query, model, db_config, number_of_results)
        summary, _ = manage_results(projects, query, results)
        summary = mistune.markdown(summary)


        return render_template("results.html", query=query, summary=summary, results=results, projects=projects)
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
