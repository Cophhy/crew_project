import { useState } from "react";

const MODELS = [
  { id: "mistral:7b-instruct", label: "Mistral 7B Instruct" },
  { id: "llama3.1:8b-instruct", label: "Llama 3.1 8B Instruct" },
  { id: "qwen2.5:7b-instruct", label: "Qwen 2.5 7B Instruct" },
  { id: "gemma2:9b-instruct", label: "Gemma 2 9B Instruct" },
];

export default function RunForm() {
  const [query, setQuery] = useState("");
  const [model, setModel] = useState(MODELS[0].id);
  const [result, setResult] = useState<string | null>(null);
  const [meta, setMeta] = useState<{lang:string, model_id:string}|null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ query, model_id: model })
      });
      const data = await res.json();
      setResult(data.result);
      setMeta({ lang: data.lang, model_id: data.model_id });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <textarea
        className="border rounded w-full p-2"
        placeholder="Pergunte algo (PT ou EN)…"
        value={query} onChange={e=>setQuery(e.target.value)} required
      />
      <div className="flex gap-2 items-center">
        <label className="text-sm font-medium">Modelo (Ollama)</label>
        <select
          className="border rounded p-1"
          value={model} onChange={e=>setModel(e.target.value)}
        >
          {MODELS.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
        </select>
        <button
          className="px-3 py-2 rounded bg-black text-white"
          disabled={loading}
        >
          {loading ? "Rodando…" : "Executar"}
        </button>
      </div>

      {meta && (
        <p className="text-sm text-gray-600">
          Idioma detectado: <b>{meta.lang}</b> • Modelo: <b>{meta.model_id}</b>
        </p>
      )}
      {result && (
        <pre className="whitespace-pre-wrap border rounded p-3">{result}</pre>
      )}
    </form>
  );
}
