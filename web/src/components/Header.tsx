"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
        <Link href="/" className="font-semibold">
          Content Creation Crew
        </Link>

        <nav className="flex gap-4 text-sm">
          <Link
            href="/"
            className={`hover:underline ${isHome ? "font-semibold" : ""}`}
          >
            Home
          </Link>
          {/* adicione outras rotas se quiser */}
          {/* <Link href="/runs" className={pathname.startsWith("/runs") ? "font-semibold" : ""}>Runs</Link> */}
        </nav>
      </div>
    </header>
  );
}
