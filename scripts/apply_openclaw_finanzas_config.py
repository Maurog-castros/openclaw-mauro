#!/usr/bin/env python3
"""Aplica config finanzas en openclaw.json (Telegram + WhatsApp -> agente finanzas)."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path("/home/mauro/openclaw-mauro/data/config/openclaw.json")
SOUL_PATH = Path("/home/mauro/openclaw-mauro/data/workspace/marketing/finanzas/SOUL.md")
WHATSAPP_ALLOW_FILE = Path("/home/mauro/openclaw-mauro/secrets/whatsapp_allow_from.txt")
WHATSAPP_AUTH_DIR = "/home/mauro/openclaw-mauro/data/config/whatsapp-auth/default"
CONFIG_DIR = Path("/home/mauro/openclaw-mauro/data/config")
REPO_ROOT = Path("/home/mauro/openclaw-mauro")
FINANZAS_COMPOSE_OVERRIDE = REPO_ROOT / "openclaw" / "docker-compose.finanzas-mounts.yml"
MERCHANT_ALIASES_EXAMPLE = REPO_ROOT / "config/finanzas/merchant_aliases.example.json"
MERCHANT_ALIASES_DEST = REPO_ROOT / "data/finanzas_merchant_aliases.json"

# Rutas dentro del contenedor gateway (openclaw.json + SOUL deben usar estas).
CONTAINER_REPO = "/home/node/openclaw-mauro"
CONTAINER_MEDIA = f"{CONTAINER_REPO}/data/config/media/inbound"
CONTAINER_FINANZAS_DATA = f"{CONTAINER_REPO}/data"
CONTAINER_CSV = f"{CONTAINER_FINANZAS_DATA}/finanzas_movimientos.csv"
CONTAINER_SCRIPTS = f"{CONTAINER_REPO}/scripts"
CONTAINER_RUN_PY = f"{CONTAINER_SCRIPTS}/run-finanzas-py.sh"
CONTAINER_VENV_PY = f"{CONTAINER_REPO}/.venv-finanzas-docker/bin/python"

# Bootstrap OpenClaw inyecta SOUL + AGENTS con techo ~7225 chars total; SOUL debe quedar <5200.
FINANZAS_SOUL = f"""# Agente Finanzas

