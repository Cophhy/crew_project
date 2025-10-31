"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE, createRun, getResult, getStatus } from "@/lib/api";

type Data = {
  status?: "queued" | "running" | "finished" | "failed";
  error?: string;
};

export default function OnePageApp() {
  const [question, setQuestion] = useState("");  // pergunta do user
  const [runId, setRunId] = useState<string | null>(null);  // ID
  const [status, setStatus] = useState<Data>({});  // status
  const [answer, setAnswer] = useState<string>("");  // resposta gerada
  const [busy, setBusy] = useState(false);  // se a aplicacao esta ocupada processando
  const esRef = useRef<EventSource | null>(null);  // ref para sse

  // Fecha a SSE quando o componente for desmontado
  useEffect(() => {
    return () => {
      if (esRef.current) esRef.current.close();  
    };
  }, []);

  // submeter a pergunta
  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();  
    if (!question.trim()) return; 
    setBusy(true);  // ocupado enquanto processa
    setAnswer("");  // Limpa a resposta anterior
    setStatus({ status: "queued" }); 
    setRunId(null);  

    try {
      const { run_id } = await createRun({
        topic: question,
        use_wikipedia: true,
      });
      setRunId(run_id);  

      // status inicial
      getStatus(run_id).then((s) => setStatus(s)).catch(() => {});

      // SSE para tempo real
      const es = new EventSource(`${API_BASE}/runs/${run_id}/stream`);
      esRef.current = es;

      // att status da exec
      es.addEventListener("update", (ev) => {
        try {
          const d = JSON.parse((ev as MessageEvent).data) as Data;
          setStatus(d);  
          if (d.status === "finished") {
          
            getResult(run_id)
              .then((r) => setAnswer(r.markdown))
              .catch(() => {});
            es.close();  // Fecha SSE quando concluido
          }
          if (d.status === "failed") {
            es.close();  // Fecha SSE se falhar
          }
        } catch {
        }
      });

      es.addEventListener("error", () => {
      });
    } catch (err: any) {
      setStatus({ status: "failed", error: err?.message || "Request failed" });  
    } finally {
      setBusy(false);  
    }
  }

  const shortId = runId ? runId.slice(0, 8) : "";  // primeiros 8 caracteres do ID da exec

  return (
    <main className="min-h-dvh max-w-3xl mx-auto p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Ask the AI</h1>
        <p className="text-sm opacity-70">
          Type your question below. We'll track the status and show you the final answer.
        </p>
      </header>

      <form onSubmit={onSubmit} className="space-y-3">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}  
          placeholder="E.g., Why do orange cats seem more social?"
          className="w-full border rounded-lg px-3 py-2 outline-none focus:ring"
        />
        <button
          disabled={busy}  
          className="px-4 py-2 rounded-lg bg-black text-white disabled:opacity-50"
        >
          {busy ? "Sending…" : "Ask"}  {/* Altera o texto do botão conforme o estado de "busy" */}
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
              <b>Status:</b> {status.status || "—"}  {/* status */}
            </p>
            {status.error && (
              <p className="text-red-600">Error: {status.error}</p>  
            )}
          </div>
          <div className="w-full h-2 bg-gray-200 rounded">
            <div
              className={`h-2 rounded transition-all ${
                status.status === "finished"
                  ? "bg-black"  
                  : "bg-black animate-progress-bar"  
              }`}
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

      {/* Resposta final */}
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
            {runId ? "Waiting for the answer…" : "Send a question to start."}
          </p>
        )}
      </section>
    </main>
  );
}
