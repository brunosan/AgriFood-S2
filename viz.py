#!/usr/bin/env python
# coding: utf-8

# In[1]:


import psycopg2
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="wb_s2_embeddings",
    user="s2",
    password="wb@s2"
)

from pgvector.psycopg2 import register_vector

register_vector(conn)

# Fetch embeddings in smaller batches
def fetch_embeddings(offset, limit):
    cur = conn.cursor()
    cur.execute("SELECT embedding FROM embeddings_openai OFFSET %s LIMIT %s", (offset, limit))
    rows = cur.fetchall()
    cur.close()
    return rows

# Convert the embeddings to a NumPy array
embeddings = []
offset = 0
limit = 1000  # Fetch 10 embeddings at a time
total_embeddings = 50000

while offset < total_embeddings:
    print("Fetching embeddings from {} to {}, of {}".format(offset, offset + limit,total_embeddings),end="\r")
    rows = fetch_embeddings(offset, limit)

    for row in rows:
        embeddings.append(np.array(row[0], dtype=np.float32))
    
    offset += limit

embeddings = np.array(embeddings)




# In[2]:


# Perform clustering using K-Means
print(f"Clustering {len(embeddings)} embeddings")
kmeans = KMeans(n_init='auto' , n_clusters=10, verbose=True, random_state=0).fit(embeddings)
labels = kmeans.labels_



# In[3]:


# Reduce the dimensionality of the embeddings using t-SNE
print("Reducing dimensionality of embeddings")
tsne = TSNE(n_components=2, random_state=0,verbose=True)
embeddings_tsne = tsne.fit_transform(embeddings)


# In[ ]:


print("Visualizing")
# Visualize the clusters using Matplotlib
plt.scatter(embeddings_tsne[:, 0], embeddings_tsne[:, 1], c=labels)
plt.show()