Finanzas personales Mauricio (Chile, CLP). Espanol chileno, conciso.
WhatsApp: formato nativo (*negrita* para titulos y montos $), emojis, separador ───. PROHIBIDO tablas markdown |col| y bloques ``` largos. Al final delegate agrega menu numerado 1-5.

## Delegacion /supp

Si el mensaje empieza con `/supp`: delegate ya enruta a support_delegate.py. Copia `whatsapp_reply` corto.

## Delegacion /intel

Si el mensaje empieza con `/intel`: `{CONTAINER_RUN_PY} {CONTAINER_SCRIPTS}/intel_delegate.py --text "<mensaje completo>" --json` -> copia `whatsapp_reply`. No uses scripts de finanzas ni CSV.

## Exec (OBLIGATORIO)

Host gateway (sin host=node). Una sola linea, formato exacto:
`{CONTAINER_RUN_PY} {CONTAINER_SCRIPTS}/SCRIPT.py ... --json`
PROHIBIDO: bash -c, sh -c, cd, &&, |, python3 -m, pip install, editar scripts (montaje read-only). PROHIBIDO tool `image` para boletas.
PROHIBIDO find/ls/cat/grep del CSV o carpetas data: usa SOLO los scripts de abajo con `$CSV`.

PY=`{CONTAINER_RUN_PY}` SCR=`{CONTAINER_SCRIPTS}` CSV=`{CONTAINER_CSV}` DATA=`{CONTAINER_FINANZAS_DATA}`

## Canal

NUNCA `NO_REPLY`. Texto normal al usuario (OpenClaw envia al canal). No uses tool `message` en DM.

## Prefijo WhatsApp

Comando corto: **`/fin`** (acepta legacy `/finanzas`). Ejemplo: `/fin cuanto gaste en mayo`.
Si el mensaje empieza con `/fin` o `/finanzas`, procesa el resto como consulta finanzas.

## Regla #1 — SIEMPRE delegate primero

Para **todo** mensaje `/fin` (texto, foto, saldo, boleta, consultas):
1. `{CONTAINER_RUN_PY} {CONTAINER_SCRIPTS}/finanzas_delegate.py --text "<mensaje>" [--has-media] --json`
2. Copia `whatsapp_reply` tal cual. Si status=delegate_miss, entonces usa script especifico.
PROHIBIDO llamar finanzas_receipt_whatsapp o finanzas_saldo_whatsapp directo salvo delegate_miss.

## Saldo Santander (texto o screenshot app) — PRIORIDAD sobre boletas

Palabras: saldo, santander, disponible, «mi saldo es», «este es mi saldo», captura app banco.
Delegate enruta a saldo. Respuesta esperada: «Saldo Santander actualizado: $X» (confirmacion simple).
**Montos con $ en bash se corrompen** ($103 -> $1). Usa `--amount` entero sin $ ni puntos:
`{CONTAINER_RUN_PY} {CONTAINER_SCRIPTS}/finanzas_delegate.py --text "mi saldo" --amount 103699 --json`
PROHIBIDO receipt_vision / finanzas_receipt si hay saldo, monto en texto, o screenshot app Santander.

## Boletas (foto de ticket/compra)

Solo si NO es saldo Santander. Si trae imagen de boleta/ticket:

1. Delegate con `--has-media` (ver Regla #1).
2. duplicate_* / error: dilo claro. validation.ok false: advierte.
3. PROHIBIDO tool `image` del chat. PROHIBIDO vision del modelo como primer intento.

Media: `{CONTAINER_MEDIA}/`

## Ultimas boletas procesadas

Preguntas tipo «ultimas boletas», «boletas recientes», «que boletas tengo»:
Delegate enruta automaticamente. Si delegate_miss: `$PY $SCR/finanzas_recent_receipts.py --csv $CSV --limit N --json` -> copia `summary`/`whatsapp_reply` **sin inventar ni resumir con LLM**. PROHIBIDO listar boletas desde memoria o tool image.

## Gastos mes

PROHIBIDO cat/head/tail/grep del CSV.
`$PY $SCR/finanzas_monthly_report.py --csv $CSV --month YYYY-MM --json` -> `summary`.

## Transferencias

`$PY $SCR/finanzas_transferencias_report.py --csv $CSV --limit N --json` (ultimas N)
`$PY $SCR/finanzas_transferencias_report.py --csv $CSV --days N --json` (periodo)
Rango: `--from` `--to`. -> `summary`. movement_count 0: dilo.

## Observaciones

`$PY $SCR/finanzas_observaciones.py set --csv $CSV --date YYYY-MM-DD --amount N --match texto --note "..." --json`
O `--movement-id ID`. clear: `--movement-id ID`.

## Misma transaccion en varias fuentes (Gmail + screenshot)

Un pago puede aparecer 2+ veces: cronjob Gmail (comprobante) + linea en screenshot app Santander (+ a veces OCR falso como boleta). **Es la misma operacion**, no hay que borrar filas.

Si el usuario dice duplicado / mismo monto / corrige / otra vez:
`$PY $SCR/finanzas_dedupe_movimientos.py auto-link --text "<msg>" --json` -> copia `whatsapp_reply`.
Canonico = Gmail o cartola. Screenshot/OCR quedan vinculados (no cuentan aparte en totales).
PROHIBIDO preguntar "elimino uno?" — explica que ambas fuentes son validas, es un solo pago.
Ejemplo arriendo: Gmail 6/jun + screenshot 8/jun = misma transferencia RENOVAL.

## Cuadratura Santander

1. `$PY $SCR/santander_cartola_agent.py --output $DATA/santander_cartola.csv --json`
2. `$PY $SCR/santander_cuadratura.py --month YYYY-MM --cartola-csv $DATA/santander_cartola.csv --unified-csv $CSV --json`

## Alias comercios

Archivo `$DATA/finanzas_merchant_aliases.json`. mall chino ya configurado.
`$PY $SCR/finanzas_merchant_report.py --aliases-file $DATA/finanzas_merchant_aliases.json --csv $CSV --alias "NOMBRE" --year YYYY --json`
Detalle: agrega `--detail` -> `detail_summary`. PROHIBIDO buscar CSV a mano.

## Saldo CC Santander

Siempre al cerrar boletas/reportes/alias:
`$PY $SCR/finanzas_saldo.py report --json` -> `whatsapp_reply` al final.
Saldo real texto: `$PY $SCR/finanzas_saldo_whatsapp.py --text "<msg>" --json`
Screenshot app: + `--image "<ruta inbound>"`. difference_ok false: copia `causes`.
"""

FINANZAS_AGENTS = f"""# Finanzas — detalle

Rutas contenedor: PY `{CONTAINER_VENV_PY}`, SCR `{CONTAINER_SCRIPTS}`, CSV `{CONTAINER_CSV}`, DATA `{CONTAINER_FINANZAS_DATA}`, media `{CONTAINER_MEDIA}/`.

Saldo: ancla app + movimientos banco - boletas digitales sin match (±5d). Perfil digital 95%; desconocido=tarjeta.
Primera vez sin ancla: bootstrap-cartola o saldo real hoy.

Transferencias: lineas con nota muestran Obs. Items traen movement_id para anotar.
Cuadratura: explica solo cartola / solo finanzas. Luego finanzas_merge si hubo datos nuevos.

Alias: fechas dd-mm-yy en detail_summary vertical. alias_not_found: ofrece agregar patterns al JSON.

Boletas: lista completa productos+precios. Saludos breves: boletas, gastos, resumen mensual.
NUNCA NO_REPLY en DM. No editar scripts (read-only).
"""

FINANZAS_AGENT_PATCH = {
    "id": "fin",
    "name": "fin",
    "description": "Gastos, boletas, transferencias y reportes mensuales",
    "workspace": "/home/node/.openclaw/workspace/marketing/finanzas",
    "agentDir": "/home/node/.openclaw/agents/finanzas/agent",
    "model": {
        "primary": "remote-lm/openclaw-remote",
        "fallbacks": [
            "remote-lm/openclaw-remote-vision",
            "remote-lm/openclaw-remote-coder",
        ],
    },
    "identity": {
        "name": "Fin",
        "theme": "gastos personales, boletas y transferencias Chile",
        "emoji": "💰",
    },
    "sandbox": {"mode": "off"},
    "contextLimits": {
        "toolResultMaxChars": 3500,
        "postCompactionMaxChars": 2500,
    },
    "tools": {
        "allow": [
            "read",
            "write",
            "exec",
            "message",
            "memory_search",
            "memory_get",
        ],
        "exec": {
            "host": "gateway",
            "security": "full",
            "ask": "off",
            "strictInlineEval": True,
            "commandHighlighting": True,
        },
    },
}

CHANNEL_DM_PROMPT = (
    "Prefijo /supp = soporte tecnico (logs, fixes). Delegate: support_delegate.py --json -> whatsapp_reply. "
    "Prefijo /fin = agente finanzas (legacy /finanzas aceptado). "
    "Canal finanzas. NUNCA respondas NO_REPLY: siempre texto visible al usuario. "
    "PASO 1 OBLIGATORIO en cada mensaje: "
    f"{CONTAINER_RUN_PY} {CONTAINER_SCRIPTS}/finanzas_delegate.py --text \"<msg>\" [--has-media] --json. "
    "Si status ok/skipped/processed: copia whatsapp_reply y TERMINA. Solo si delegate_miss sigue con scripts abajo. "
    "Ultimas boletas: finanzas_recent_receipts.py --limit N --json. "
    "Consultas por mes: finanzas_monthly_report.py --month YYYY-MM --json. "
    "Transferencias: finanzas_transferencias_report.py --limit N --json; NUNCA cat el CSV. "
    "IG (link o seguimiento «ultimo post»/«de que trata»): content_instagram_whatsapp.py --text \"<msg>\" --json -> whatsapp_reply. "
    "Observaciones: finanzas_observaciones.py set --date ... --amount ... --match ... --note \"...\" --json. "
    "Duplicados multi-fuente (Gmail+screenshot misma tx): finanzas_dedupe_movimientos.py auto-link --text \"<msg>\" --json. "
    "No eliminar registros; vincular. Canonico = Gmail/cartola. "
    "Gasto por lugar/alias: finanzas_merchant_report.py --alias \"NOMBRE\" --detail --json; "
    "responde copiando detail_summary (formato WhatsApp *negrita*, sin tablas |). "
    "Cuadratura banco: santander_cartola_agent.py + santander_cuadratura.py --month YYYY-MM --json. "
    "Fotos de boletas: finanzas_delegate.py --text \"<msg>\" --has-media --json -> whatsapp_reply (Iamiko vision). "
    "Saldo Santander (texto o screenshot app): finanzas_saldo_whatsapp.py --text \"<msg>\" --json; NO receipt_vision si dice saldo. "
    "PROHIBIDO tool image. PROHIBIDO find/ls/cat/grep en data/. "
    "Saldo CC Santander: finanzas_saldo.py report --json al cerrar; set-actual con finanzas_saldo_whatsapp.py --text. "
    f"CSV: {CONTAINER_CSV}"
)

# Auto-compact: solo claves validas en OpenClaw 2026.5.x (evita crash gateway).
# Ventana modelo ~32k: floor alto (28k+) deja sin espacio y falla auto-compaction.
COMPACTION_DEFAULTS: dict = {
    "reserveTokensFloor": 8000,
}

SESSION_DEFAULTS: dict = {
    "reset": {
        "idleMinutes": 480,
    },
    "typingMode": "instant",
    "typingIntervalSeconds": 4,
}

HOST_CONTAINER_SYMLINKS: dict[str, Path] = {}

FINANZAS_DOCKER_MOUNTS = [
    f"{REPO_ROOT}/scripts:{CONTAINER_REPO}/scripts:ro",
    f"{REPO_ROOT}/.venv-finanzas-docker:{CONTAINER_REPO}/.venv-finanzas-docker:rw",
    f"{REPO_ROOT}/.venv-finanzas:{CONTAINER_REPO}/.venv-finanzas:ro",
    f"{REPO_ROOT}/data:{CONTAINER_REPO}/data:rw",
]

FINANZAS_COMPOSE_OVERRIDE_YAML = f"""# Montajes para agente finanzas (generado por apply_openclaw_finanzas_config.py)
services:
  openclaw-gateway:
    volumes:
      - {FINANZAS_DOCKER_MOUNTS[0]}
      - {FINANZAS_DOCKER_MOUNTS[1]}
      - {FINANZAS_DOCKER_MOUNTS[2]}
      - {FINANZAS_DOCKER_MOUNTS[3]}
  openclaw-cli:
    volumes:
      - {FINANZAS_DOCKER_MOUNTS[0]}
      - {FINANZAS_DOCKER_MOUNTS[1]}
      - {FINANZAS_DOCKER_MOUNTS[2]}
      - {FINANZAS_DOCKER_MOUNTS[3]}
"""


def ensure_finanzas_docker_mounts() -> str:
    FINANZAS_COMPOSE_OVERRIDE.parent.mkdir(parents=True, exist_ok=True)
    FINANZAS_COMPOSE_OVERRIDE.write_text(FINANZAS_COMPOSE_OVERRIDE_YAML, encoding="utf-8")
    return str(FINANZAS_COMPOSE_OVERRIDE)


def ensure_host_symlinks_for_container() -> list[str]:
    """Reservado; los symlinks fuera del bind mount no funcionan en Docker."""
    return []


def ensure_merchant_aliases_seed() -> bool:
    """Crea data/finanzas_merchant_aliases.json desde el ejemplo si no existe."""
    if MERCHANT_ALIASES_DEST.exists():
        return False
    if not MERCHANT_ALIASES_EXAMPLE.exists():
        return False
    MERCHANT_ALIASES_DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MERCHANT_ALIASES_EXAMPLE, MERCHANT_ALIASES_DEST)
    return True


def backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = path.with_suffix(path.suffix + f".bak-finanzas-{stamp}")
    shutil.copy2(path, dest)
    return dest


def normalize_e164(value: str) -> str:
    text = value.strip()
    if not text or text.startswith("#"):
        return ""
    if not text.startswith("+"):
        digits = re.sub(r"\D", "", text)
        if digits.startswith("569") or digits.startswith("56"):
            return f"+{digits}" if not digits.startswith("+") else digits
        if len(digits) == 9 and digits.startswith("9"):
            return f"+56{digits}"
        return f"+{digits}" if digits else ""
    return text


def load_whatsapp_allow_from() -> list[str]:
    numbers: list[str] = []
    env_value = os.environ.get("FINANZAS_WHATSAPP_ALLOW_FROM", "")
    for part in env_value.split(","):
        normalized = normalize_e164(part)
        if normalized:
            numbers.append(normalized)
    if WHATSAPP_ALLOW_FILE.exists():
        for line in WHATSAPP_ALLOW_FILE.read_text(encoding="utf-8").splitlines():
            normalized = normalize_e164(line)
            if normalized and normalized not in numbers:
                numbers.append(normalized)
    return [n for n in numbers if not n.endswith("00000000")]


def patch_vision_model_input(data: dict) -> bool:
    changed = False
    models = data.get("models", {}).get("providers", {}).get("remote-lm", {}).get("models", [])
    for model in models:
        if model.get("id") == "openclaw-remote-vision":
            inputs = model.get("input") or []
            if "image" not in inputs:
                model["input"] = ["text", "image"]
                changed = True
    return changed


def patch_finanzas_agent(data: dict) -> bool:
    agents = data.get("agents", {}).get("list", [])
    target = None
    others: list = []
    for agent in agents:
        if agent.get("id") in ("finanzas", "fin"):
            if target is None:
                target = agent
        else:
            others.append(agent)
    if target is None:
        target = dict(FINANZAS_AGENT_PATCH)
    else:
        for key, value in FINANZAS_AGENT_PATCH.items():
            target[key] = value
    data.setdefault("agents", {})["list"] = others + [target]
    return True


def patch_compaction_and_session(data: dict) -> bool:
    """reserveTokensFloor + idle reset; solo campos aceptados por el schema del gateway."""
    changed = False
    agents = data.setdefault("agents", {})
    defaults = agents.setdefault("defaults", {})
    for key in ("typingMode", "typingIntervalSeconds"):
        if key in SESSION_DEFAULTS and defaults.get(key) != SESSION_DEFAULTS[key]:
            defaults[key] = SESSION_DEFAULTS[key]
            changed = True
    compaction = defaults.setdefault("compaction", {})
    for key in list(compaction.keys()):
        if key not in COMPACTION_DEFAULTS:
            compaction.pop(key, None)
            changed = True
    for key, value in COMPACTION_DEFAULTS.items():
        if compaction.get(key) != value:
            compaction[key] = value
            changed = True
    session = data.setdefault("session", {})
    reset = session.setdefault("reset", {})
    desired_reset = SESSION_DEFAULTS["reset"]
    for key in list(reset.keys()):
        if key not in desired_reset:
            reset.pop(key, None)
            changed = True
    for key, value in desired_reset.items():
        if reset.get(key) != value:
            reset[key] = value
            changed = True
    for key in ("typingMode", "typingIntervalSeconds"):
        if key in SESSION_DEFAULTS and session.get(key) != SESSION_DEFAULTS[key]:
            session[key] = SESSION_DEFAULTS[key]
            changed = True
    if "maintenance" in session:
        session.pop("maintenance", None)
        changed = True
    return changed


def ensure_channel_binding(data: dict, channel: str, comment: str) -> bool:
    bindings = data.get("bindings") or []
    changed = False
    for binding in bindings:
        match = binding.get("match") or {}
        if match.get("channel") == channel:
            if binding.get("agentId") != "fin":
                binding["agentId"] = "fin"
                binding["comment"] = comment
                changed = True
            return changed
    bindings.append({"agentId": "fin", "comment": comment, "match": {"channel": channel}})
    data["bindings"] = bindings
    return True


def patch_telegram_channel(data: dict) -> bool:
    telegram = data.setdefault("channels", {}).setdefault("telegram", {})
    changed = False
    owner_id = "8503943962"
    dms = telegram.get("dms") or {}
    if owner_id in dms and "systemPrompt" in dms.get(owner_id, {}):
        dms.pop(owner_id, None)
        if dms:
            telegram["dms"] = dms
        else:
            telegram.pop("dms", None)
        changed = True
    direct = telegram.setdefault("direct", {})
    dm_cfg = direct.setdefault(owner_id, {})
    if dm_cfg.get("systemPrompt") != CHANNEL_DM_PROMPT:
        dm_cfg["systemPrompt"] = CHANNEL_DM_PROMPT
        changed = True
    roots = telegram.setdefault("trustedLocalFileRoots", [])
    for root in (
        CONTAINER_MEDIA,
        CONTAINER_FINANZAS_DATA,
        f"{CONTAINER_FINANZAS_DATA}/inbox/boletas",
    ):
        if root not in roots:
            roots.append(root)
            changed = True
    telegram["trustedLocalFileRoots"] = roots
    return changed


def patch_whatsapp_channel(data: dict, allow_from: list[str]) -> bool:
    whatsapp = data.setdefault("channels", {}).setdefault("whatsapp", {})
    desired = {
        "enabled": True,
        "dmPolicy": "allowlist" if allow_from else "pairing",
        "groupPolicy": "disabled",
        "allowFrom": allow_from,
        "sendReadReceipts": True,
        "reactionLevel": "ack",
        "mediaMaxMb": 50,
        "accounts": {
            "default": {
                "enabled": True,
                "name": "OpenClaw Fin",
                "authDir": "/home/node/.openclaw/whatsapp-auth/default",
            }
        },
    }
    changed = False
    for key, value in desired.items():
        if whatsapp.get(key) != value:
            whatsapp[key] = value
            changed = True
    direct = whatsapp.setdefault("direct", {})
    wildcard = direct.setdefault("*", {})
    if wildcard.get("systemPrompt") != CHANNEL_DM_PROMPT:
        wildcard["systemPrompt"] = CHANNEL_DM_PROMPT
        changed = True
    for number in allow_from:
        entry = direct.setdefault(number, {})
        if entry.get("systemPrompt") != CHANNEL_DM_PROMPT:
            entry["systemPrompt"] = CHANNEL_DM_PROMPT
            changed = True
    return changed


def patch_whatsapp_plugin(data: dict) -> bool:
    entries = data.setdefault("plugins", {}).setdefault("entries", {})
    current = entries.get("whatsapp") or {}
    if current.get("enabled") is True and current.get("config") == {}:
        return False
    entries["whatsapp"] = {"enabled": True, "config": {}}
    return True


def patch_owner_allow_from(data: dict, whatsapp_numbers: list[str]) -> bool:
    commands = data.setdefault("commands", {})
    owners = list(commands.get("ownerAllowFrom") or [])
    changed = False
    if "telegram:8503943962" not in owners:
        owners.append("telegram:8503943962")
        changed = True
    for number in whatsapp_numbers:
        token = f"whatsapp:{number}"
        if token not in owners:
            owners.append(token)
            changed = True
    if changed:
        commands["ownerAllowFrom"] = owners
    return changed


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"ERROR: no existe {CONFIG_PATH}", file=sys.stderr)
        return 1

    whatsapp_allow = load_whatsapp_allow_from()
    Path(WHATSAPP_AUTH_DIR).mkdir(parents=True, exist_ok=True)
    symlinks = ensure_host_symlinks_for_container()
    compose_override = ensure_finanzas_docker_mounts()
    merchant_aliases_seeded = ensure_merchant_aliases_seed()

    backup(CONFIG_PATH)
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    changes = {
        "vision_input": patch_vision_model_input(data),
        "compaction_session": patch_compaction_and_session(data),
        "finanzas_agent": patch_finanzas_agent(data),
        "telegram_binding": ensure_channel_binding(
            data, "telegram", "Telegram -> agente finanzas (boletas + gastos)"
        ),
        "whatsapp_binding": ensure_channel_binding(
            data, "whatsapp", "WhatsApp -> agente finanzas (boletas + gastos)"
        ),
        "telegram_channel": patch_telegram_channel(data),
        "whatsapp_channel": patch_whatsapp_channel(data, whatsapp_allow),
        "whatsapp_plugin": patch_whatsapp_plugin(data),
        "owner_allow_from": patch_owner_allow_from(data, whatsapp_allow),
        "whatsapp_allow_from": whatsapp_allow,
    }

    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    SOUL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SOUL_PATH.exists():
        backup(SOUL_PATH)
    SOUL_PATH.write_text(FINANZAS_SOUL, encoding="utf-8")

    agents_md = SOUL_PATH.parent / "AGENTS.md"
    if agents_md.exists():
        backup(agents_md)
    agents_md.write_text(FINANZAS_AGENTS, encoding="utf-8")

    changes["container_symlinks"] = symlinks
    changes["docker_compose_override"] = compose_override
    changes["merchant_aliases_seeded"] = merchant_aliases_seeded
    print(
        json.dumps(
            {
                "ok": True,
                "changes": changes,
                "config": str(CONFIG_PATH),
                "restart_hint": (
                    f"cd {REPO_ROOT}/openclaw && docker compose "
                    f"-f docker-compose.yml -f docker-compose.finanzas-mounts.yml "
                    f"up -d openclaw-gateway"
                ),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
