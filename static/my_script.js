const SUPABASE_API_URL = 'https://afptefjaljkghrsmuyrf.supabase.co';
const SUPABASE_PUBLIC_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFmcHRlZmphbGprZ2hyc211eXJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE2Nzk1ODAxMzgsImV4cCI6MTk5NTE1NjEzOH0.sKRssTnTA3jhDROd1tTatEq_cKTk0Xw0E-n1AQZfuZ8';

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'
const supabase = createClient(SUPABASE_API_URL, SUPABASE_PUBLIC_KEY);

const maxLengthChar = 500;

$(document).ready(function () {
    $('#search-button').click(async function () {
        console.log('search button clicked');
        const query = $('#search-input').val().trim();
        const results = await fetchProjects(query);
        await displayResults(results);
      });
});



function truncateText(text, maxLength = maxLengthChar) {
    return text.substring(0, maxLength) + '...';

}

function formatDate(dateString) {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
    const year = date.getFullYear();

    return `${month}/${day}/${year}`;
}

async function fetchProjects(query) {
    try {
      const response = await $.ajax({
        method: 'POST',
        url: 'https://afptefjaljkghrsmuyrf.functions.supabase.co/s3-edge', // Update this URL to match your Edge Function endpoint
        contentType: 'application/json',
        headers: {
            'Authorization': `Bearer ${SUPABASE_PUBLIC_KEY}`,
          },
        data: JSON.stringify({ query }),
      });
  
      return response;
    } catch (error) {
      console.error('Error fetching projects:', error);
      return [];
    }
  }
  

  async function displayResults(results) {
    const container = $('#results');
    container.empty();
  
    for (const result of results) {
      const { data: data, error } = await supabase
        .from('projects')
        .select('title, url, abstract, txturl, date, authors, keywords')
        .eq('project_id', result.project_id)
  
      if (error) {
        console.error('Error fetching project data:', error);
        continue;
      }
      const project = data[0];
  
      const card = `
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">${project.title}</h5>
            <p class="card-subtitle mb-2 text-muted">Snippet: ${truncateText(result.chunk)}</p>
            <p class="card-text"><bold>Project Abstract:</bold> ${truncateText(project.abstract)}</p>
            <p class="card-authors"><strong>Authors:</strong> ${project.authors}</p>
            <p class="card-date"><strong>Date:</strong> ${formatDate(project.date)}</p>
            <p class="card-keywords"><strong>Keywords:</strong> ${truncateText(project.keywords)}</p>
            <p class="card-date"><strong>Similarity:</strong> ${result.similarity.toFixed(2)}</p>
            <a href="${project.url}" class="card-link" target="_blank">View Project</a>
            <a href="${project.txturl}" class="card-link" target="_blank">Read Full Text</a>
          </div>
        </div>
      `;
  
      container.append(card);
    }
  }
  
