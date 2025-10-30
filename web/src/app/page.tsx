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

  // Cleanup SSE when unmounting
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
      // 1) create a run (send the question as "topic")
      const { run_id } = await createRun({
        topic: question,
        use_wikipedia: true,
      });
      setRunId(run_id);

      // 2) fetch current status (bootstrap)
      getStatus(run_id).then((s) => setStatus(s)).catch(() => {});

      // 3) open SSE for real-time progress
      const es = new EventSource(`${API_BASE}/runs/${run_id}/stream`);
      esRef.current = es;

      es.addEventListener("update", (ev) => {
        try {
          const d = JSON.parse((ev as MessageEvent).data) as Data;
          setStatus(d);
          if (d.status === "finished") {
            // 4) fetch final answer (Markdown)
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
        // optional: reconnect/display toast
      });
    } catch (err: any) {
      setStatus({ status: "failed", error: err?.message || "Request failed" });
    } finally {
      setBusy(false);
    }
  }

  const shortId = runId ? runId.slice(0, 8) : "";

  return (
    <main className="min-h-screen max-w-4xl mx-auto p-8 space-y-8 bg-gray-100 rounded-xl shadow-xl">
      <header className="space-y-1 text-center">
        <h1 className="text-3xl font-semibold text-blue-800">Ask the AI</h1>
        <p className="text-sm text-gray-600">
          Type your question below. We'll track the status and show you the final answer.
        </p>
      </header>

      <form onSubmit={onSubmit} className="space-y-3">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="E.g., Why do orange cats seem more sociable?"
          className="w-full border border-gray-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-blue-400 transition duration-200"
        />
        <button
          disabled={busy}
          className="w-full px-4 py-3 rounded-lg bg-blue-600 text-white text-lg disabled:opacity-50 focus:ring-2 focus:ring-blue-400 transition duration-200"
        >
          {busy ? "Submitting…" : "Ask"}
        </button>
      </form>

      {/* Status */}
      {runId && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-medium text-lg text-blue-800">Status</h2>
            <span className="text-xs text-gray-500">ID {shortId}…</span>
          </div>

          {/* Loading Animation */}
          <div className="flex justify-center items-center space-x-3">
            {status.status === "running" && !busy && (
              <div className="flex space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce delay-200"></div>
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce delay-400"></div>
              </div>
            )}
          </div>

          {/* Display status and error */}
          <div className="text-sm">
            <p>
              <b>Status:</b> {status.status || "—"}
            </p>
            {status.error && (
              <p className="text-red-600 text-sm">Error: {status.error}</p>
            )}
          </div>
        </section>
      )}

      {/* Final Answer */}
      <section className="space-y-2">
        <h2 className="font-medium text-lg text-blue-800">Answer</h2>
        {answer ? (
          <textarea
            className="w-full h-96 border border-gray-300 rounded-lg p-3 font-mono text-sm bg-white shadow-md"
            value={answer}
            readOnly
          />
        ) : (
          <p className="text-sm text-gray-600">
            {runId ? "Waiting for the answer…" : "Send a question to start."}
          </p>
        )}
      </section>
    </main>
  );
}
