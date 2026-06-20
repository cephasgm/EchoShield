// Proxies ALL /api/* requests to Render backend
export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  // Build the target URL on Render
  const targetUrl = 'https://echoshield-api-4x6z.onrender.com' + url.pathname + url.search;

  try {
    // Forward the request exactly, preserving method, headers, and body
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? await request.text() : undefined
    });

    // Return the backend response as-is
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Proxy error: ' + err.message }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}