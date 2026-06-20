export async function onRequest(context) {
  // Only allow POST
  if (context.request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    // Forward the request to the Render backend
    const backendUrl = 'https://echoshield-api-4x6z.onrender.com/api/simulate';
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': context.request.headers.get('Content-Type') || 'application/json',
        'Authorization': context.request.headers.get('Authorization') || ''
      },
      body: await context.request.text()
    });

    // Return the backend response unchanged
    const data = await response.text();
    return new Response(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Proxy error: ' + err.message }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}