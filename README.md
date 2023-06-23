# Quick explanation

The following steps will recreate the entire stack locally.

## Setup

1. `set_db.sh` install the right stuff and preps the postgres [on osx].

## Content retrieval and ingestion

### Projects

1. `get_project_data.ipynb` pulls from the WB API the project info related to a set of terms `related_terms`. It stores the results in `data/projects_metadata.json`

2. `get_fulltext.ipynb` downloads the flat text version of each P project in `data/projects_metadata.json` and stores it withi nthe the folder  `data/fulltext/`

### Use cases

1. `process_docx.ipynb` converts the docx file in `data` folder and stores them in `data/use_cases.json`

### Datasets

1. `process_datasets.ipynb` converts the excel file of dataset metadata in `data/datasets.xls` stores them in `data/datasets.json` TODO

### Ingestion into db

1. `tokenize_sentences2db.ipynb` iterates over each project, pulling the full text, chunking the text [and title, abstract, ...],gettign the embedd of each chunk, and storing it in the db.

## How to use

After running the step above, you can run the app with:

* `search.py` This is a sample search script that embeds the query, and then searches the db for the closest match, pulling the associated project info.
* A minimal web app. run `python app/app.py` and then go to `http://localhost:5000/` to see the app.

<img width="817" src="https://user-images.githubusercontent.com/434029/226652044-6dafb4d1-4439-4c70-b991-d4a377c6e3a2.png">

And these are the results:
<img width="1288" src="https://user-images.githubusercontent.com/434029/226652294-b6dd1c2a-77bb-4b13-9c16-95107f914609.png">

