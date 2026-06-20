export async function onRequest(context) {
  return new Response(JSON.stringify({ message: "Proxy works!", method: context.request.method }), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}