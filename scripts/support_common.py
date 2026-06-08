"""Utilidades agente soporte OpenClaw (/supp)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path("/home/mauro/openclaw-mauro")
if not REPO_ROOT.exists():
    REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_FINDINGS_CSV = REPO_ROOT / "data/support_findings.csv"
DEFAULT_SQLITE = REPO_ROOT / "data/config/state/openclaw.sqlite"
DEFAULT_SESSIONS_JSON = REPO_ROOT / "data/config/agents/finanzas/sessions/sessions.json"
GATEWAY_CONTAINER = "openclaw-openclaw-gateway-1"
OPENCLAW_LOG_GLOB = "/tmp/openclaw/openclaw-*.log"

FINDINGS_COLUMNS = [
    "finding_id",
    "detected_at",
    "severity",
    "category",
    "source_log",
    "summary",
    "detail",
    "status",
    "remediated_at",
    "remediation_action",
    "verified_at",
    "commit_hash",
]

AUTO_FIX_CATEGORIES = frozenset(
    {"session_stuck", "context_overflow", "whatsapp_pending", "gateway_unhealthy"}
)

FIXABLE_STATUSES = frozenset({"open", "failed"})


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def run_cmd(cmd: List[str], *, timeout: int = 120, cwd: Optional[Path] = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def docker_logs(tail: int = 200) -> str:
    code, out, err = run_cmd(["docker", "logs", GATEWAY_CONTAINER, "--tail", str(tail)], timeout=60)
    return out + err if code == 0 else err or out


def docker_exec_tail_log(lines: int = 300) -> str:
    code, out, err = run_cmd(
        [
            "docker",
            "exec",
            GATEWAY_CONTAINER,
            "sh",
            "-c",
            f"tail -n {lines} {OPENCLAW_LOG_GLOB} 2>/dev/null || true",
        ],
        timeout=60,
    )
    return out or err


def gateway_healthy() -> bool:
    code, out, _ = run_cmd(
        [
            "docker",
            "inspect",
            GATEWAY_CONTAINER,
            "--format",
            "{{.State.Health.Status}}",
        ],
        timeout=30,
    )
    return code == 0 and "healthy" in (out or "").lower()


def whatsapp_pending_count() -> int:
    if not DEFAULT_SQLITE.exists():
        return 0
    import sqlite3

    con = sqlite3.connect(DEFAULT_SQLITE)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT count(*) FROM plugin_state_entries "
            "WHERE plugin_id='whatsapp' AND namespace LIKE 'inbound.v1.pending%'"
        )
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        con.close()


def fin_failed_delivery_count() -> int:
    if not DEFAULT_SQLITE.exists():
        return 0
    import sqlite3

    con = sqlite3.connect(DEFAULT_SQLITE)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT count(*) FROM delivery_queue_entries "
            "WHERE status='failed' AND (session_key LIKE 'agent:fin%' OR session_key LIKE 'agent:finanzas%')"
        )
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        con.close()


def live_health() -> Dict[str, Any]:
    sess = fin_main_session_status()
    pending = whatsapp_pending_count()
    failed_del = fin_failed_delivery_count()
    healthy = gateway_healthy()
    session_running = (sess.get("status") or "") == "running"
    needs_fix = (
        not healthy
        or pending > 0
        or session_running
        or failed_del > 0
    )
    return {
        "gateway_healthy": healthy,
        "whatsapp_pending": pending,
        "fin_session": sess,
        "fin_session_running": session_running,
        "fin_failed_deliveries": failed_del,
        "needs_remediation": needs_fix,
    }


def fin_main_session_status() -> Dict[str, Any]:
    if not DEFAULT_SESSIONS_JSON.exists():
        return {}
    try:
        data = json.loads(DEFAULT_SESSIONS_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    entry = data.get("agent:fin:main") or {}
    return {
        "status": entry.get("status"),
        "session_id": entry.get("sessionId"),
        "updated_at": entry.get("updatedAt") or entry.get("updated_at"),
    }


def finding_fingerprint(category: str, summary: str) -> str:
    raw = f"{category}|{summary}"[:500]
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def ensure_findings_csv(path: Path = DEFAULT_FINDINGS_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=FINDINGS_COLUMNS).writeheader()


def load_findings(path: Path = DEFAULT_FINDINGS_CSV) -> List[Dict[str, str]]:
    ensure_findings_csv(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_finding(row: Dict[str, Any], path: Path = DEFAULT_FINDINGS_CSV) -> Dict[str, str]:
    ensure_findings_csv(path)
    entry = {col: str(row.get(col) or "") for col in FINDINGS_COLUMNS}
    if not entry["finding_id"]:
        entry["finding_id"] = uuid.uuid4().hex[:12]
    if not entry["detected_at"]:
        entry["detected_at"] = now_iso()
    if not entry["status"]:
        entry["status"] = "open"

    existing = load_findings(path)
    fp = finding_fingerprint(entry["category"], entry["summary"])
    for old in existing:
        if old.get("status") in FIXABLE_STATUSES and finding_fingerprint(
            old.get("category", ""), old.get("summary", "")
        ) == fp:
            return old

    with path.open("a", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=FINDINGS_COLUMNS).writerow(entry)
    return entry


def reopen_failed_findings(categories: Optional[List[str]] = None, path: Path = DEFAULT_FINDINGS_CSV) -> int:
    """Marca failed -> open para permitir reintento de auto-fix."""
    rows = load_findings(path)
    changed = 0
    for row in rows:
        if row.get("status") != "failed":
            continue
        cat = row.get("category") or ""
        if categories and cat not in categories:
            continue
        if cat not in AUTO_FIX_CATEGORIES:
            continue
        row["status"] = "open"
        changed += 1
    if changed:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FINDINGS_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
    return changed


def update_finding(
    finding_id: str,
    updates: Dict[str, str],
    path: Path = DEFAULT_FINDINGS_CSV,
) -> Optional[Dict[str, str]]:
    rows = load_findings(path)
    changed = False
    for row in rows:
        if row.get("finding_id") == finding_id:
            row.update({k: str(v) for k, v in updates.items()})
            changed = True
            break
    if not changed:
        return None
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINDINGS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return next(r for r in rows if r.get("finding_id") == finding_id)


def parse_log_findings(log_text: str) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    if re.search(r"stalled session:.*agent:fin:main", log_text):
        findings.append(
            {
                "severity": "critical",
                "category": "session_stuck",
                "source_log": "openclaw-gateway",
                "summary": "Sesion agent:fin:main atascada (stalled_agent_run)",
                "detail": "queueDepth>0 sin progreso LLM",
            }
        )
    if "context-overflow-precheck" in log_text:
        findings.append(
            {
                "severity": "critical",
                "category": "context_overflow",
                "source_log": "openclaw-gateway",
                "summary": "Context overflow en agent:fin:main",
                "detail": "Historial/tool results exceden ventana; requiere reset sesion",
            }
        )
    if "Ollama could not be reached" in log_text:
        findings.append(
            {
                "severity": "info",
                "category": "ollama_unreachable",
                "source_log": "openclaw-gateway",
                "summary": "Ollama 127.0.0.1:11434 no alcanzable",
                "detail": "Vision local fallo; remoto LiteLLM puede seguir OK",
            }
        )
    if "remaining bootstrap budget is 1 chars" in log_text:
        findings.append(
            {
                "severity": "warning",
                "category": "bootstrap_budget",
                "source_log": "openclaw-gateway",
                "summary": "SOUL/USER truncado por budget bootstrap",
                "detail": "Reducir SOUL o USER.md para agente fin",
            }
        )
    return findings


def git_commit_push(message: str) -> Dict[str, str]:
    run_cmd(["git", "add", "data/support_findings.csv", "scripts/"])
    code, out, err = run_cmd(["git", "commit", "-m", message], timeout=60)
    if code != 0 and "nothing to commit" in (out + err):
        return {"status": "skip", "message": "sin cambios para commit"}
    if code != 0:
        return {"status": "error", "message": (err or out)[:500]}
    _, log_out, _ = run_cmd(["git", "log", "-1", "--format=%H %s"])
    hash_line = (log_out or "").strip()
    push_code, push_out, push_err = run_cmd(["git", "push"], timeout=120)
    if push_code != 0:
        return {"status": "committed_no_push", "message": (push_err or push_out)[:500], "commit": hash_line}
    return {"status": "ok", "commit": hash_line, "message": "push ok"}
