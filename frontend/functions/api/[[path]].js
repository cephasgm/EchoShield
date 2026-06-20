export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  const targetUrl = 'https://echoshield-api-4x6z.onrender.com' + url.pathname + url.search;

  // Build a clean set of headers to forward
  const headers = {};
  for (const [key, value] of request.headers.entries()) {
    // Only forward necessary headers; skip host and cf-specific headers
    if (['content-type', 'authorization', 'accept', 'accept-encoding', 'user-agent'].includes(key.toLowerCase())) {
      headers[key] = value;
    }
  }

  const init = {
    method: request.method,
    headers: headers
  };

  // Attach body only for methods that support it
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.text();
  }

  try {
    const response = await fetch(targetUrl, init);
    const body = await response.text();

    return new Response(body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
        'Access-Control-Allow-Origin': '*' // although not strictly needed, it's safe
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Proxy error: ' + err.message }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}