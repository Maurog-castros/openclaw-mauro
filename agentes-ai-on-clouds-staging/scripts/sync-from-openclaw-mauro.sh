#!/usr/bin/env bash
# Copia READ-ONLY desde el entorno legacy hacia este repo.
# NO modifica /home/mauro/openclaw-mauro (producción sigue igual).
set -euo pipefail

SRC="${OPENCLAW_LEGACY_ROOT:-/home/mauro/openclaw-mauro}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: origen no existe: $SRC" >&2
  exit 1
fi

log() { echo "[sync $STAMP] $*"; }

RSYNC_EXCLUDES=(
  --exclude '__pycache__/'
  --exclude '*.pyc'
  --exclude '*.pyo'
  --exclude '.pytest_cache/'
  --exclude '*.bak'
  --exclude '*.bak-*'
  --exclude 'finanzas-SOUL-content-delegate.md'
)

mkdir -p \
  "$REPO_ROOT/apps/openclaw/scripts" \
  "$REPO_ROOT/apps/openclaw/config" \
  "$REPO_ROOT/apps/openclaw/docker" \
  "$REPO_ROOT/apps/openclaw/agents" \
  "$REPO_ROOT/apps/openclaw/workspaces/skills" \
  "$REPO_ROOT/apps/openclaw/cron" \
  "$REPO_ROOT/apps/litellm" \
  "$REPO_ROOT/apps/memory-services" \
  "$REPO_ROOT/apps/open-webui" \
  "$REPO_ROOT/docs/runbooks" \
  "$REPO_ROOT/docs/operations" \
  "$REPO_ROOT/secrets.example"

log "Origen (solo lectura): $SRC"
log "Destino: $REPO_ROOT"

# --- Scripts agentes ---
log "scripts/ -> apps/openclaw/scripts/"
rsync -a "${RSYNC_EXCLUDES[@]}" \
  "$SRC/scripts/" \
  "$REPO_ROOT/apps/openclaw/scripts/"

# --- Config versionable ---
if [[ -d "$SRC/config" ]]; then
  log "config/ -> apps/openclaw/config/"
  rsync -a "${RSYNC_EXCLUDES[@]}" \
    "$SRC/config/" \
    "$REPO_ROOT/apps/openclaw/config/"
fi

# --- Docker / compose (sin backups) ---
log "docker compose + overrides"
for f in docker-compose.yml docker-compose.finanzas-mounts.yml .env.example; do
  if [[ -f "$SRC/openclaw/$f" ]]; then
    cp -a "$SRC/openclaw/$f" "$REPO_ROOT/apps/openclaw/docker/"
  fi
done
if [[ -d "$SRC/docker-overrides/openclaw-with-ssh" ]]; then
  rsync -a --exclude '*.bak*' --exclude 'Dockerfile.bak*' \
    "$SRC/docker-overrides/openclaw-with-ssh/" \
    "$REPO_ROOT/apps/openclaw/docker/openclaw-with-ssh/"
fi
if [[ -f "$SRC/openclaw/deploy/Dockerfile" ]]; then
  mkdir -p "$REPO_ROOT/apps/openclaw/docker/deploy"
  cp -a "$SRC/openclaw/deploy/Dockerfile" "$REPO_ROOT/apps/openclaw/docker/deploy/"
fi

# --- LiteLLM ---
if [[ -f "$SRC/openclaw/litellm-config.yaml" ]]; then
  cp -a "$SRC/openclaw/litellm-config.yaml" "$REPO_ROOT/apps/litellm/litellm-config.yaml"
fi
cp -a "$REPO_ROOT/apps/litellm/litellm-config.yaml" "$REPO_ROOT/apps/litellm/litellm-config.example.yaml" 2>/dev/null || true

# --- Memory services (fragmento desde compose) ---
cat > "$REPO_ROOT/apps/memory-services/README.md" <<'EOF'
# Memory services

Postgres (pgvector) + Redis usados por OpenClaw.

En bare-metal hoy corren como contenedores `postgres-memory` y `redis-memory`
definidos en `apps/openclaw/docker/docker-compose.yml`.

En cloud: desplegar vía `infra/k8s/base/memory/` o servicios gestionados (RDS/Cloud SQL + Memorystore/Elasticache).
EOF

