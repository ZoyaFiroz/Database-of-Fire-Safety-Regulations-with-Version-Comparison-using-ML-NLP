import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fire Safety Regulations — Comparison Engine",
  description:
    "Version comparison dashboard for UK Approved Document B (fire safety), with cross-language support.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen`}>
        <Header />
        {children}
      </body>
    </html>
  );
}
