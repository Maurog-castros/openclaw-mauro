#!/usr/bin/env bash
# Resetea sesión WhatsApp del agente content (context overflow / sesión vieja).
set -eu
REPO="${OPENCLAW_REPO:-/home/mauro/openclaw-mauro}"
STAMP="$(date +%Y%m%d-%H%M%S)"
export REPO STAMP
python3 <<'PY'
import json
import os
from pathlib import Path
REPO = Path(os.environ["REPO"])
stamp = os.environ["STAMP"]
path = REPO / "data/config/agents/content/sessions/sessions.json"
data = json.loads(path.read_text(encoding="utf-8"))
path.with_suffix(path.suffix + f".bak-reset-{stamp}").write_text(
    path.read_text(encoding="utf-8"), encoding="utf-8"
)
entry = data.pop("agent:content:main", None)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if entry:
    sid = entry.get("sessionId", "")
    print("removed agent:content:main sid=", sid)
    jl = REPO / "data/config/agents/content/sessions" / f"{sid}.jsonl"
    if jl.exists():
        jl.rename(jl.with_suffix(f".jsonl.bak-reset-{stamp}"))
        print("archived", jl.name)
PY
echo "Listo. Prueba de nuevo por WhatsApp."
