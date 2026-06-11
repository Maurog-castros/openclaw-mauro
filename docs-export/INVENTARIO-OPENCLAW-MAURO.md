# Inventario: `/home/mauro/openclaw-mauro` → `agentes-ai-on-clouds`

**Fecha:** 2026-06-03  
**Origen:** servidor Ubuntu `mauro@192.168.1.12`  
**Destino repo:** `/home/mauro/agentes-ai-on-clouds`  
**OpenClaw:** 2026.5.31 (aprox.)

---

## 1. Resumen ejecutivo

| Componente | Estado en servidor | Subir al repo |
|------------|-------------------|---------------|
| OpenClaw gateway + CLI | Docker `openclaw-with-ssh:local` | `apps/openclaw/docker` + submodule o referencia |
| LiteLLM | `openclaw-litellm-1` | `apps/litellm` |
| Memoria (Postgres+pgvector, Redis) | `postgres-memory`, `redis-memory` | `apps/memory-services` |
| Open WebUI | contenedor aparte | `apps/open-webui` |
| Jenkins | `jenkins-devops` | `cicd/jenkins` |
| Agentes custom (Python) | `scripts/` | `apps/openclaw/scripts` |
| Config agentes / SOUL | `config/` + `data/workspace/` | `apps/openclaw/config` + `agents/` |
| Runtime / sesiones / CSV vivos | `data/` (~770M+) | **NO** (solo ejemplos + PVC en K8s) |
| Secretos | `secrets/` | **NO** → `secrets.example/` |

---

## 2. Stack en ejecución (Docker)

| Contenedor | Imagen | Rol |
|------------|--------|-----|
| `openclaw-openclaw-gateway-1` | `openclaw-with-ssh:local` | Gateway, WhatsApp/Telegram, agentes |
| `openclaw-openclaw-cli-1` | `openclaw-with-ssh:local` | CLI admin |
| `openclaw-litellm-1` | `berriai/litellm:main-latest` | Proxy modelos (Ollama, remoto, visión) |
| `openclaw-openclaw-proxy-1` | `nginx:alpine` | Proxy HTTP |
| `openclaw-ollama-fast-1` | `ollama/ollama` | LLM local rápido |
| `postgres-memory` | `pgvector/pgvector:pg16` | Memoria vectorial |
| `redis-memory` | `redis:7-alpine` | Cache memoria |
| `open-webui` | `ghcr.io/open-webui/open-webui:main` | UI chat |
| `jenkins-devops` | `jenkins/jenkins:lts-jdk21` | CI/CD host |

**Compose principal:** `openclaw-mauro/openclaw/docker-compose.yml`  
**Override finanzas:** `openclaw/docker-compose.finanzas-mounts.yml` (monta `scripts/`, `.venv-finanzas/`, `data/`)  
**Imagen custom:** `docker-overrides/openclaw-with-ssh/` (Dockerfile + wrappers SSH)

---

## 3. Agentes OpenClaw (`data/config/openclaw.json`)

| ID | Nombre | Workspace (contenedor) | Canal / binding |
|----|--------|------------------------|-----------------|
| `main` | — | default | — |
| `intel` | intel | `workspace/marketing/intel` | Marketing (cron/orquestador) |
| `content` | content | `workspace/marketing/content` | Instagram/WhatsApp vía delegación finanzas |
| `sales` | sales | `workspace/marketing/sales` | Leads / ventas |
| `finanzas` | finanzas | `workspace/marketing/finanzas` | **Telegram + WhatsApp** (bindings activos) |
| `pyme-chile` | PymeChile | `workspace/pyme-chile` | Proyecto PYME |
| `hl-miko-web` | hl-miko-web | `workspace/projects/hl_miko` | Proyecto HL-Miko |

**Bindings actuales:** solo `finanzas` → `telegram` y `whatsapp`.

**SOUL / identidad por agente:**

| Agente | Ruta SOUL (host) |
|--------|------------------|
| finanzas | `data/workspace/marketing/finanzas/SOUL.md` |
| content | `data/workspace/marketing/content/SOUL.md` |
| intel | `data/workspace/marketing/intel/SOUL.md` |
| sales | `data/workspace/marketing/sales/SOUL.md` |
| pyme-chile | `data/workspace/pyme-chile/SOUL.md` |
| main / sandboxes | `data/config/sandboxes/agent-*/SOUL.md` |

**Skills workspace:** `data/workspace/skills/` (container-digest, content-draft, host-status, lead-finder, trend-radar, …)

---

## 4. Scripts Python / shell (lógica de negocio)

### 4.1 Finanzas (desplegados en servidor)

