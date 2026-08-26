"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";
import { ApiError } from "@/lib/api";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    try {
      await register(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-73px)] max-w-md flex-col items-center justify-center px-4 py-10">
      <div className="mb-6 flex flex-col items-center text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-teal to-brand-gold text-lg font-bold text-[#071a1f] shadow-[0_8px_24px_rgba(20,184,166,0.35)]">
          V
        </div>
        <h1 className="mt-4 bg-gradient-to-r from-brand-tealDark via-white to-brand-gold bg-clip-text text-2xl font-bold tracking-tight text-transparent">
          Veritext
        </h1>
        <p className="mt-1 text-sm text-gray-400">Structured, secure document comparison</p>
      </div>

      <div className="w-full rounded-2xl border border-brand-teal/20 bg-white/[0.03] p-8 shadow-[0_0_60px_-30px_rgba(20,184,166,0.4)] backdrop-blur-md">
        <h2 className="text-xl font-bold">Create an account</h2>
        <p className="mt-1 text-sm text-gray-400">
          Save comparisons, add notes, and track your export history.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/25"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">
              Password (min. 8 characters)
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/25"
            />
          </div>

          {error && <p className="text-sm text-removed">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 rounded-lg bg-gradient-to-r from-brand-teal to-brand-tealDark px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Creating account…" : "Sign up"}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-gray-400">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-goldLight hover:underline">
            Log in
          </Link>
        </p>
      </div>

      <p className="mt-5 flex items-center gap-1.5 text-xs text-gray-500">
        <span aria-hidden>🔒</span> Your credentials are hashed and never shared with third parties.
      </p>
    </main>
  );
}
