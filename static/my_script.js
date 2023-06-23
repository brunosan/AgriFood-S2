const SUPABASE_API_URL = 'https://afptefjaljkghrsmuyrf.supabase.co';
const SUPABASE_PUBLIC_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFmcHRlZmphbGprZ2hyc211eXJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE2Nzk1ODAxMzgsImV4cCI6MTk5NTE1NjEzOH0.sKRssTnTA3jhDROd1tTatEq_cKTk0Xw0E-n1AQZfuZ8';

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'
const supabase = createClient(SUPABASE_API_URL, SUPABASE_PUBLIC_KEY);

const maxLengthChar = 500;

$(document).ready(function () {
    console.log("ready!");
    $("#search-button").click(async function (event) {
        event.preventDefault();
        console.log("clicked!");
        $(".spinner").show();
        //$("#results").empty();
        try {
            //console.log("Initiating search...");
            const query = $('#search-input').val().trim();
            //console.log(query);
            const results = await fetchProjects(query);
            console.log(results);
            await displayResults(results);
            await updateSummary(results);
        } catch (error) {
            console.error('Error:', error);
            $(".spinner").hide();
            $("#results").html("<p>Error: " + error.message + "</p>");
        }
    });

    $("#sample-query-button").click(function () {
        const sampleQueries = [  
            "digital solutions and risk for optimizing fertilizer management",
            "digital tools and challenges for organic farming success",
            "digital solutions for climate change impact in agriculture",
            "digital solutions for food security challenges and opportunities",
            "best practices and benefits of using digital tools for crop rotation",
            "effective digital solutions for integrated pest management",
            "éxito y complejidades de herramientas digitales en la agricultura orgánica",
            "desafíos y oportunidades de soluciones digitales en la seguridad alimentaria",
            "mejores prácticas y beneficios del uso de herramientas digitales en la rotación de cultivos",
            "solutions numériques et risques pour optimiser la gestion des engrais en agriculture",
            "outils numériques et défis pour réussir l'agriculture biologique",
            "solutions numériques pour atténuer l'impact du changement climatique sur l'agriculture",
            "meilleures pratiques et avantages de l'utilisation d'outils numériques dans la rotation des cultures",
            "Digital solutions for fertilizer management and the risks involved",
            "Successful cases of using blockchain for supply chain transparency in agriculture",
            "How can satellite images be used to improve crop yield and mitigate risk?",
            "Challenges and opportunities of implementing IOT in precision agriculture",
            "Best practices for using digital tools for crop rotation",
            "Effective digital solutions for integrated pest management"
            ];
        

        const randomIndex = Math.floor(Math.random() * sampleQueries.length);
        $("#search-input").val(sampleQueries[randomIndex]);
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
      //console.log('Fetching projects...')
      const response = await $.ajax({
        method: 'POST',
        url: 'https://afptefjaljkghrsmuyrf.functions.supabase.co/s3-edge', // Update this URL to match your Edge Function endpoint
        contentType: 'application/json',
        headers: {
            'Authorization': `Bearer ${SUPABASE_PUBLIC_KEY}`,
          },
        data: JSON.stringify({ query }),
      });
      //console.log('Projects fetched:', response)
      return response;
    } catch (error) {
      console.error('Error fetching projects:', error);
      return [];
    }
  }
  

  async function displayResults(results) {
    $(".spinner").hide();
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
  
  function updateSummary(results) {
    const numResults = results.length;
    let summaryText = `Found ${numResults} matching results.`;
    const req = {'query': query, 'results': results};
    try {
      //console.log('Fetching projects...')
      const response = await $.ajax({
        method: 'POST',
        url: 'https://afptefjaljkghrsmuyrf.functions.supabase.co/s3-summary', // Update this URL to match your Edge Function endpoint
        contentType: 'application/json',
        headers: {
            'Authorization': `Bearer ${SUPABASE_PUBLIC_KEY}`,
          },
        data: JSON.stringify({ req }),
      });
      //console.log('response: ', response)
      return response;
    } catch (error) {
      console.error('Error fetching projects:', error);
      return [];
    }
  }
    document.getElementById("summary-section").innerHTML = summaryText;
  }
