"""Workspace (MCP) + approvals API. All writes/commands go through a human approval."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.approvals.service import approval_service
from app.integrations.mcp.client import MCPUnavailable
from app.workspace.service import WorkspaceError, workspace_service

router = APIRouter(prefix="/workspace", tags=["workspace"])


class InspectRequest(BaseModel):
    question: str = ""


class EditRequest(BaseModel):
    path: str = Field(..., description="File path relative to the authorized project")
    instruction: str = ""
    find: Optional[str] = None
    replace: Optional[str] = None


class CommandRequest(BaseModel):
    command_id: str


class Decision(BaseModel):
    actor: str = "engineer"
    comment: str = ""


def _wrap(exc: Exception):
    if isinstance(exc, MCPUnavailable):
        raise HTTPException(503, str(exc))
    if isinstance(exc, WorkspaceError):
        raise HTTPException(400, str(exc))
    raise exc


@router.get("/status")
async def status():
    return await workspace_service.status()


@router.post("/inspect")
async def inspect(req: InspectRequest):
    try:
        return await workspace_service.inspect(req.question)
    except Exception as e:  # noqa: BLE001
        _wrap(e)


@router.post("/propose-edit")
async def propose_edit(req: EditRequest):
    try:
        return await workspace_service.propose_edit(req.path, req.instruction, req.find, req.replace)
    except Exception as e:  # noqa: BLE001
        _wrap(e)


@router.post("/commands")
async def command(req: CommandRequest):
    try:
        return await workspace_service.propose_command(req.command_id)
    except Exception as e:  # noqa: BLE001
        _wrap(e)


@router.get("/approvals")
async def approvals():
    return approval_service.list()


@router.post("/approvals/{action_id}/approve")
async def approve(action_id: str, d: Decision):
    try:
        return await workspace_service.approve(action_id, d.actor)
    except Exception as e:  # noqa: BLE001
        _wrap(e)


@router.post("/approvals/{action_id}/reject")
async def reject(action_id: str, d: Decision):
    try:
        return workspace_service.reject(action_id, d.actor, d.comment)
    except Exception as e:  # noqa: BLE001
        _wrap(e)


@router.get("/audit")
async def audit(limit: int = 50):
    return approval_service.recent_audit(limit)
