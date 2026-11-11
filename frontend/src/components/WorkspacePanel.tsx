'use client';

import { useCallback, useEffect, useState } from 'react';

interface Command { id: string; description: string; requires_approval: boolean }
interface WsStatus { connected: boolean; reason?: string; transport?: string; project?: string; tools?: string[]; resources?: string[]; commands?: Command[] }
interface Action { id: string; kind: 'write' | 'exec'; summary: string; status: string; preview?: string; target?: string; result?: any; created_at: string }
interface AuditEvent { ts: string; event: string; summary?: string; command_id?: string; actor?: string; ok?: boolean }

async function call(apiBase: string, path: string, body?: unknown) {
  const res = await fetch(`${apiBase}${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

function DiffView({ diff }: { diff: string }) {
  return (
    <pre className="text-[11px] leading-4 bg-slate-950 border border-slate-800 rounded-lg p-2 overflow-x-auto max-h-56">
      {diff.split('\n').map((l, i) => (
        <div key={i} className={l.startsWith('+') && !l.startsWith('+++') ? 'text-emerald-400' : l.startsWith('-') && !l.startsWith('---') ? 'text-rose-400' : l.startsWith('@@') ? 'text-cyan-400' : 'text-slate-400'}>{l || ' '}</div>
      ))}
    </pre>
  );
}

export default function WorkspacePanel({ apiBase }: { apiBase: string }) {
  const [status, setStatus] = useState<WsStatus | null>(null);
  const [actions, setActions] = useState<Action[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [output, setOutput] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [path, setPath] = useState('app.py');
  const [instruction, setInstruction] = useState('');
  const [find, setFind] = useState('');
  const [replace, setReplace] = useState('');

  const refresh = useCallback(async () => {
    try {
      setStatus(await call(apiBase, '/workspace/status'));
      setActions(await call(apiBase, '/workspace/approvals'));
      setAudit(await call(apiBase, '/workspace/audit?limit=12'));
    } catch (e: any) { setError(e.message); }
  }, [apiBase]);

  useEffect(() => { refresh(); }, [refresh]);

  const run = async (fn: () => Promise<any>) => {
    setBusy(true); setError('');
    try { await fn(); } catch (e: any) { setError(e.message); } finally { setBusy(false); refresh(); }
  };

  const showResult = (r: any) => {
    if (!r) return;
    if (r.output !== undefined) setOutput(`$ ${(r.argv || []).join(' ')}\nexit code ${r.exit_code}\n\n${r.output}`);
    else setOutput(JSON.stringify(r, null, 2));
  };

  const pending = actions.filter((a) => a.status === 'pending');
  const decided = actions.filter((a) => a.status !== 'pending').slice(0, 4);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs text-slate-300">
      {/* Connection */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-slate-200">MCP host workspace</span>
          <span className={status?.connected ? 'text-emerald-400' : 'text-amber-400'}>
            ● {status ? (status.connected ? `connected (${status.transport})` : 'not connected') : 'checking…'}
          </span>
        </div>
        {status?.connected ? (
          <div className="text-slate-400">
            Project <span className="text-cyan-300 font-mono">{status.project}</span> · {status.tools?.length} tools · {status.resources?.length} resources
            <div className="font-mono text-[10px] text-slate-500 mt-1">{status.tools?.join(' · ')}</div>
          </div>
        ) : (
          <div className="text-slate-500">{status?.reason || ''} — start the host MCP server (see docs/MCP_SETUP.md).</div>
        )}
        <div className="flex gap-2 pt-1">
          <button disabled={busy || !status?.connected} onClick={() => run(async () => { const r = await call(apiBase, '/workspace/inspect', { question: 'Inspect the project' }); setOutput(r.answer); })}
            className="px-2.5 py-1 rounded-lg bg-cyan-500 text-slate-950 font-semibold disabled:opacity-40">Inspect project</button>
          <button onClick={refresh} className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700">Refresh</button>
        </div>
      </section>

      {/* Propose edit */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-2">
        <div className="font-semibold text-slate-200">Propose a code change <span className="text-slate-500 font-normal">(nothing is written until you approve)</span></div>
        <input value={path} onChange={(e) => setPath(e.target.value)} placeholder="path, e.g. app.py" className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 font-mono" />
        <textarea value={instruction} onChange={(e) => setInstruction(e.target.value)} rows={2} placeholder="Instruction for the local LLM, e.g. 'make greeting() end with an exclamation mark'"
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5" />
        <details className="text-slate-400">
          <summary className="cursor-pointer">Explicit find / replace (works without the LLM)</summary>
          <div className="grid grid-cols-2 gap-2 mt-2">
            <textarea value={find} onChange={(e) => setFind(e.target.value)} rows={2} placeholder="find (exact, once)" className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 font-mono" />
            <textarea value={replace} onChange={(e) => setReplace(e.target.value)} rows={2} placeholder="replace with" className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 font-mono" />
          </div>
        </details>
        <button disabled={busy || !status?.connected} onClick={() => run(() => call(apiBase, '/workspace/propose-edit', { path, instruction, find: find || null, replace: find ? replace : null }))}
          className="px-2.5 py-1 rounded-lg bg-cyan-500 text-slate-950 font-semibold disabled:opacity-40">Propose change</button>
      </section>

      {/* Commands */}
      <section className="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-2">
        <div className="font-semibold text-slate-200">Allow-listed commands</div>
        <div className="flex flex-wrap gap-1.5">
          {(status?.commands || []).map((c) => (
            <button key={c.id} title={c.description} disabled={busy}
              onClick={() => run(async () => { const r = await call(apiBase, '/workspace/commands', { command_id: c.id }); if (r.result) showResult(r.result); })}
              className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 hover:border-cyan-500 font-mono disabled:opacity-40">
              {c.id}{c.requires_approval ? ' 🔒' : ''}
            </button>
          ))}
        </div>
        <div className="text-[10px] text-slate-500">🔒 = needs human approval before it runs</div>
      </section>

      {/* Approval gate */}
      <section className="bg-amber-500/5 border border-amber-500/40 rounded-xl p-3 space-y-2">
        <div className="font-semibold text-amber-300">Human approval gate · {pending.length} pending</div>
        {pending.length === 0 && <div className="text-slate-500">No actions waiting for approval.</div>}
        {pending.map((a) => (
          <div key={a.id} className="bg-slate-900 border border-slate-800 rounded-lg p-2 space-y-2">
            <div className="flex justify-between gap-2"><span className="text-slate-200">{a.summary}</span><span className="font-mono text-slate-500">{a.id}</span></div>
            {a.kind === 'write' && a.preview && <DiffView diff={a.preview} />}
            <div className="flex gap-2">
              <button disabled={busy} onClick={() => run(async () => { const r = await call(apiBase, `/workspace/approvals/${a.id}/approve`, {}); showResult(r.result); })}
                className="px-2.5 py-1 rounded-lg bg-emerald-500 text-slate-950 font-semibold disabled:opacity-40">Approve</button>
              <button disabled={busy} onClick={() => run(() => call(apiBase, `/workspace/approvals/${a.id}/reject`, { comment: 'rejected in UI' }))}
                className="px-2.5 py-1 rounded-lg bg-rose-500/80 text-slate-950 font-semibold disabled:opacity-40">Reject</button>
            </div>
          </div>
        ))}
        {decided.map((a) => (
          <div key={a.id} className="text-slate-500">{a.status === 'approved' ? '✔' : '✖'} {a.summary} — {a.status}{a.result && a.result.ok === false ? ` (error: ${a.result.error || 'exit ' + a.result.exit_code})` : ''}</div>
        ))}
      </section>

      {error && <div className="text-rose-400 bg-rose-500/10 border border-rose-500/30 rounded-lg p-2">{error}</div>}
      {busy && <div className="text-cyan-400">Working…</div>}

      {output && (
        <section className="space-y-1">
          <div className="font-semibold text-slate-200">Result</div>
          <pre className="text-[11px] bg-slate-950 border border-slate-800 rounded-lg p-2 whitespace-pre-wrap max-h-72 overflow-y-auto">{output}</pre>
        </section>
      )}

      <section className="space-y-1">
        <div className="font-semibold text-slate-200">Audit trail (append-only)</div>
        {audit.map((e, i) => (
          <div key={i} className="font-mono text-[10px] text-slate-500">{e.ts} · {e.event} · {e.summary || e.command_id}{e.actor ? ` · ${e.actor}` : ''}</div>
        ))}
      </section>
    </div>
  );
}
