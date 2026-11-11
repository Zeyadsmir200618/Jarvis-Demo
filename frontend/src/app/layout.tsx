import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import clsx from "clsx";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "J.A.R.V.I.S. Digital Twin",
  description: "AI-Powered Digital Twin Platform with Multi-Agent Orchestration and Ollama LLM",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={clsx(inter.className, "flex flex-col min-h-screen antialiased")}>
        {children}
      </body>
    </html>
  );
}
