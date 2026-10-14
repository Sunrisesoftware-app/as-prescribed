// The public demo's edge. asprescribed.sunrisesoftware.app is this Worker's custom domain, so
// Cloudflare holds the DNS record and the certificate. Every request goes through the Workers VPC
// binding APP to the app on the ultragravel machine (127.0.0.1:8300 over the machine's Cloudflare
// tunnel); responses, including a run's server-sent event stream, pass through as they arrive.
// The app only serves GET, and nothing about a session is logged here either.
const ORIGIN = "http://asprescribed.sunrisesoftware.app";

export default {
  async fetch(request, env) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("method not allowed", { status: 405, headers: { allow: "GET, HEAD" } });
    }
    const url = new URL(request.url);
    try {
      return await env.APP.fetch(new URL(url.pathname + url.search, ORIGIN), {
        method: request.method,
        headers: request.headers,
      });
    } catch {
      return new Response("The demo server is not reachable right now.", {
        status: 502,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }
  },
};
