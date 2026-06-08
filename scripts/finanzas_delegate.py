"""Delegacion deterministica finanzas: boletas foto, /intel, /content."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/node/openclaw-mauro")
if not ROOT.exists():
    ROOT = Path(__file__).resolve().parent.parent

SCR = ROOT / "scripts"
if str(SCR) not in sys.path:
    sys.path.insert(0, str(SCR))

from whatsapp_menu import MenuOption, finish_reply, resolve_menu_choice

RUN_PY = ROOT / "scripts/run-finanzas-py.sh"
INBOUND_CANDIDATES = [
    ROOT / "data/config/media/inbound",
    Path("/home/node/.openclaw/media/inbound"),
    Path("/home/mauro/openclaw-mauro/data/config/media/inbound"),
]

SUPP_RE = re.compile(r"^\s*/supp\b", re.I)
INTEL_RE = re.compile(r"^\s*/intel\b", re.I)
CONTENT_RE = re.compile(r"^\s*/content\b|instagram\.com/(?:p|reel)/", re.I)
RECENT_RECEIPTS_RE = re.compile(
    r"\b(ultim(?:as|os)|recientes|procesad(?:as|os)|historial)\b.*\b(boleta?s?|ticket?s?|recibos?)\b"
    r"|\b(boleta?s?|ticket?s?|recibos?)\b.*\b(ultim(?:as|os)|recientes|procesad(?:as|os))\b"
    r"|\bcuales?\s+(?:son\s+)?(?:las?\s+)?ultim(?:as|os)\b",
    re.I,
)
RECENT_RECEIPTS_LIMIT_RE = re.compile(r"\b(\d{1,2})\s*(?:ultim(?:as|os))?\s*boleta", re.I)
SKIP_CMD_RE = re.compile(r"^\s*/(?:new|reset|status|help)\b", re.I)
SALDO_RE = re.compile(
    r"\bsaldo\b|cuenta\s+corriente|\bsantander\b|\bdisponible\b"
    r"|este\s+es\s+mi\s+saldo|mi\s+saldo\s+es|saldo\s+real|captura|screenshot",
    re.I,
)
DEDUPE_RE = re.compile(
    r"\b(duplicad|mismo\s+monto|otra\s+vez|corrige|es\s+la\s+misma|misma\s+transacc)\b",
    re.I,
)
BOLETA_RE = re.compile(
    r"\b(boleta|ticket|compra|recibo|foto|supermercado|farmacia|minimarket)\b",
    re.I,
)
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
FIN_PREFIX_RE = re.compile(r"^\s*/(?:fin|finanzas)\b\s*", re.I)


def py_cmd(script: str, *args: str) -> list[str]:
    return [str(RUN_PY), str(SCR / script), *args]


def run_json(cmd: list[str], timeout: int = 200) -> tuple[int, dict, str, str]:
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout, check=False)
    payload: dict = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"whatsapp_reply": proc.stdout.strip()}
    return proc.returncode, payload, proc.stdout, proc.stderr


def emit(payload: dict, *, as_json: bool, agent: str = "fin", skip_menu: bool = False) -> None:
    reply = payload.get("whatsapp_reply") or payload.get("summary") or ""
    if reply and payload.get("status") not in {"skip", "delegate_miss"}:
        menu_agent = payload.get("agent") or agent
        if menu_agent not in ("fin", "supp"):
            menu_agent = "fin"
        payload["whatsapp_reply"] = finish_reply(reply, agent=menu_agent, skip_menu=skip_menu)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("whatsapp_reply", ""))


def strip_fin_prefix(text: str) -> str:
    return FIN_PREFIX_RE.sub("", text or "").strip()


def resolve_inbound() -> Path:
    for candidate in INBOUND_CANDIDATES:
        if candidate.exists():
            return candidate
    return INBOUND_CANDIDATES[0]


def latest_inbound_image(max_age_sec: int = 120) -> Path | None:
    inbound = resolve_inbound()
    if not inbound.exists():
        return None
    now = time.time()
    candidates = [
        p
        for p in inbound.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXT and (now - p.stat().st_mtime) <= max_age_sec
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def run_script_menu(value: str) -> dict:
    parts = value.split("|")
    script = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    code, payload, _, stderr = run_json(py_cmd(script, *args, "--json"))
    if code != 0 and not payload.get("whatsapp_reply") and not payload.get("summary"):
        return {"status": "error", "agent": "fin", "whatsapp_reply": stderr[:400] or "Error ejecutando accion."}
    payload.setdefault("agent", "fin")
    payload.setdefault("status", "ok")
    payload.setdefault("whatsapp_reply", payload.get("summary") or "")
    return payload


def run_menu_option(opt: MenuOption) -> dict:
    if opt.kind == "text":
        return dispatch_text(opt.value, has_media=False, image_path=None, amount=0)
    if opt.kind == "script":
        return run_script_menu(opt.value)
    if opt.kind == "monthly":
        code, payload, _, stderr = run_json(
            py_cmd("finanzas_monthly_report.py", "--month", opt.value, "--json")
        )
        if code != 0:
            return {"status": "error", "agent": "fin", "whatsapp_reply": stderr[:400] or "Sin reporte mensual."}
        payload.setdefault("whatsapp_reply", payload.get("summary") or "")
        payload.setdefault("agent", "fin")
        return payload
    if opt.kind == "supp":
        code, payload, _, stderr = run_json(
            py_cmd("support_delegate.py", "--text", f"/supp {opt.value}", "--json")
        )
        payload.setdefault("agent", "supp")
        if code != 0 and not payload.get("whatsapp_reply"):
            payload["whatsapp_reply"] = stderr[:400] or "Supp no respondio."
        return payload
    return {"status": "error", "agent": "fin", "whatsapp_reply": "Opcion de menu desconocida."}


def should_process_dedupe(text: str) -> bool:
    if not DEDUPE_RE.search(text or ""):
        return False
    t = text or ""
    if re.search(r"\$\s*\d{1,3}(?:\.\d{3})+|\d{5,}", t):
        return True
    if re.search(r"\b(TRANSF|RENOVAL|arriendo)\b", t, re.I):
        return True
    return False


def run_dedupe(text: str) -> dict:
    code, payload, _, stderr = run_json(py_cmd("finanzas_dedupe_movimientos.py", "auto-link", "--text", text, "--json"))
    if code != 0 and not payload.get("whatsapp_reply"):
        return {
            "status": "error",
            "agent": "fin",
            "whatsapp_reply": "No pude vincular duplicados. Indica monto y nombre (ej. RENOVAL).",
            "stderr": stderr[-800:],
        }
    payload.setdefault("agent", "fin")
    payload.setdefault("status", payload.get("status", "ok"))
    return payload


def should_process_saldo(text: str, has_media: bool, image_path: str | None) -> bool:
    t = (text or "").strip()
    if SALDO_RE.search(t):
        return True
    try:
        from finanzas_saldo import parse_balance_text

        if parse_balance_text(t):
            return True
    except ImportError:
        pass
    return False


def should_process_receipt(text: str, has_media: bool, image_path: str | None) -> bool:
    if SKIP_CMD_RE.search(text):
        return False
    if RECENT_RECEIPTS_RE.search(text):
        return False
    if should_process_saldo(text, has_media, image_path):
        return False
    if BOLETA_RE.search(text):
        return True
    if has_media or image_path:
        latest = latest_inbound_image()
        if not image_path and not latest:
            return False
        t = (text or "").strip()
        if len(t) >= 140:
            return False
        if SALDO_RE.search(t):
            return False
        return bool(BOLETA_RE.search(t) or len(t) < 80)
    if latest_inbound_image():
        return bool(BOLETA_RE.search(text) or len((text or "").strip()) < 80)
    return False


def parse_recent_receipts_limit(text: str, default: int = 10) -> int:
    m = RECENT_RECEIPTS_LIMIT_RE.search(text or "")
    if m:
        return max(1, min(int(m.group(1)), 20))
    m2 = re.search(r"\b(\d{1,2})\s+boleta", text or "", re.I)
    if m2:
        return max(1, min(int(m2.group(1)), 20))
    return default


def run_recent_receipts(limit: int = 10) -> dict:
    code, payload, _, stderr = run_json(py_cmd("finanzas_recent_receipts.py", "--limit", str(limit), "--json"))
    if code != 0 and not payload.get("whatsapp_reply"):
        return {"status": "error", "agent": "fin", "whatsapp_reply": "No pude listar boletas recientes.", "stderr": stderr[-800:]}
    payload.setdefault("agent", "fin")
    payload.setdefault("status", "ok")
    return payload


def run_saldo(text: str, image_path: str | None, amount: int | None = None) -> dict:
    cmd = py_cmd("finanzas_saldo_whatsapp.py", "--text", text, "--json")
    if amount is not None and amount > 0:
        cmd.extend(["--amount", str(amount)])
    if image_path:
        cmd.extend(["--image", image_path])
    code, payload, _, stderr = run_json(cmd, timeout=120)
    if code != 0 and not payload.get("whatsapp_reply"):
        return {
            "status": "error",
            "agent": "fin",
            "whatsapp_reply": "No pude procesar el saldo. Intenta con el monto en texto.",
            "stderr": stderr[-800:],
        }
    payload.setdefault("agent", "fin")
    payload.setdefault("status", payload.get("status", "ok"))
    return payload


def run_receipt(text: str, source: str, image_path: str | None) -> dict:
    inbound = resolve_inbound()
    cmd = py_cmd(
        "finanzas_receipt_whatsapp.py",
        "--text",
        text,
        "--inbound-dir",
        str(inbound),
        "--source",
        source,
        "--json",
    )
    if image_path:
        cmd.extend(["--image", image_path])
    code, payload, stdout, stderr = run_json(cmd, timeout=200)
    if code != 0 and not payload.get("whatsapp_reply"):
        return {
            "status": "error",
            "agent": "finanzas",
            "whatsapp_reply": "No pude procesar la boleta. Revisa logs del gateway.",
            "stderr": stderr[-1000:],
            "stdout": stdout[-1000:],
        }
    payload.setdefault("agent", "finanzas")
    payload.setdefault("status", payload.get("status", "ok"))
    return payload


def dispatch_text(
    text: str,
    *,
    has_media: bool,
    image_path: str | None,
    amount: int,
    raw_text: str = "",
) -> dict:
    if SUPP_RE.search(raw_text or ""):
        code, payload, _, stderr = run_json(py_cmd("support_delegate.py", "--text", raw_text or "", "--json"))
        if code != 0 and not payload.get("whatsapp_reply"):
            payload = {"status": "error", "agent": "supp", "whatsapp_reply": "Supp no respondio.", "stderr": stderr[-800:]}
        payload.setdefault("agent", "supp")
        return payload

    if INTEL_RE.search(text):
        code, payload, _, stderr = run_json(py_cmd("intel_delegate.py", "--text", text, "--json"))
        if code != 0 and not payload.get("whatsapp_reply"):
            payload = {"status": "error", "whatsapp_reply": "Intel no respondio.", "stderr": stderr[-800:]}
        payload.setdefault("agent", "fin")
        return payload

    if CONTENT_RE.search(text):
        code, payload, _, _ = run_json(py_cmd("content_instagram_whatsapp.py", "--text", text, "--json"))
        if code != 0 and not payload.get("whatsapp_reply"):
            payload = {"status": "error", "whatsapp_reply": payload.get("message", "Content no respondio.")}
        payload.setdefault("agent", "fin")
        return payload

    if RECENT_RECEIPTS_RE.search(text):
        return run_recent_receipts(parse_recent_receipts_limit(text))

    if should_process_dedupe(text):
        return run_dedupe(text)

    if amount and amount > 0:
        return run_saldo(text, image_path, amount=amount)

    if should_process_saldo(text, has_media, image_path):
        return run_saldo(text, image_path, amount=amount if amount else None)

    if should_process_receipt(text, has_media, image_path):
        return run_receipt(text, "whatsapp_foto", image_path)

    return {"status": "delegate_miss", "agent": "finanzas", "whatsapp_reply": ""}


def main() -> None:
    parser = argparse.ArgumentParser(description="Delegate finanzas WhatsApp.")
    parser.add_argument("--text", default="")
    parser.add_argument("--amount", type=int, default=0)
    parser.add_argument("--has-media", action="store_true")
    parser.add_argument("--image", default=None)
    parser.add_argument("--source", default="whatsapp_foto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raw_text = (args.text or "").strip()
    text = strip_fin_prefix(raw_text)
    image_path = args.image or (str(latest_inbound_image()) if args.has_media else None)

    if SKIP_CMD_RE.search(text):
        emit({"status": "skip", "agent": "fin", "whatsapp_reply": ""}, as_json=args.json, skip_menu=True)
        return

    menu_opt = resolve_menu_choice(text)
    if menu_opt:
        emit(run_menu_option(menu_opt), as_json=args.json)
        return

    result = dispatch_text(
        text,
        has_media=args.has_media,
        image_path=image_path,
        amount=int(args.amount or 0),
        raw_text=raw_text,
    )

    if result.get("status") == "delegate_miss":
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        sys.exit(2)
        return

    emit(result, as_json=args.json)


if __name__ == "__main__":
    main()
