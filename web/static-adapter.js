/* Browser-only transport for public synthetic fixtures. Never invokes local APIs. */
(() => {
  if (!window.FINAL_DATA?.summary.static_site) return;
  const fixtures = window.STATIC_FIXTURES;
  const events = window.FINAL_DATA.events;
  const respond = (value, status = 200) =>
    Promise.resolve(
      new Response(JSON.stringify(value), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    );
  window.STATIC_DEMO = {
    async fetch(path, options = {}) {
      const url = new URL(path, window.location.href);
      if (url.pathname === "/api/status")
        return respond({
          product: "ai-security-demo.v3",
          synthetic: true,
          static_site: true,
          model_ready: false,
          live_event_ids: [],
        });
      let body;
      try {
        body = JSON.parse(options.body || "{}");
      } catch {
        return respond({ error: "invalid_request" }, 400);
      }
      if (url.pathname === "/api/operate" || url.pathname === "/api/stop")
        return respond(
          {
            error: "static_execution_disabled",
            message: "線上展示不執行模型或網路處置。",
          },
          403,
        );
      const event = events.find((row) => row.event_id === body.event_id);
      if (!event) return respond({ error: "unknown_event" }, 400);
      if (url.pathname === "/api/export") {
        // Original Python JSON is preserved verbatim for ledger hash verification.
        return new Response(fixtures.exports[event.event_id], {
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.pathname !== "/api/retrieve")
        return respond({ error: "unknown_route" }, 404);
      const start = performance.now();
      const query = fixtures.queries[event.event_id];
      const ranked = fixtures.cases
        .map((row) => ({
          id: row.id,
          score: row.vector.reduce(
            (sum, value, index) => sum + value * query[index],
            0,
          ),
        }))
        .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
        .slice(0, 5);
      const expected = event.evidence.map((row) => row.case_id);
      if (ranked.some((row, index) => row.id !== expected[index]))
        return respond({ error: "fixture_rank_mismatch" }, 409);
      // Retain the frozen evidence/ledger bytes; actual browser ranking is checked above.
      return respond({
        ...event.result,
        replay_event: event,
        retrieval_ms: performance.now() - start,
        browser_ranking_verified: true,
      });
    },
  };
})();
