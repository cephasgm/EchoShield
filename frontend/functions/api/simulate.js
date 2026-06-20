export async function onRequest(context) {
  // Only allow POST
  if (context.request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  const backendUrl = 'https://echoshield-api-4x6z.onrender.com/api/simulate';

  try {
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': context.request.headers.get('Authorization') || ''
      },
      body: JSON.stringify(await context.request.json())
    });

    // Read the response as text and pass it through
    const responseBody = await response.text();

    return new Response(responseBody, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
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