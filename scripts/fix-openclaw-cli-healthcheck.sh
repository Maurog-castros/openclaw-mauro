#!/usr/bin/env bash
set -euo pipefail
COMPOSE="/home/mauro/openclaw-mauro/openclaw/docker-compose.yml"
python3 - <<'PY'
from pathlib import Path
p = Path("/home/mauro/openclaw-mauro/openclaw/docker-compose.yml")
text = p.read_text()
bad = 'fetch(http://openclaw-gateway:18789/healthz)'
good = "fetch('http://openclaw-gateway:18789/healthz')"
if bad not in text:
    raise SystemExit(f"missing pattern: {bad}")
p.write_text(text.replace(bad, good, 1))
print("patched healthcheck URL quotes")
PY
cd /home/mauro/openclaw-mauro/openclaw
docker compose up -d --force-recreate openclaw-cli
sleep 40
docker inspect openclaw-openclaw-cli-1 --format 'health={{.State.Health.Status}}'
