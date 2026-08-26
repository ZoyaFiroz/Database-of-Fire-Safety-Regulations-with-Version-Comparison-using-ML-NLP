"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "./AuthProvider";

const NAV_LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/regulations", label: "UK Fire Safety" },
  { href: "/general-compare", label: "Custom Compare" },
];

export default function Header() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <nav className="no-print sticky top-0 z-50 flex flex-wrap items-center justify-between gap-3 border-b border-brand-teal/20 bg-[#071a1f]/85 px-4 py-4 backdrop-blur-md sm:px-6">
      <Link href="/" className="flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-gradient-to-br from-brand-teal to-brand-gold text-sm font-bold text-[#071a1f] shadow-[0_4px_14px_rgba(20,184,166,0.35)]">
          V
        </div>
        <span className="bg-gradient-to-r from-brand-tealDark via-white to-brand-gold bg-clip-text text-base font-bold tracking-tight text-transparent sm:text-lg">
          Veritext
        </span>
      </Link>

      <div className="flex flex-wrap items-center gap-4">
        <div className="hidden items-center gap-1 rounded-full border border-white/10 bg-white/[0.03] p-1 sm:flex">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                  active
                    ? "bg-brand-teal/25 text-brand-goldLight"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        {!loading && !user && (
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-gray-300 hover:text-white"
            >
              Log in
            </Link>
            <Link
              href="/register"
              className="rounded-lg border border-brand-gold/30 bg-brand-gold/10 px-3 py-1.5 text-sm font-medium text-brand-goldLight hover:border-brand-gold/50 hover:bg-brand-gold/20"
            >
              Sign up
            </Link>
          </div>
        )}

        {!loading && user && (
          <div className="flex items-center gap-3">
            <Link href="/account" className="text-sm text-gray-300 hover:text-white">
              {user.email}
            </Link>
            <button
              onClick={handleLogout}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm font-medium text-gray-300 hover:border-removed/40 hover:bg-removed/20 hover:text-white"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
