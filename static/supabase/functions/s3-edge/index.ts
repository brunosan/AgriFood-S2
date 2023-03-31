
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';


export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const SUPABASE_API_URL = Deno.env.get('SUPABASE_API_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const OPENAI_PUBLIC_KEY = Deno.env.get('OPENAI_PUBLIC_KEY');


console.log(`Function "browser-with-cors" up and running!`)

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
    const reqJ = await req.json()
    const query = await reqJ['query'];
    const embedding = await getEmbedding(query);
    const results = await searchProjects(supabaseClient,embedding);

    return new Response(JSON.stringify(results), {
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


async function getEmbedding(query) {
  console.log('query', query);
  try {
    const OPENAI_PUBLIC_KEY = Deno.env.get('OPENAI_PUBLIC_KEY');
    console.log('OPENAI_SECRET_KEY', OPENAI_PUBLIC_KEY)
    const response = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_PUBLIC_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: `${query}`,
        model: "text-embedding-ada-002"
      }),
    });

    const data = await response.json();
    console.log('data', data);
    const embedding = data.data[0].embedding;
    return embedding;
  } catch (error) {
    console.error('Error fetching embedding:', error);
    return null;
  }
}

async function searchProjects(supabase,query_embedding) {
  const match_count = 5;
  const similarity_threshold = 0.1;
  try {
    let { data, error } = await supabase.rpc('s2', {
      match_count,
      query_embedding,
      similarity_threshold,
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
