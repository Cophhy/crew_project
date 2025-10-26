"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE, createRun, getResult, getStatus } from "@/lib/api";

type Data = {
  status?: "queued" | "running" | "finished" | "failed";
  step?: "research" | "writing" | "editing";
  error?: string;
};

export default function OnePageApp() {
  const [question, setQuestion] = useState("");
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<Data>({});
  const [answer, setAnswer] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  // encerra SSE ao desmontar
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
      // 1) cria execução (envia a pergunta como "topic")
      const { run_id } = await createRun({
        topic: question,
        use_wikipedia: true,
      });
      setRunId(run_id);

      // 2) pega status atual (bootstrap)
      getStatus(run_id).then((s) => setStatus(s)).catch(() => {});

      // 3) abre SSE para progresso em tempo real
      const es = new EventSource(`${API_BASE}/runs/${run_id}/stream`);
      esRef.current = es;

      es.addEventListener("update", (ev) => {
        try {
          const d = JSON.parse((ev as MessageEvent).data) as Data;
          setStatus(d);
          if (d.status === "finished") {
            // 4) busca resposta final (Markdown)
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
        // opcional: reconectar/exibir toast
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
        <h1 className="text-2xl font-semibold">Pergunte para a IA</h1>
        <p className="text-sm opacity-70">
          Digite sua pergunta abaixo. Vamos acompanhar o status e te mostrar a
          resposta final.
        </p>
      </header>

      <form onSubmit={onSubmit} className="space-y-3">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ex.: Por que gatos laranja parecem mais sociáveis?"
          className="w-full border rounded-lg px-3 py-2 outline-none focus:ring"
        />
        <button
          disabled={busy}
          className="px-4 py-2 rounded-lg bg-black text-white disabled:opacity-50"
        >
          {busy ? "Enviando…" : "Perguntar"}
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
              <b>Situação:</b> {status.status || "—"}
              {status.step ? ` · passo: ${status.step}` : ""}
            </p>
            {status.error && (
              <p className="text-red-600">Erro: {status.error}</p>
            )}
          </div>
          <div className="w-full h-2 bg-gray-200 rounded">
            <div
              className="h-2 bg-black rounded transition-all"
              style={{
                width:
                  status.status === "finished"
                    ? "100%"
                    : status.step === "writing"
                    ? "66%"
                    : status.step === "research" || status.status === "running"
                    ? "33%"
                    : "10%",
              }}
            />
          </div>
        </section>
      )}

      {/* Resposta final */}
      <section className="space-y-2">
        <h2 className="font-medium">Resposta</h2>
        {answer ? (
          <textarea
            className="w-full h-96 border rounded-lg p-3 font-mono text-sm"
            value={answer}
            readOnly
          />
        ) : (
          <p className="text-sm opacity-70">
            {runId ? "Aguardando a resposta…" : "Envie uma pergunta para começar."}
          </p>
        )}
      </section>
    </main>
  );
}
