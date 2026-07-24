"""API do console operacional Helena."""

from __future__ import annotations

import secrets

from flask import jsonify, request

from . import helena_bp
from ..config import Config
from ..services.helena_control import (
    CONTROL_VERSION,
    HelenaCommandStore,
    HelenaConflictError,
    HelenaControlError,
    HelenaPlanner,
    public_record,
    resolve_control_context,
)
from ..utils.internal_auth import require_internal_token
from ..utils.rate_limit import rate_limit


def _disabled_response():
    return jsonify({
        "success": False,
        "error": "Console Helena desabilitado neste ambiente",
    }), 503


def _require_enabled():
    return bool(Config.HELENA_CONTROL_ENABLED)


def _json_body(max_bytes: int = 64 * 1024) -> dict:
    if (request.content_length or 0) > max_bytes:
        raise HelenaControlError("Payload excede o limite do console Helena")
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise HelenaControlError("Payload JSON precisa ser um objeto")
    return payload


def _error_response(exc: Exception):
    status = 409 if isinstance(exc, HelenaConflictError) else 400
    return jsonify({"success": False, "error": str(exc)}), status


@helena_bp.route("/status", methods=["GET"])
@rate_limit(limit=60, window_seconds=60.0, scope="helena.status")
def get_helena_status():
    """Estado publico sanitizado; nao revela modelo, token ou infraestrutura."""
    enabled = bool(Config.HELENA_CONTROL_ENABLED)
    configured = bool((Config.INTERNAL_API_TOKEN or "").strip())
    return jsonify({
        "success": True,
        "data": {
            "version": CONTROL_VERSION,
            "enabled": enabled,
            "available": enabled and configured,
            "authentication": "internal_token",
        },
    })


@helena_bp.route("/session", methods=["POST"])
@require_internal_token
@rate_limit(limit=20, window_seconds=60.0, scope="helena.session")
def open_helena_session():
    if not _require_enabled():
        return _disabled_response()
    return jsonify({
        "success": True,
        "data": {
            "authenticated": True,
            "version": CONTROL_VERSION,
            "capabilities": [
                "observe",
                "plan",
                "approve",
                "operate",
                "audit",
            ],
        },
    })


@helena_bp.route("/context", methods=["POST"])
@require_internal_token
@rate_limit(limit=30, window_seconds=60.0, scope="helena.context")
def get_helena_context():
    if not _require_enabled():
        return _disabled_response()
    try:
        payload = _json_body()
        context = resolve_control_context(payload.get("context"))
        return jsonify({"success": True, "data": context})
    except (HelenaControlError, ValueError) as exc:
        return _error_response(exc)


@helena_bp.route("/commands/plan", methods=["POST"])
@require_internal_token
@rate_limit(limit=12, window_seconds=60.0, scope="helena.plan")
def plan_helena_command():
    if not _require_enabled():
        return _disabled_response()
    try:
        payload = _json_body()
        command = str(payload.get("command") or "")
        plan, context, planner_source = HelenaPlanner().plan(
            command,
            payload.get("context"),
        )
        approval_token = secrets.token_urlsafe(32) if plan["requires_approval"] else None
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()[:200] or None
        record, replayed = HelenaCommandStore().create(
            plan=plan,
            context=context,
            prompt=command,
            planner_source=planner_source,
            approval_token=approval_token,
            idempotency_key=idempotency_key,
        )
        data = public_record(record)
        data["replayed"] = replayed
        if approval_token and record.get("status") == "pending_approval":
            data["approval_token"] = approval_token
        return jsonify({"success": True, "data": data}), 200 if replayed else 201
    except (HelenaControlError, ValueError) as exc:
        return _error_response(exc)


@helena_bp.route("/commands/<command_id>/execute", methods=["POST"])
@require_internal_token
@rate_limit(limit=12, window_seconds=60.0, scope="helena.execute")
def execute_helena_command(command_id: str):
    if not _require_enabled():
        return _disabled_response()
    try:
        payload = _json_body()
        record, execution_ticket = HelenaCommandStore().begin_execution(
            command_id,
            payload.get("approval_token"),
        )
        return jsonify({
            "success": True,
            "data": {
                "command": public_record(record),
                "execution_ticket": execution_ticket,
                "actions": record["plan"]["actions"],
            },
        })
    except (HelenaControlError, ValueError) as exc:
        return _error_response(exc)


@helena_bp.route("/commands/<command_id>/complete", methods=["POST"])
@require_internal_token
@rate_limit(limit=30, window_seconds=60.0, scope="helena.complete")
def complete_helena_command(command_id: str):
    if not _require_enabled():
        return _disabled_response()
    try:
        payload = _json_body()
        ticket = str(payload.get("execution_ticket") or "")
        if not ticket:
            raise HelenaControlError("Informe o ticket de execucao")
        record = HelenaCommandStore().finish(
            command_id,
            ticket,
            success=bool(payload.get("success")),
            result=payload.get("result"),
            error=payload.get("error"),
        )
        return jsonify({"success": True, "data": public_record(record)})
    except (HelenaControlError, ValueError) as exc:
        return _error_response(exc)


@helena_bp.route("/commands/<command_id>/cancel", methods=["POST"])
@require_internal_token
@rate_limit(limit=20, window_seconds=60.0, scope="helena.cancel")
def cancel_helena_command(command_id: str):
    if not _require_enabled():
        return _disabled_response()
    try:
        record = HelenaCommandStore().cancel(command_id)
        return jsonify({"success": True, "data": public_record(record)})
    except (HelenaControlError, ValueError) as exc:
        return _error_response(exc)


@helena_bp.route("/commands/<command_id>", methods=["GET"])
@require_internal_token
@rate_limit(limit=60, window_seconds=60.0, scope="helena.command")
def get_helena_command(command_id: str):
    if not _require_enabled():
        return _disabled_response()
    try:
        record = HelenaCommandStore().get(command_id)
        if not record:
            return jsonify({"success": False, "error": "Comando nao encontrado"}), 404
        return jsonify({"success": True, "data": public_record(record)})
    except ValueError as exc:
        return _error_response(exc)


@helena_bp.route("/commands", methods=["GET"])
@require_internal_token
@rate_limit(limit=30, window_seconds=60.0, scope="helena.commands")
def list_helena_commands():
    if not _require_enabled():
        return _disabled_response()
    try:
        limit = max(1, min(int(request.args.get("limit", 20)), 100))
    except (TypeError, ValueError):
        limit = 20
    records = HelenaCommandStore().list_records(limit=limit)
    return jsonify({
        "success": True,
        "data": [public_record(record) for record in records],
        "count": len(records),
    })
