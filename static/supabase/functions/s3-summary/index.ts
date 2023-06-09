// Follow this setup guide to integrate the Deno language server with your editor:
// https://deno.land/manual/getting_started/setup_your_environment
// This enables autocomplete, go to definition, etc.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';


export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const SUPABASE_API_URL = Deno.env.get('SUPABASE_API_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const OPENAI_PUBLIC_KEY = Deno.env.get('OPENAI_PUBLIC_KEY');



console.log("Hello from Functions!")

serve(async (req) => {
  // This is needed if you're planning to invoke your function from a browser.
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      SUPABASE_API_URL,
      SUPABASE_SERVICE_ROLE_KEY,
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    );
    console.log('req', req);
    const reqJ = await req.json()
    console.log('reqJ', reqJ);
    const { summary } = await generateSummary(reqJ)
    
    return new Response(JSON.stringify(summary), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})


async function generateSummary(req) {
  console.log('Generate Summary req: ', req);
  const query = await req['query']; 
  const results = req['results'];
  console.log('query', query);
  console.log('results', results);
  const resultText = results
    .map((result, index) => `Result ${index + 1}: ${result.title}`)
    .join('. ');

  // Combine the query and result text
  const combinedText = `Query: ${query}. ${resultText}`;

  try {
    const OPENAI_PUBLIC_KEY = Deno.env.get('OPENAI_PUBLIC_KEY');
    const response = await fetch('https://api.openai.com/v1/engines/davinci-codex/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_PUBLIC_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: `Generate a summary for the following information: ${combinedText}`,
        max_tokens: 100, // Adjust this value based on the desired summary length
        n: 1,
        stop: null,
        temperature: 0.5,
      }),
    });

    const data = await response.json();
    const summary = data.choices && data.choices[0].text.trim();
    return summary;
  } catch (error) {
    console.error('Error fetching summary:', error);
    return null;
  }
}


// To invoke:
// curl -i --location --request POST 'http://localhost:54321/functions/v1/' \
//   --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0' \
//   --header 'Content-Type: application/json' \
//   --data '{"name":"Functions"}'
