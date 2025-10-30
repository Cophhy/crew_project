// lib/api.ts
export type Artifact = { kind: "markdown"|"text"|"json"|"file"|"image"; uri?: string|null; content?: string|null };
export type TaskResult = {
  name: string; status: "success"|"error";
  started_at: string; finished_at?: string|null; duration_seconds?: number|null;
  output_markdown?: string|null; observations: string[]; artifacts: Artifact[];
  metadata: Record<string, any>;
};
export type CrewOutput = {
  run_id: string; crew: string;
  started_at: string; finished_at?: string|null; duration_seconds?: number|null;
  inputs: Record<string, any>; tasks: TaskResult[];
  final_markdown?: string|null; output_file?: string|null; usage: Record<string, any>;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function createRun(topic: string): Promise<CrewOutput> {
  const r = await fetch(`${API}/runs`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ topic })});
  if (!r.ok) throw new Error(`POST /runs failed: ${r.status}`);
  return await r.json();
}

export function subscribeRun(runId: string, onDone: (out: CrewOutput)=>void) {
  const es = new EventSource(`${API}/runs/${runId}/stream`);
  // evento genérico
  es.onmessage = (ev) => { onDone(JSON.parse(ev.data)); es.close(); };
  // evento nomeado
  es.addEventListener("run.completed", (ev) => { onDone(JSON.parse((ev as MessageEvent).data)); es.close(); });
  es.onerror = (_e) => { es.close(); };
  return () => es.close();
}
