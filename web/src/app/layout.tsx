import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Content Creation Crew",
  description: "Research → Writing → Editing, powered by your Crew and Ollama",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