| Script | Función |
|--------|---------|
| `finanzas_common.py` | Esquema CSV, paths, merge |
| `finanzas_merge.py` | Unifica fuentes → `finanzas_movimientos.csv` |
| `transferencias_agent.py` | Gmail Santander → `transferencias.csv` |
| `finanzas_transferencias_report.py` | Reporte transferencias (--days / --limit) |
| `santander_cartola_agent.py` | Cartola banco |
| `santander_cuadratura.py` | Cuadratura mes |
| `receipt_vision_agent.py` | Boletas con visión (qwen3-vl vía LiteLLM) |
| `finanzas_monthly_report.py` | Resumen mensual |
| `finanzas_merchant_report.py` | Gasto por comercio/alias |
| `finanzas_observaciones.py` | Notas por movimiento |
| `apply_openclaw_finanzas_config.py` | Patch `openclaw.json` + compose mounts |
| `run_finanzas_pipeline.sh` | Cron */15 min |
| `reset_finanzas_whatsapp_session.sh` | Reset sesión WA |
| `setup_whatsapp_openclaw.sh` | Setup canal |

**Requirements:** `requirements-finanzas-agent.txt`  
**Venv:** `.venv-finanzas/`

### 4.2 Contenido / Instagram (desplegados)

| Script | Función |
|--------|---------|
| `content_instagram_analyze.py` | Embed IG + visión opcional |
| `content_instagram_whatsapp.py` | URL o seguimiento desde WhatsApp |
| `content_instagram_last.py` | Último análisis guardado |
| `content_intel_brief.py` | Brief desde reports intel |
| `content_draft_instagram.py` | Borrador posts |
| `apply_openclaw_content_config.py` | Config agente content |
| `reset_content_whatsapp_session.sh` | Reset sesión content |

### 4.3 Líder (supermercado, cron */30)

| Script | Función |
|--------|---------|
| `lider_receipts_agent.py` | Boletas email → `lider_receipts.csv` |
| `lider_monthly_report.py` | Reporte mensual |

**Requirements:** `requirements-lider-agent.txt`  
**Venv:** `.venv-lider/`

### 4.4 Infra / mantenimiento

| Script | Función |
|--------|---------|
| `sync-openclaw-models.sh` | Cron 03:17 — sync modelos |
| `run-marketing-daily.sh` | Orquestación marketing |
| `gateway-entrypoint.sh`, `cli-entrypoint.sh` | Entrypoints Docker |
| `ensure-bun.sh` | Build deps |

### 4.5 Solo en repo dev local (`C:\DEV\openclaw-mauro`) — aún no en servidor

| Script | Función |
|--------|---------|
| `linkedin_jobs_agent.py` | Jobs LinkedIn (CV matching) |
| `linkedin_jobs_soldador.py` | Variante soldador |
| `linkedin_jobs_report.py` | Reportes |
| `fix-openclaw-cli-healthcheck.sh` | Healthcheck CLI |
| `app.py` | App auxiliar local |
| README hermes-dashboard, linkedin-* | Documentación |

**Config LinkedIn (local git):** `config/linkedin_jobs/`, `config/linkedin_jobs_soldador/`

---

## 5. Configuración versionable (`config/`)

| Ruta | Contenido |
|------|-----------|
| `config/finanzas/merchant_aliases.example.json` | Alias comercios |
| `config/finanzas/openclaw-compaction-session.example.json` | Compaction (reserveTokensFloor 8000) |
| `config/marketing/content-SOUL-whatsapp.md` | SOUL content WhatsApp |
| `config/marketing/finanzas-SOUL-content-delegate.md` | Delegación IG → scripts |
| `config/marketing/README-content-whatsapp.md` | Doc flujo |

**En servidor, parcial en `scripts/`:** copia suelta `finanzas-SOUL-content-delegate.md` (duplicado; consolidar en `config/marketing/`).

**Config runtime (NO commitear tal cual):** `data/config/openclaw.json` (~19 KB) — extraer plantilla `openclaw.example.json` sin API keys.

---

## 6. Datos runtime (`data/`) — NO subir al repo

| Archivo / dir | Tamaño aprox. | Uso |
|---------------|---------------|-----|
| `data/config/` | 373 MB | Sesiones, sandboxes, openclaw.json |
| `data/workspace/` | 392 MB | SOUL, drafts, skills, proyectos |
| `finanzas_movimientos.csv` | 280 KB | Ledger unificado |
| `transferencias.csv` | 92 KB | Transferencias Gmail |
| `santander_cartola.csv` | 144 KB | Cartola |
| `receipts_registry.json` | 195 KB | Registro boletas |
| `lider_receipts.csv` | 12 KB | Boletas Líder |
| `data/inbox/` | 216 KB | Media entrante |
| `content/references/instagram/*.json` | bajo `workspace/marketing/content/` | Análisis IG guardados |

