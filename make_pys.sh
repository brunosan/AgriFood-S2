#!/bin/bash

jupyter nbconvert --to script tokenize_sentences2db.ipynb
jupyter nbconvert --to script search.ipynb
jupyter nbconvert --to script get_full_text.ipynb