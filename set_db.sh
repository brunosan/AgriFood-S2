#!/bin/bash

brew install postgresql@14
brew services start postgresql
brew install pgvector/brew/pgvector
brew unlink pgvector 
brew link pgvector
brew services restart postgresql


# Replace with your desired username, password, and database name
USERNAME="s2"
PASSWORD="wb@s2"
DATABASE_NAME="wb_s2_embeddings"

# Log in to the PostgreSQL server and create a new user and database
psql postgres -c "CREATE ROLE $USERNAME WITH LOGIN PASSWORD '$PASSWORD' CREATEDB;"
psql postgres -c "ALTER USER $USERNAME WITH SUPERUSER;"

#delete database if exists
psql postgres -c "DROP DATABASE IF EXISTS $DATABASE_NAME;"

psql postgres -c "CREATE DATABASE $DATABASE_NAME WITH OWNER $USERNAME;"
psql postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql postgres -c "create index on embeddings_openai 
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);"
