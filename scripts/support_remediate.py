#!/usr/bin/env python3
"""Remedia hallazgos conocidos del agente soporte."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from support_common import (
    AUTO_FIX_CATEGORIES,
    REPO_ROOT,
    gateway_healthy,
    git_commit_push,
    load_findings,
    now_iso,
    run_cmd,
    update_finding,
    whatsapp_pending_count,
)


def remediate_clear_whatsapp_and_reset() -> str:
    script = REPO_ROOT / "scripts/clear-whatsapp-pending-remote.sh"
    if not script.exists():
        return "script clear-whatsapp no encontrado"
    code, out, err = run_cmd(["bash", str(script)], timeout=180)
    return (out or err or f"exit={code}")[:800]


def remediate_restart_gateway() -> str:
    code, out, err = run_cmd(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.yml",
            "-f",
            "docker-compose.finanzas-mounts.yml",
            "restart",
            "openclaw-gateway",
        ],
        cwd=REPO_ROOT / "openclaw",
        timeout=120,
    )
    return (out or err or f"exit={code}")[:400]


def pick_open_findings(categories: List[str] | None = None) -> List[dict]:
    rows = load_findings()
    out = []
    for row in rows:
        if row.get("status") != "open":
            continue
        cat = row.get("category") or ""
        if categories and cat not in categories:
            continue
        if cat in AUTO_FIX_CATEGORIES:
            out.append(row)
    return out


def remediate_finding(finding_id: str, *, do_commit: bool) -> dict:
    rows = load_findings()
    row = next((r for r in rows if r.get("finding_id") == finding_id), None)
    if not row:
        return {"status": "not_found", "finding_id": finding_id}
    return _apply_fix(row, do_commit=do_commit)


def _apply_fix(row: dict, *, do_commit: bool) -> dict:
    cat = row.get("category") or ""
    actions: List[str] = []

    if cat in {"session_stuck", "context_overflow", "whatsapp_pending"}:
        actions.append(remediate_clear_whatsapp_and_reset())
    elif cat == "gateway_unhealthy":
        actions.append(remediate_restart_gateway())
    else:
        return {
            "status": "skip",
            "finding_id": row.get("finding_id"),
            "message": f"Sin playbook auto para {cat}",
        }

    verified = gateway_healthy() and whatsapp_pending_count() == 0
    commit_info = {}
    if do_commit and verified:
        commit_info = git_commit_push(f"fix(supp): {row.get('summary', cat)[:60]}")

    update_finding(
        row["finding_id"],
        {
            "status": "remediated" if verified else "failed",
            "remediated_at": now_iso(),
            "remediation_action": " | ".join(actions)[:500],
            "verified_at": now_iso() if verified else "",
            "commit_hash": (commit_info.get("commit") or "")[:64],
        },
    )

    summary = (
        f"Fix {row.get('category')}: {'OK' if verified else 'parcial'}\n"
        f"Gateway: {'healthy' if gateway_healthy() else 'revisar'}\n"
        f"Pending WA: {whatsapp_pending_count()}\n"
        f"Commit: {commit_info.get('commit', 'ninguno')}"
    )
    return {
        "status": "ok" if verified else "partial",
        "finding_id": row.get("finding_id"),
        "verified": verified,
        "commit": commit_info,
        "summary": summary,
        "whatsapp_reply": summary,
    }


def remediate_auto(*, do_commit: bool) -> dict:
    targets = pick_open_findings()
    if not targets:
        msg = "Sin hallazgos abiertos con playbook auto."
        return {"status": "ok", "fixed": 0, "summary": msg, "whatsapp_reply": msg}

    results = [_apply_fix(row, do_commit=do_commit) for row in targets[:3]]
    fixed = sum(1 for r in results if r.get("verified"))
    summary = f"Remediados: {fixed}/{len(results)}\n" + "\n".join(
        r.get("summary", "")[:120] for r in results
    )
    return {
        "status": "ok",
        "fixed": fixed,
        "results": results,
        "summary": summary,
        "whatsapp_reply": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Remedia hallazgos /supp")
    parser.add_argument("--finding-id", default="")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--no-commit", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.finding_id:
        result = remediate_finding(args.finding_id, do_commit=not args.no_commit)
    elif args.auto:
        result = remediate_auto(do_commit=not args.no_commit)
    else:
        result = {"status": "error", "message": "Usa --auto o --finding-id"}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result.get("whatsapp_reply") or result.get("summary") or result.get("message"))


if __name__ == "__main__":
    main()
