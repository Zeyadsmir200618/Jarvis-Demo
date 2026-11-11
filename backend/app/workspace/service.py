"""Developer workspace through MCP — an early prototype of the documented
Remediation -> Human approval -> Execution -> Validation path, applied to a
real project folder on the host PC.

  inspect()          read-only: project tree + key files (+ LLM summary if Ollama is up)
  propose_edit()     LLM (or explicit find/replace) builds new content; the MCP server
                     computes the diff; a PENDING approval is created. Nothing is written.
  propose_command()  read-only commands run at once; others become PENDING approvals.
  approve()/reject() human decision -> one-time token -> MCP tool call -> audit trail.
"""
from __future__ import annotations

import re
from typing import Any

from app.approvals.service import approval_service
from app.approvals.tokens import mint_token
from app.core import config
from app.integrations.mcp.client import MCPUnavailable, mcp_client
from app.llm.ollama_client import ollama_client


def _llm_failed(text: str) -> bool:
    return not text or text.startswith("[Ollama Connection Warning") or text.startswith("[Error")


class WorkspaceError(Exception):
    pass


class WorkspaceService:
    async def status(self) -> dict:
        if not mcp_client.enabled:
            return {"connected": False, "reason": "MCP not configured", "transport": config.MCP_TRANSPORT}
        try:
            desc = await mcp_client.describe()
            summary = await mcp_client.call("project_summary")
            cmds = await mcp_client.call("list_commands")
            return {"connected": True, "transport": config.MCP_TRANSPORT, "project": summary.get("project"),
                    "tools": desc["tools"], "resources": desc["resources"], "commands": cmds.get("commands", [])}
        except MCPUnavailable as e:
            return {"connected": False, "reason": str(e), "transport": config.MCP_TRANSPORT}

    async def inspect(self, question: str = "") -> dict:
        steps = [{"step": 1, "thought": "Route to the host workspace via MCP", "action": "project_summary", "observation": None}]
        try:
            summary = await mcp_client.call("project_summary")
        except MCPUnavailable as e:
            return {"ok": False, "answer": f"MCP workspace unavailable: {e}", "steps": steps}
        files = {}
        for name in summary.get("key_files", [])[:4]:
            r = await mcp_client.call("read_file", {"path": name})
            if r.get("ok"):
                files[name] = r["content"][:3000]
        py = (await mcp_client.call("find_files", {"pattern": "*.py", "max_results": 20})).get("matches", [])
        steps[0]["observation"] = f"{len(summary.get('tree', []))} entries, key files: {', '.join(summary.get('key_files', [])) or 'none'}"
        steps.append({"step": 2, "thought": "Read key files through MCP (read-only)", "action": "read_file x%d" % len(files), "observation": ", ".join(files) or "none"})
        tree = "\n".join(summary.get("tree", [])[:80])
        prompt = (f"You are inspecting the project '{summary.get('project')}'.\nUser request: {question or 'Summarize the project.'}\n\n"
                  f"File tree:\n{tree}\n\n" + "\n\n".join(f"--- {n} ---\n{c}" for n, c in files.items()) +
                  "\n\nExplain briefly what the project does, how it is structured, how to test and run it.")
        answer = await ollama_client.generate(prompt=prompt, temperature=0.2)
        if _llm_failed(answer):
            answer = (f"**Project `{summary.get('project')}`** (read via MCP; LLM offline, so no AI summary)\n\n"
                      f"Key files: {', '.join(summary.get('key_files', [])) or 'none'}\n\nPython files: {', '.join(py) or 'none'}\n\n"
                      f"Allowed commands: {', '.join(summary.get('commands', []))}\n\n```\n{tree}\n```")
            steps.append({"step": 3, "thought": "LLM unavailable — returning the structured summary only", "action": None, "observation": None})
        else:
            steps.append({"step": 3, "thought": "Summarised with the local LLM", "action": "ollama.generate", "observation": None})
        return {"ok": True, "answer": answer, "steps": steps, "summary": summary}

    async def propose_edit(self, path: str, instruction: str = "", find: str | None = None, replace: str | None = None) -> dict:
        cur = await mcp_client.call("read_file", {"path": path})
        if not cur.get("ok"):
            raise WorkspaceError(cur.get("error", "cannot read file"))
        old = cur["content"]
        source = "explicit find/replace"
        if find:
            if old.count(find) != 1:
                raise WorkspaceError(f"'find' text must occur exactly once (found {old.count(find)}).")
            new = old.replace(find, replace or "")
        else:
            if not instruction:
                raise WorkspaceError("Provide an instruction, or find/replace text.")
            out = await ollama_client.generate(
                prompt=(f"Apply this change to the file `{path}`:\n{instruction}\n\nCurrent content:\n```\n{old}\n```\n\n"
                        "Return ONLY the complete updated file inside one fenced code block. Change nothing else."),
                temperature=0.1)
            if _llm_failed(out):
                raise WorkspaceError("The local LLM is offline. Start Ollama, or use explicit find/replace.")
            m = re.search(r"```[a-zA-Z0-9_+-]*\n(.*?)```", out, re.S)
            new = m.group(1) if m else out
            if old.endswith("\n") and not new.endswith("\n"):
                new += "\n"
            source = f"LLM ({config.OLLAMA_MODEL})"
        prev = await mcp_client.call("preview_write", {"path": path, "content": new})
        if not prev.get("ok"):
            raise WorkspaceError(prev.get("error", "preview failed"))
        if not prev.get("changed"):
            raise WorkspaceError("The proposed change is identical to the current file.")
        return approval_service.create("write", f"Edit {prev['path']} ({source})",
                                       {"path": prev["path"], "content": new, "digest": prev["digest"]}, prev["diff"])

    async def propose_command(self, command_id: str) -> dict:
        cmds = {c["id"]: c for c in (await mcp_client.call("list_commands")).get("commands", [])}
        if command_id not in cmds:
            raise WorkspaceError(f"Command '{command_id}' is not allow-listed on the MCP server.")
        if not cmds[command_id]["requires_approval"]:
            result = await mcp_client.call("run_command", {"command_id": command_id})
            approval_service.audit("read_only_command", command_id=command_id, ok=result.get("ok"))
            return {"status": "executed", "requires_approval": False, "result": result}
        project = (await mcp_client.call("project_summary")).get("project")
        action = approval_service.create("exec", f"Run '{command_id}': {cmds[command_id]['description']}",
                                         {"command_id": command_id, "project": project})
        return {"status": "pending", "requires_approval": True, "action": action}

    async def approve(self, action_id: str, actor: str = "engineer") -> dict:
        a = approval_service.get(action_id)
        if not a or a["status"] != "pending":
            raise WorkspaceError("Action not found or already decided.")
        p: dict[str, Any] = a["payload"]
        if a["kind"] == "write":
            token = mint_token(config.JARVIS_APPROVAL_SECRET, "write", p["path"], p["digest"])
            result = await mcp_client.call("write_file", {"path": p["path"], "content": p["content"], "approval_token": token})
        else:
            token = mint_token(config.JARVIS_APPROVAL_SECRET, "exec", p["command_id"], p["project"])
            result = await mcp_client.call("run_command", {"command_id": p["command_id"], "approval_token": token})
        return approval_service.decide(action_id, "approved", actor, result=result)

    def reject(self, action_id: str, actor: str = "engineer", comment: str = "") -> dict:
        a = approval_service.get(action_id)
        if not a or a["status"] != "pending":
            raise WorkspaceError("Action not found or already decided.")
        return approval_service.decide(action_id, "rejected", actor, comment)


workspace_service = WorkspaceService()
