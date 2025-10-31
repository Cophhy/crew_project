"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE, createRun, getResult, getStatus } from "@/lib/api";

type Data = {
  status?: "queued" | "running" | "finished" | "failed";
  error?: string;
};

export default function OnePageApp() {
  const [question, setQuestion] = useState("");
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<Data>({});
  const [answer, setAnswer] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  // Close SSE when component unmounts
  useEffect(() => {
    return () => {
      if (esRef.current) esRef.current.close();
    };
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setAnswer("");
    setStatus({ status: "queued" });
    setRunId(null);

    try {
      // 1) Create run (send the question as "topic")
      const { run_id } = await createRun({
        topic: question,
        use_wikipedia: true,
      });
      setRunId(run_id);

      // 2) Get current status (bootstrap)
      getStatus(run_id).then((s) => setStatus(s)).catch(() => {});

      // 3) Open SSE for real-time progress
      const es = new EventSource(`${API_BASE}/runs/${run_id}/stream`);
      esRef.current = es;

      es.addEventListener("update", (ev) => {
        try {
          const d = JSON.parse((ev as MessageEvent).data) as Data;
          setStatus(d);
          if (d.status === "finished") {
            // 4) Fetch final answer (Markdown)
            getResult(run_id)
              .then((r) => setAnswer(r.markdown))
              .catch(() => {});
            es.close();
          }
          if (d.status === "failed") {
            es.close();
          }
        } catch {
          /* ignore parse */
        }
      });

      es.addEventListener("error", () => {
        // Optional: reconnect/display toast
      });
    } catch (err: any) {
      setStatus({ status: "failed", error: err?.message || "Request failed" });
    } finally {
      setBusy(false);
    }
  }

  const shortId = runId ? runId.slice(0, 8) : "";

  return (
    <main className="min-h-dvh max-w-3xl mx-auto p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Ask the AI</h1>
        <p className="text-sm opacity-70">
          Enter your question below. We'll track the status and show you the
          final answer.
        </p>
      </header>

      <form onSubmit={onSubmit} className="space-y-3">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Why do orange cats seem more sociable?"
          className="w-full border rounded-lg px-3 py-2 outline-none focus:ring"
        />
        <button
          disabled={busy}
          className="px-4 py-2 rounded-lg bg-black text-white disabled:opacity-50"
        >
          {busy ? "Submitting…" : "Ask"}
        </button>
      </form>

      {/* Status */}
      {runId && (
        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="font-medium">Status</h2>
            <span className="text-xs text-gray-500">ID {shortId}…</span>
          </div>
          <div className="text-sm">
            <p>
              <b>Status:</b> {status.status || "—"}
            </p>
            {status.error && (
              <p className="text-red-600">Error: {status.error}</p>
            )}
          </div>
          <div className="w-full h-2 bg-gray-200 rounded">
            <div
              className="h-2 bg-black rounded transition-all"
              style={{
                width:
                  status.status === "finished"
                    ? "100%"
                    : status.status === "running"
                    ? "50%"
                    : "10%",
              }}
            />
          </div>
        </section>
      )}

      {/* Final Answer */}
      <section className="space-y-2">
        <h2 className="font-medium">Answer</h2>
        {answer ? (
          <textarea
            className="w-full h-96 border rounded-lg p-3 font-mono text-sm"
            value={answer}
            readOnly
          />
        ) : (
          <p className="text-sm opacity-70">
            {runId ? "Waiting for the answer…" : "Submit a question to start."}
          </p>
        )}
      </section>
    </main>
  );
}
