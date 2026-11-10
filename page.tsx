'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  agentUsed?: string;
  steps?: AgentStepLog[];
  previewUrl?: string;
}

interface AgentStepLog {
  step: number;
  thought: string;
  action?: string;
  observation?: string;
}

interface SystemStatus {
  status: string;
  ollama_connected: boolean;
  ollama_model: string;
  generated_sites_count: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Inline SVG Icon components to ensure zero dependency failure
const Icons = {
  Zap: ({ className }: { className?: string }) => (
    <svg className={cn("w-5 h-5", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  Send: ({ className }: { className?: string }) => (
    <svg className={cn("w-4 h-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
    </svg>
  ),
  Loader: ({ className }: { className?: string }) => (
    <svg className={cn("w-4 h-4 animate-spin", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  ),
  Bot: ({ className }: { className?: string }) => (
    <svg className={cn("w-4 h-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
    </svg>
  ),
  Code: ({ className }: { className?: string }) => (
    <svg className={cn("w-4 h-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  ),
  Terminal: ({ className }: { className?: string }) => (
    <svg className={cn("w-4 h-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  ),
  Info: ({ className }: { className?: string }) => (
    <svg className={cn("w-4 h-4", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Layout: ({ className }: { className?: string }) => (
    <svg className={cn("w-5 h-5", className)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
    </svg>
  ),
};

function AgentIcon({ agentName, className }: { agentName?: string; className?: string }) {
  if (agentName === 'General Companion Agent') {
    return <Icons.Bot className={cn("text-cyan-400", className)} />;
  }
  if (agentName === 'Web & Code Builder Agent') {
    return <Icons.Code className={cn("text-emerald-400", className)} />;
  }
  if (agentName === 'Root Cause Analysis Agent') {
    return <Icons.Terminal className={cn("text-rose-400", className)} />;
  }
  if (agentName === 'System') {
    return <Icons.Info className={cn("text-blue-400", className)} />;
  }
  return <Icons.Zap className={cn("text-cyan-400", className)} />;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([{
    id: 'welcome',
    text: "Hello! I'm J.A.R.V.I.S., your AI-Powered Digital Twin platform. You can ask me general questions, ask me to build websites (e.g., 'build a login page'), or report system errors for root cause analysis.",
    sender: 'agent',
    agentUsed: 'System',
  }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [activeAgent, setActiveAgent] = useState<'auto' | 'general' | 'web_builder' | 'rca'>('auto');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentPreviewUrl, setCurrentPreviewUrl] = useState<string | null>(null);
  const [showAgentLogs, setShowAgentLogs] = useState(false);
  const [currentAgentSteps, setCurrentAgentSteps] = useState<AgentStepLog[]>([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/status`);
      if (response.ok) {
        const data: SystemStatus = await response.json();
        setSystemStatus(data);
      }
    } catch (error) {
      console.error("Failed to fetch system status", error);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsgText = input;
    const newUserMessage: Message = {
      id: Date.now().toString(),
      text: userMsgText,
      sender: 'user',
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setCurrentAgentSteps([]);
    setShowAgentLogs(false);
    setIsLoading(true);
    setInput('');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsgText,
          agent_override: activeAgent !== 'auto' ? activeAgent : undefined
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      let extractedUrl = data.preview_url;
      if (!extractedUrl && data.response.includes('.html')) {
        const match = data.response.match(/(site_[a-zA-Z0-9_]+\.html)/);
        if (match) {
          extractedUrl = `/generated_sites/${match[0]}`;
        }
      }
      const agentResponse: Message = {
        id: Date.now().toString() + '-agent',
        text: data.response,
        sender: 'agent',
        agentUsed: data.agent_used,
        steps: data.steps || [],
        previewUrl: extractedUrl ? `${API_BASE_URL}${extractedUrl}` : undefined,
      };

      setMessages((prev) => [...prev, agentResponse]);
      if (data.steps?.length) {
        setCurrentAgentSteps(data.steps);
      }
      if (agentResponse.previewUrl) {
        setCurrentPreviewUrl(agentResponse.previewUrl);
        setShowAgentLogs(false);
      } else if (data.steps?.length) {
        setShowAgentLogs(true);
      }
    } catch (error) {
      setMessages((prev) => [...prev, {
        id: Date.now().toString() + '-error',
        text: `Error connecting to J.A.R.V.I.S. backend. Ensure FastAPI server is running on http://localhost:8000. Details: ${(error as Error).message}`,
        sender: 'agent',
        agentUsed: 'System Error',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-between p-4 md:p-6 font-sans">
      {/* Top Header */}
      <header className="w-full max-w-6xl bg-slate-900/80 border border-slate-800 backdrop-blur-md rounded-2xl p-4 mb-4 flex items-center justify-between shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cyan-500/20 border border-cyan-500/40 rounded-xl flex items-center justify-center text-cyan-400">
            <Icons.Zap className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              J.A.R.V.I.S. <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono border border-cyan-500/30">AI Twin</span>
            </h1>
            <p className="text-xs text-slate-400">Multi-Agent Orchestration Engine (Ollama Llama 3)</p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          {systemStatus ? (
            <div className={cn(
              "px-3 py-1.5 rounded-full flex items-center gap-2 border font-medium",
              systemStatus.ollama_connected
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-amber-500/10 border-amber-500/30 text-amber-400"
            )}>
              <span className={cn("w-2 h-2 rounded-full animate-pulse", systemStatus.ollama_connected ? "bg-emerald-400" : "bg-amber-400")} />
              Ollama: {systemStatus.ollama_connected ? `Connected (${systemStatus.ollama_model})` : 'Standalone Mode'}
            </div>
          ) : (
            <div className="px-3 py-1.5 rounded-full bg-slate-800 text-slate-400 animate-pulse border border-slate-700">
              Connecting...
            </div>
          )}
          <div className="px-3 py-1.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            Sites Built: <span className="text-cyan-400 font-bold">{systemStatus?.generated_sites_count || 0}</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="w-full max-w-6xl flex-1 grid grid-cols-1 md:grid-cols-12 gap-4 h-[calc(100vh-140px)]">

        {/* Left Chat Window (7 Cols) */}
        <div className="md:col-span-7 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl backdrop-blur-sm">

          {/* Agent Mode Bar */}
          <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Active Agent Routing:</span>
            <div className="flex gap-1.5">
              {(['auto', 'general', 'web_builder', 'rca'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setActiveAgent(mode)}
                  className={cn(
                    "px-3 py-1 rounded-lg font-medium transition-all duration-150",
                    activeAgent === mode
                      ? "bg-cyan-500 text-slate-950 font-semibold shadow-md shadow-cyan-500/20"
                      : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                  )}
                >
                  {mode === 'auto' ? '⚡ Auto' : mode === 'general' ? '💬 Chat' : mode === 'web_builder' ? '🛠️ Builder' : '🔍 RCA'}
                </button>
              ))}
            </div>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex flex-col max-w-[88%]",
                  msg.sender === 'user' ? "ml-auto items-end" : "mr-auto items-start"
                )}
              >
                <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] text-slate-400">
                  {msg.sender === 'agent' ? (
                    <>
                      <AgentIcon agentName={msg.agentUsed} className="w-3.5 h-3.5" />
                      <span className="font-semibold text-slate-300">{msg.agentUsed || 'J.A.R.V.I.S.'}</span>
                    </>
                  ) : (
                    <span className="font-semibold text-cyan-400">You</span>
                  )}
                </div>

                <div className={cn(
                  "rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md",
                  msg.sender === 'user'
                    ? "bg-cyan-600 text-white rounded-tr-none"
                    : "bg-slate-800/90 text-slate-100 border border-slate-700/60 rounded-tl-none whitespace-pre-wrap"
                )}>
                  {msg.text}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 rounded-xl p-3 w-fit">
                <Icons.Loader className="w-4 h-4 text-cyan-400" />
                <span>Orchestrator reasoning and executing agent tools...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Form */}
          <form onSubmit={handleSubmit} className="p-3 bg-slate-900/90 border-t border-slate-800 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask J.A.R.V.I.S. to build a website, answer questions, or diagnose errors..."
              className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold px-4 py-2.5 rounded-xl transition-all flex items-center justify-center shadow-lg shadow-cyan-500/20"
            >
              {isLoading ? <Icons.Loader /> : <Icons.Send />}
            </button>
          </form>
        </div>

        {/* Right Panel: Web Preview & Agent Execution Logs (5 Cols) */}
        <div className="md:col-span-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl backdrop-blur-sm">

          {/* Header Toggle */}
          <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
              <Icons.Layout className="w-4 h-4 text-cyan-400" />
              <span>{showAgentLogs ? 'Agent Execution Trace' : 'Live Interactive Web Preview'}</span>
            </div>
            <button
              onClick={() => setShowAgentLogs(!showAgentLogs)}
              className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 font-medium transition-all"
            >
              {showAgentLogs ? 'Show Web Preview' : 'Show Execution Logs'}
            </button>
          </div>

          {/* Display View */}
          <div className="flex-1 bg-slate-950 relative overflow-hidden flex flex-col">
            {showAgentLogs ? (
              <div className="flex-1 p-4 overflow-y-auto space-y-3 font-mono text-xs">
                {currentAgentSteps.length === 0 ? (
                  <div className="text-slate-500 text-center py-10">No agent step logs recorded yet.</div>
                ) : (
                  currentAgentSteps.map((s, idx) => (
                    <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-1">
                      <div className="text-cyan-400 font-bold">Step {s.step}: {s.thought}</div>
                      {s.action && <div className="text-amber-300">Action: {s.action}</div>}
                      {s.observation && <div className="text-slate-400 text-[11px] bg-slate-950 p-1.5 rounded border border-slate-800 mt-1">{s.observation}</div>}
                    </div>
                  ))
                )}
              </div>
            ) : currentPreviewUrl ? (
              <iframe
                src={currentPreviewUrl}
                className="w-full h-full border-0 bg-white"
                title="Generated Web Application"
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-500 space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-600">
                  <Icons.Code className="w-8 h-8 text-cyan-500/40" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-300">No Generated Web Preview Active</h3>
                  <p className="text-xs text-slate-500 max-w-xs mt-1">
                    Ask J.A.R.V.I.S. <span className="text-cyan-400 font-mono">"build a login page"</span> or <span className="text-cyan-400 font-mono">"create a dashboard"</span> to render a live interactive preview!
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </main>
  );
}
