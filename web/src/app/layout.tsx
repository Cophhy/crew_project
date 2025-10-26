import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Content Creation Crew",
  description: "Research → Writing → Editing, powered by your Crew and Ollama",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <Header />
        <div className="mx-auto max-w-5xl px-4">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
