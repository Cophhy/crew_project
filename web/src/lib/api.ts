export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export type RunCreateReq = { topic: string; use_wikipedia?: boolean };
export type RunCreateRes = { run_id: string };
export type RunStatus = {
  run_id: string;
  status: "queued" | "running" | "finished" | "failed";
  step?: "research" | "writing" | "editing";
  error?: string;
};
export type RunResult = { run_id: string; markdown: string };

export async function createRun(body: RunCreateReq): Promise<RunCreateRes> {
  const r = await fetch(`${API_BASE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`POST /runs ${r.status}`);
  return r.json();
}

export async function getStatus(runId: string): Promise<RunStatus> {
  const r = await fetch(`${API_BASE}/runs/${runId}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /runs/${runId} ${r.status}`);
  return r.json();
}

export async function getResult(runId: string): Promise<RunResult> {
  const r = await fetch(`${API_BASE}/runs/${runId}/result`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /runs/${runId}/result ${r.status}`);
  return r.json();
}
