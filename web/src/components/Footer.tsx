export default function Footer() {
  return (
    <footer className="mt-12 border-t bg-white">
      <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-gray-600 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>© {new Date().getFullYear()} Content Creation Crew</p>
        <p className="opacity-70">
          Powered by FastAPI, Next.js, Tailwind & Ollama
        </p>
      </div>
    </footer>
  );
}