**Backups CSV:** múltiples `*.bak-*` — excluir del repo.

---

## 7. Secretos (`secrets/`) — solo ejemplos en repo

| Archivo servidor | Migrar como |
|------------------|-------------|
| `gmail_credentials.json` | `secrets.example/gmail_credentials.json.example` |
| `gmail_token.json` | (runtime OAuth, no commit) |
| `whatsapp_allow_from.txt` | `secrets.example/whatsapp_allow_from.example.txt` |
| `github_hl_miko_*` | ejemplos sin valores |
| `santander_cartola.env` | `secrets.example/santander_cartola.env.example` (ya en dev) |

---

## 8. Cron (host)

```cron
*/30  lider_receipts_agent.py
17 3  sync-openclaw-models.sh
*/15  run_finanzas_pipeline.sh
```

Logs: `openclaw-mauro/logs/`

---

## 9. Documentación existente

| Archivo | Tema |
|---------|------|
| `MARKETING-AGENTS-ORCHESTRATOR.md` | Equipo marketing IA |
| `scripts/README-finanzas-agent.md` | Agente finanzas |
| `scripts/README-transferencias-agent.md` | Transferencias |
| `scripts/README-content-whatsapp.md` | Instagram WhatsApp |
| `scripts/README-lider-agent.md` | Líder |
| `openclaw/.env.example` | Vars OpenClaw upstream |

---

## 10. Basura / no migrar

| Ruta | Motivo |
|------|--------|
| `tmp-deploy*`, `tmp-fix*`, `tmp-ig` | Despliegues temporales |
| `backups/` | Snapshots locales |
| `.venv-finanzas`, `.venv-lider` | Regenerar con requirements |
| `openclaw/.git` | Submodule/upstream separado |
| `data/config/agents/*/sessions/*.jsonl` | Estado conversación |
| `__pycache__`, `*.pyc` | Artefactos |
| `graphify-out/` (solo dev Windows) | Análisis local |

---

## 11. Mapa → estructura `agentes-ai-on-clouds`

```
apps/openclaw/
├── docker/          ← docker-compose.yml, finanzas-mounts.yml, docker-overrides/
├── scripts/         ← todos los *.py, run_*.sh, requirements-*.txt
├── config/
│   ├── agents/      ← por agente: finanzas, content, intel, sales, …
│   │   └── <id>/
│   │       ├── SOUL.md
│   │       ├── openclaw.agent.example.json
│   │       └── skills/
│   └── channels/    ← whatsapp, telegram ejemplos
├── agents/          ← documentación por agente (README.md cada uno)
└── workspaces/    ← plantillas SOUL/skills (sin data/ runtime)

apps/litellm/        ← config.yaml, model_list (sin API keys)
apps/memory-services/← manifests postgres+redis o chart
apps/open-webui/     ← compose fragment o values helm

infra/k8s/           ← base + overlays dev/prod (futuro)
infra/terraform/     ← módulos gke/eks/aks (futuro)
cicd/jenkins/        ← Jenkinsfile, jobs
docs/
├── inventory/       ← este archivo
└── architecture/    ← diagramas (siguiente paso)
scripts/             ← bootstrap install, rsync-from-legacy.sh
secrets.example/     ← todos los .example
```

---

## 12. Prioridad de migración (fases)

### Fase 1 — Código y config (ahora)
1. `scripts/` completo (servidor + alinear con dev local LinkedIn)
2. `config/finanzas`, `config/marketing`
3. SOUL.md desde `data/workspace/marketing/*/SOUL.md`
4. `docker-compose*.yml` + `docker-overrides/openclaw-with-ssh`
5. READMEs y `MARKETING-AGENTS-ORCHESTRATOR.md` → `docs/`

### Fase 2 — Plantillas
1. `openclaw.example.json` derivado de producción (redactado)
2. `secrets.example/` completo
3. Cron como `apps/openclaw/cron/kubernetes-cronjob.yaml` o doc

### Fase 3 — Cloud
1. K8s base (gateway, litellm, memory)
2. Terraform por cloud
3. Jenkins pipeline deploy

---

## 13. Comandos útiles (auditoría)

```bash
# Tamaños
du -sh /home/mauro/openclaw-mauro/{scripts,config,data,openclaw,secrets}

# Agentes en JSON
python3 -c "import json;d=json.load(open('data/config/openclaw.json'));print([a['id'] for a in d['agents']['list']])"

# Diff scripts servidor vs git local
diff -qr /home/mauro/openclaw-mauro/scripts /path/to/local/scripts
```

---

*Generado para el proyecto agentes-ai-on-clouds. Siguiente paso: script `scripts/sync-from-openclaw-mauro.sh` que copie Fase 1 sin secretos ni `data/`.*
