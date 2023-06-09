// Replace with your Supabase API URL and public key
const SUPABASE_API_URL = 'https://afptefjaljkghrsmuyrf.supabase.co';
const SUPABASE_PUBLIC_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFmcHRlZmphbGprZ2hyc211eXJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE2Nzk1ODAxMzgsImV4cCI6MTk5NTE1NjEzOH0.sKRssTnTA3jhDROd1tTatEq_cKTk0Xw0E-n1AQZfuZ8';
const OPENAI_PUBLIC_KEY = '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';

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'
const supabase = createClient(SUPABASE_API_URL, SUPABASE_PUBLIC_KEY);


$(document).ready(function() {
    $('#search-button').click(async function() {
        console.log('search button clicked')
        const query = $('#search-input').val();
        const embedding = await getEmbedding(query);
    
        if (embedding) {
        const results = await searchProjects(embedding);
        displayResults(results);
        } else {
        alert('Failed to fetch embedding for the query.');
        }
    });
});

async function getEmbedding(query) {
    try {
        console.log('getting embedding for query: ', query)
        const response = await $.ajax({
        method: 'POST',
        url: 'https://api.openai.com/v1/embeddings',
        headers: {
          'Authorization': `Bearer ${OPENAI_PUBLIC_KEY}`,
          'Content-Type': 'application/json',
        },
        data: JSON.stringify({
          input: "${query}",
          model: "text-embedding-ada-002"
        }),
      });
      const embedding = response.data[0].embedding;
      return embedding;
    } catch (error) {
      console.error('Error fetching embedding:', error);
      return null;
    }
  }

async function searchProjects(embedding) {
    const match_count = 5
    const similarity_threshold = 0.5
    try {
      const { data, error } = await supabase.rpc('match_documents', {
        match_count, 
        embedding, 
        similarity_threshold
      });
      if (error) {
        throw new Error(error.message);
      }
      return data;
    } catch (error) {
      console.error('Error fetching data:', error);
      return [];
    }
  }
  

function displayResults(results) {
  const container = $('#results');
  container.empty();

  for (const result of results) {
    const card = `
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">${result.title}</h5>
          <p class="card-text">${result.description}</p>
          <a href="${result.url}" class="card-link" target="_blank">View Project</a>
        </div>
      </div>
    `;

    container.append(card);
  }
}
