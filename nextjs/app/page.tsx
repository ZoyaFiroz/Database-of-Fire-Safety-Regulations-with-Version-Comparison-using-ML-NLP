"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

const WORKFLOWS = [
  {
    href: "/regulations",
    icon: "🛡️",
    accent: "teal" as const,
    title: "UK Safety Regulation Comparison",
    description:
      "Structured, clause-level comparison across ingested versions of Approved Document B - fixed schema, clause-by-clause diffing.",
    cta: "Open UK Fire Safety workflow",
  },
  {
    href: "/general-compare",
    icon: "🔗",
    accent: "gold" as const,
    title: "Custom Document Comparison",
    description:
      "Upload any two documents and get a plain-language, AI-synthesized comparison with a single similarity score - no fixed schema required.",
    cta: "Open Custom Compare workflow",
  },
];

export default function DashboardHubPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return <main className="mx-auto max-w-4xl px-4 py-10 text-gray-400">Loading…</main>;
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 sm:py-16">
      <div className="text-center">
        <span className="inline-block rounded-full border border-brand-teal/30 bg-brand-teal/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-brand-goldLight">
          Welcome back
        </span>
        <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
          {user.email.split("@")[0]}, choose a comparison workflow
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-sm text-gray-400">
          Veritext runs two distinct comparison engines - pick the one that fits the documents
          you&apos;re working with.
        </p>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-2">
        {WORKFLOWS.map((w) => {
          const isTeal = w.accent === "teal";
          return (
            <Link
              key={w.href}
              href={w.href}
              className={`group flex flex-col rounded-3xl border p-7 backdrop-blur-md transition ${
                isTeal
                  ? "border-brand-teal/25 bg-gradient-to-b from-brand-teal/10 to-white/[0.02] hover:border-brand-teal/50 hover:shadow-[0_0_50px_-20px_rgba(20,184,166,0.5)]"
                  : "border-brand-gold/25 bg-gradient-to-b from-brand-gold/10 to-white/[0.02] hover:border-brand-gold/50 hover:shadow-[0_0_50px_-20px_rgba(212,175,55,0.5)]"
              }`}
            >
              <div
                className={`flex h-14 w-14 items-center justify-center rounded-2xl text-2xl ${
                  isTeal ? "bg-brand-teal/20" : "bg-brand-gold/20"
                }`}
              >
                {w.icon}
              </div>
              <h2 className="mt-5 text-xl font-bold text-white">{w.title}</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-gray-400">{w.description}</p>
              <span
                className={`mt-6 inline-flex items-center gap-2 text-sm font-semibold ${
                  isTeal ? "text-brand-teal" : "text-brand-goldLight"
                }`}
              >
                {w.cta}
                <span className="transition group-hover:translate-x-1">→</span>
              </span>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
