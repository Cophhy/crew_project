// page.tsx (ou componente)
"use client";
import { useState } from "react";
import { createRun, subscribeRun, CrewOutput } from "@/lib/api";

export default function Home() {
  const [topic, setTopic] = useState("");
  const [out, setOut] = useState<CrewOutput|null>(null);
  const [loading, setLoading] = useState(false);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    const first = await createRun(topic);   // já é JSON Pydantic
    setOut(first);
    // escuta o stream (receberá o mesmo CrewOutput final e fecha)
    subscribeRun(first.run_id, (finalOut) => setOut(finalOut));
    setLoading(false);
  }

  return (
    <main className="p-6 max-w-3xl mx-auto">
      <form onSubmit={run} className="flex gap-2">
        <input className="border rounded px-3 py-2 flex-1" value={topic} onChange={e=>setTopic(e.target.value)} placeholder="Topic..." />
        <button className="bg-black text-white rounded px-4 py-2" disabled={!topic.trim() || loading}>
          {loading ? "Running..." : "Run"}
        </button>
      </form>

      {out && (
        <section className="mt-6 space-y-4">
          <h2 className="font-semibold text-lg">CrewOutput (Pydantic JSON)</h2>
          <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">{JSON.stringify(out, null, 2)}</pre>

          {out.final_markdown && (
            <>
              <h3 className="font-semibold">final_markdown</h3>
              <pre className="bg-white border p-3 rounded overflow-auto">{out.final_markdown}</pre>
            </>
          )}
        </section>
      )}
    </main>
  );
}