# --- Agent SOUL + plantillas workspace ---
copy_soul() {
  local agent_id="$1"
  local soul_path="$2"
  local dest="$REPO_ROOT/apps/openclaw/agents/$agent_id"
  mkdir -p "$dest"
  if [[ -f "$soul_path" ]]; then
    cp -a "$soul_path" "$dest/SOUL.md"
    log "  SOUL: $agent_id"
  fi
}

log "Agentes (SOUL.md)"
copy_soul finanzas "$SRC/data/workspace/marketing/finanzas/SOUL.md"
copy_soul content  "$SRC/data/workspace/marketing/content/SOUL.md"
copy_soul intel    "$SRC/data/workspace/marketing/intel/SOUL.md"
copy_soul sales    "$SRC/data/workspace/marketing/sales/SOUL.md"
copy_soul pyme-chile "$SRC/data/workspace/pyme-chile/SOUL.md"

for agent_dir in "$REPO_ROOT/apps/openclaw/agents/"*/; do
  [[ -d "$agent_dir" ]] || continue
  id="$(basename "$agent_dir")"
  if [[ ! -f "$agent_dir/README.md" ]]; then
    cat > "$agent_dir/README.md" <<EOF
# Agente \`$id\`

- \`SOUL.md\`: identidad y reglas (copiado desde legacy workspace).
- Scripts: ver \`apps/openclaw/scripts/\` y runbooks en \`docs/runbooks/\`.
EOF
  fi
done

# --- Skills (plantillas, sin backups openclaw) ---
if [[ -d "$SRC/data/workspace/skills" ]]; then
  log "skills/ -> apps/openclaw/workspaces/skills/"
  rsync -a --exclude '.openclaw-install-backups' \
    "$SRC/data/workspace/skills/" \
    "$REPO_ROOT/apps/openclaw/workspaces/skills/"
fi

# --- Docs legacy ---
if [[ -f "$SRC/MARKETING-AGENTS-ORCHESTRATOR.md" ]]; then
  cp -a "$SRC/MARKETING-AGENTS-ORCHESTRATOR.md" "$REPO_ROOT/docs/MARKETING-AGENTS-ORCHESTRATOR.md"
fi
for rb in "$SRC/scripts"/README-*.md; do
  [[ -f "$rb" ]] && cp -a "$rb" "$REPO_ROOT/docs/runbooks/" || true
done

# --- Cron referencia (host) ---
if crontab -l 2>/dev/null | grep -q openclaw-mauro; then
  crontab -l 2>/dev/null | grep openclaw-mauro > "$REPO_ROOT/docs/operations/cron.host.snapshot.txt" || true
  log "Cron snapshot -> docs/operations/cron.host.snapshot.txt"
fi

# --- openclaw.json plantilla (redactada) ---
python3 - "$SRC" "$REPO_ROOT" <<'PY'
import json, re, sys
from pathlib import Path

src, repo = Path(sys.argv[1]), Path(sys.argv[2])
cfg_path = src / "data/config/openclaw.json"
out = repo / "apps/openclaw/config/openclaw.example.json"
if not cfg_path.is_file():
    sys.exit(0)

raw = cfg_path.read_text(encoding="utf-8")
# Redactar tokens y claves obvias
redacted = re.sub(r'"(apiKey|botToken|token|password|secret|master_key)"\s*:\s*"[^"]*"',
                  lambda m: f'"{m.group(1)}": "REDACTED"', raw, flags=re.I)
redacted = re.sub(r'"(api_key)"\s*:\s*"[^"]*"', r'"\1": "REDACTED"', redacted, flags=re.I)
try:
    data = json.loads(redacted)
except json.JSONDecodeError:
    out.write_text('{"_error": "could not parse redacted config"}\n', encoding="utf-8")
    sys.exit(0)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "_comment": "Plantilla derivada de produccion; revisar antes de commit. Sin secretos.",
    "_source": str(cfg_path),
    "config": data,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"  openclaw.example.json ({out.stat().st_size} bytes)")
PY

# --- secrets.example (solo plantillas; nunca copiar secrets/) ---
if [[ -f "$SRC/secrets/whatsapp_allow_from.txt" ]]; then
  sed 's/+[0-9]\{9,\}/+569XXXXXXXX/' "$SRC/secrets/whatsapp_allow_from.txt" \
    > "$REPO_ROOT/secrets.example/whatsapp_allow_from.example.txt" 2>/dev/null || true
fi

log "Sync completado. Produccion en $SRC no fue modificada."
