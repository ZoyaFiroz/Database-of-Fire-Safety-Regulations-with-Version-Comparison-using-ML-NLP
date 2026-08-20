import Link from "next/link";

export default function Header() {
  return (
    <nav className="sticky top-0 z-50 flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-[#090d16]/80 px-4 py-4 backdrop-blur-md sm:px-6">
      <Link href="/" className="flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-gradient-to-br from-accent-indigo to-accent-purple text-sm font-bold shadow-[0_4px_14px_rgba(99,102,241,0.4)]">
          ADB
        </div>
        <span className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-base font-bold tracking-tight text-transparent sm:text-lg">
          Approved Document B — Comparison Engine
        </span>
      </Link>
      <span className="whitespace-nowrap rounded-full border border-purple-400/30 bg-purple-500/20 px-3 py-1 text-xs font-semibold text-purple-300">
        Next.js Edition
      </span>
    </nav>
  );
}
