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

RUN_PY = ROOT / "scripts/run-finanzas-py.sh"
SCR = ROOT / "scripts"
INBOUND_CANDIDATES = [
    ROOT / "data/config/media/inbound",
    Path("/home/node/.openclaw/media/inbound"),
    Path("/home/mauro/openclaw-mauro/data/config/media/inbound"),
]

INTEL_RE = re.compile(r"^\s*/intel\b", re.I)
CONTENT_RE = re.compile(r"^\s*/content\b|instagram\.com/(?:p|reel)/", re.I)
RECENT_RECEIPTS_RE = re.compile(
    r"\b(ultim(?:as|os)|recientes|procesad(?:as|os)|historial)\b.*\b(boleta?s?|ticket?s?|recibos?)\b"
    r"|\b(boleta?s?|ticket?s?|recibos?)\b.*\b(ultim(?:as|os)|recientes|procesad(?:as|os))\b"
    r"|\bcuales?\s+(?:son\s+)?(?:las?\s+)?ultim(?:as|os)\b",
    re.I,
)
SKIP_CMD_RE = re.compile(r"^\s*/(?:new|reset|status|help)\b", re.I)
SALDO_RE = re.compile(
    r"\bsaldo\b|cuenta\s+corriente|\bsantander\b|\bdisponible\b"
    r"|este\s+es\s+mi\s+saldo|mi\s+saldo\s+es|saldo\s+real|captura|screenshot",
    re.I,
)
BOLETA_RE = re.compile(
    r"\b(boleta|ticket|compra|recibo|foto|supermercado|farmacia|minimarket)\b",
    re.I,
)
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


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


def run_recent_receipts(limit: int = 10) -> dict:
    code, payload, stdout, stderr = run_json(
        py_cmd("finanzas_recent_receipts.py", "--limit", str(limit), "--json")
    )
    if code != 0 and not payload.get("whatsapp_reply"):
        return {
            "status": "error",
            "agent": "fin",
            "whatsapp_reply": "No pude listar boletas recientes.",
            "stderr": stderr[-800:],
        }
    payload.setdefault("agent", "fin")
    payload.setdefault("status", "ok")
    return payload


def run_saldo(text: str, image_path: str | None) -> dict:
    cmd = py_cmd("finanzas_saldo_whatsapp.py", "--text", text, "--json")
    if image_path:
        cmd.extend(["--image", image_path])
    code, payload, stdout, stderr = run_json(cmd, timeout=120)
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


FIN_PREFIX_RE = re.compile(r"^\s*/(?:fin|finanzas)\b\s*", re.I)


def strip_fin_prefix(text: str) -> str:
    return FIN_PREFIX_RE.sub("", text or "").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Delegate finanzas WhatsApp.")
    parser.add_argument("--text", default="")
    parser.add_argument("--has-media", action="store_true", help="Mensaje trae imagen adjunta.")
    parser.add_argument("--image", help="Ruta explicita inbound.")
    parser.add_argument("--source", default="whatsapp_foto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = strip_fin_prefix((args.text or "").strip())
    image_path = args.image or (str(latest_inbound_image()) if args.has_media else None)

    if SKIP_CMD_RE.search(text):
        payload = {"status": "skip", "agent": "fin", "whatsapp_reply": ""}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "")
        return

    if INTEL_RE.search(text):
        code, payload, stdout, stderr = run_json(py_cmd("intel_delegate.py", "--text", text, "--json"))
        if code != 0 and not payload.get("whatsapp_reply"):
            payload = {
                "status": "error",
                "whatsapp_reply": "Intel no respondio. Intenta de nuevo.",
                "stderr": stderr[-800:],
            }
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload.get("whatsapp_reply", ""))
        return

    if CONTENT_RE.search(text):
        code, payload, stdout, stderr = run_json(py_cmd("content_instagram_whatsapp.py", "--text", text, "--json"))
        if code != 0 and not payload.get("whatsapp_reply"):
            payload = {"status": "error", "whatsapp_reply": payload.get("message", "Content no respondio.")}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload.get("whatsapp_reply", ""))
        return

    if RECENT_RECEIPTS_RE.search(text):
        result = run_recent_receipts()
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result.get("whatsapp_reply", ""))
        return

    if should_process_saldo(text, args.has_media, image_path):
        result = run_saldo(text, image_path)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result.get("whatsapp_reply", ""))
        return

    if should_process_receipt(text, args.has_media, image_path):
        result = run_receipt(text, args.source, image_path)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result.get("whatsapp_reply", ""))
        return

    print(
        json.dumps({"status": "delegate_miss", "agent": "finanzas"}, ensure_ascii=False)
        if args.json
        else ""
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
